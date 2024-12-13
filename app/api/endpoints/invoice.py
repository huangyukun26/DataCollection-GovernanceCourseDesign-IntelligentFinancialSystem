from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
import os
import traceback

from app.services.ocr_service import OCRService
from app.db.session import get_db
from app.models.invoice import Invoice
from app.utils.storage import MinioStorage
from app.schemas.invoice import Invoice as InvoiceSchema

router = APIRouter()
ocr_service = OCRService()
storage = MinioStorage()

@router.post("/upload/")
async def upload_invoice(
    file: UploadFile = File(..., description="发票图片文件(最大10MB)"),
    db: Session = Depends(get_db)
):
    """
    上传并识别发票
    """
    try:
        # 检查文件大小
        file_size = 0
        contents = bytearray()
        
        # 分块读取文件
        chunk_size = 1024 * 1024  # 1MB chunks
        while True:
            chunk = await file.read(chunk_size)
            if not chunk:
                break
            file_size += len(chunk)
            contents.extend(chunk)
            
            # 检查文件大小是否超过限制 (10MB)
            if file_size > 10 * 1024 * 1024:
                raise HTTPException(
                    status_code=413,
                    detail="文件大小超过限制(最大10MB)"
                )
        
        # 调用OCR服务处理发票
        result = await ocr_service.process_invoice(bytes(contents))
        
        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result["message"])
            
        # 保存文件到MinIO
        file_path = f"invoices/{file.filename}"
        await storage.upload_file(file_path, bytes(contents))
        
        # 获取文件URL
        file_url = await storage.get_file_url(file_path)
        
        # 保存发票信息到数据库
        invoice_data = result["data"]
        invoice = Invoice(
            invoice_code=invoice_data["invoice_code"],
            invoice_number=invoice_data["invoice_number"],
            invoice_date=invoice_data["invoice_date"],
            total_amount=invoice_data["total_amount"],
            tax_amount=invoice_data["tax_amount"],
            seller=invoice_data["seller"],
            buyer=invoice_data["buyer"],
            file_path=file_path
        )
        
        db.add(invoice)
        db.commit()
        db.refresh(invoice)
        
        return {
            "status": "success",
            "message": "发票上传并识别成功",
            "data": {
                "invoice_id": invoice.id,
                "invoice_info": invoice_data,
                "image_url": file_url
            }
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"发票处理错误: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"发票处理失败: {str(e)}"
        )

@router.get("/list/")
async def list_invoices(db: Session = Depends(get_db)):
    """获取发票列表"""
    try:
        invoices = db.query(Invoice).all()
        return {
            "status": "success",
            "data": [
                {
                    "id": invoice.id,
                    "invoice_code": invoice.invoice_code,
                    "invoice_number": invoice.invoice_number,
                    "invoice_date": invoice.invoice_date,
                    "total_amount": invoice.total_amount,
                    "tax_amount": invoice.tax_amount,
                    "seller": invoice.seller,
                    "buyer": invoice.buyer,
                    "file_path": invoice.file_path,
                    "created_at": invoice.created_at,
                    "updated_at": invoice.updated_at
                }
                for invoice in invoices
            ]
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取发票列表失败: {str(e)}"
        )

@router.get("/{invoice_id}", response_model=InvoiceSchema)
async def get_invoice(invoice_id: int, db: Session = Depends(get_db)):
    """获取单个发票详情"""
    try:
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            raise HTTPException(status_code=404, detail="发票不存在")
        return InvoiceSchema.from_orm(invoice)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取发票详情失败: {str(e)}"
        )

@router.delete("/{invoice_id}")
async def delete_invoice(invoice_id: int, db: Session = Depends(get_db)):
    """删除发票"""
    try:
        # 查找发票
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            raise HTTPException(status_code=404, detail="发票不存在")
        
        # 从MinIO中删除文件
        try:
            if invoice.file_path:
                await storage.delete_file(invoice.file_path)
        except Exception as e:
            print(f"删除MinIO文件失败: {str(e)}")
            # 继续执行，即使文件删除失败
        
        # 从数据库中删除记录
        db.delete(invoice)
        db.commit()
        
        return {
            "status": "success",
            "message": "发票删除成功"
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"删除发票失败: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"删除发票失败: {str(e)}"
        ) 