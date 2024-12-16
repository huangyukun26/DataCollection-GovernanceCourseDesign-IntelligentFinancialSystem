from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from app.db.session import get_db
from app.services.bank_statement_service import BankStatementService
from app.schemas.bank_statement import (
    BankStatement, 
    BankStatementCreate, 
    BankStatementUpdate,
    BankStatementListResponse
)

# 添加请求体模型
class BatchDeleteRequest(BaseModel):
    ids: List[int]

router = APIRouter()
bank_statement_service = BankStatementService()

@router.post("/upload/", response_model=BankStatement)
async def upload_bank_statement(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """上传银行流水"""
    try:
        # 读取文件内容
        file_content = await file.read()
        
        # 创建空的statement_data(后续会通过OCR填充)
        statement_data = BankStatementCreate()
        
        # 创建银行流水记录
        result = bank_statement_service.create_bank_statement(
            db=db,
            file_data=file_content,
            statement_data=statement_data
        )
        
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"上传银行流水失败: {str(e)}"
        )

@router.get("/list/", response_model=BankStatementListResponse)
async def list_bank_statements(
    skip: int = 0,
    limit: int = 100,
    account_number: Optional[str] = None,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db)
):
    """获取银行流水列表"""
    try:
        statements, total = bank_statement_service.get_bank_statements(
            db=db,
            skip=skip,
            limit=limit,
            account_number=account_number,
            start_date=start_date,
            end_date=end_date
        )
        return {
            "status": "success",
            "data": statements,
            "total": total
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取银行流水列表失败: {str(e)}"
        )

@router.get("/{statement_id}", response_model=BankStatement)
async def get_bank_statement(
    statement_id: int,
    db: Session = Depends(get_db)
):
    """获取单条银行流水记录"""
    statement = bank_statement_service.get_bank_statement(db, statement_id)
    if not statement:
        raise HTTPException(
            status_code=404,
            detail="银行流水记录不存在"
        )
    return statement

@router.put("/{statement_id}", response_model=BankStatement)
async def update_bank_statement(
    statement_id: int,
    statement_data: BankStatementUpdate,
    db: Session = Depends(get_db)
):
    """更新银行流水记录"""
    statement = bank_statement_service.update_bank_statement(
        db=db,
        statement_id=statement_id,
        statement_data=statement_data
    )
    if not statement:
        raise HTTPException(
            status_code=404,
            detail="银行流水记录不存在"
        )
    return statement

@router.delete("/{statement_id}")
async def delete_bank_statement(
    statement_id: int,
    db: Session = Depends(get_db)
):
    """删除银行流水记录"""
    success = bank_statement_service.delete_bank_statement(db, statement_id)
    if not success:
        raise HTTPException(
            status_code=404,
            detail="银行流水记录不存在"
        )
    return {"status": "success"}

@router.get("/statistics/")
async def get_statistics(
    account_number: Optional[str] = None,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db)
):
    """获取统计数据"""
    try:
        stats = bank_statement_service.get_statistics(
            db=db,
            account_number=account_number,
            start_date=start_date,
            end_date=end_date
        )
        return {
            "status": "success",
            "data": stats
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取统计数据失败: {str(e)}"
        )

@router.post("/batch-delete/")
async def batch_delete_bank_statements(
    request: BatchDeleteRequest,
    db: Session = Depends(get_db)
):
    """批量删除银行流水记录"""
    try:
        success = bank_statement_service.batch_delete_bank_statements(db, request.ids)
        if success:
            return {"status": "success", "message": "批量删除成功"}
        else:
            raise HTTPException(
                status_code=400,
                detail="部分记录删除失败"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"批量删除失败: {str(e)}"
        ) 