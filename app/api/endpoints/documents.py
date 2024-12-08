from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.services.document_processor import DocumentProcessor
from app.models.document import Document
from datetime import datetime
import os
import aiofiles
import magic
from typing import Optional, Dict, Any
from pydantic import BaseModel

router = APIRouter()

class DocumentResponse(BaseModel):
    document_id: int
    status: str
    result: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

@router.post("/upload/", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    doc_type: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        # 验证文档类型
        if doc_type not in ["contract", "invoice", "bank_statement"]:
            raise HTTPException(status_code=400, detail="Invalid doc_type")
        
        # 验证文件类型
        content = await file.read()
        mime = magic.Magic(mime=True)
        file_type = mime.from_buffer(content)
        
        if not file_type.startswith(('image/', 'application/pdf')):
            raise HTTPException(
                status_code=400,
                detail="Invalid file type. Only images and PDFs are allowed."
            )
        
        # 创建文件保存目录
        upload_dir = os.path.join("uploads", doc_type)
        os.makedirs(upload_dir, exist_ok=True)
        
        # 生成唯一文件名
        file_ext = os.path.splitext(file.filename)[1]
        unique_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}{file_ext}"
        file_path = os.path.join(upload_dir, unique_filename)
        
        # 保存文件
        async with aiofiles.open(file_path, 'wb') as out_file:
            await out_file.write(content)
            await out_file.flush()  # 确保文件写入磁盘
        
        # 处理文档
        processor = DocumentProcessor()
        result = await processor.process_document(file_path, doc_type)
        
        if result.get("status") == "error":
            raise HTTPException(status_code=500, detail=result.get("error", "Unknown error"))
        
        # 创建文档记录
        doc = Document(
            doc_type=doc_type,
            file_path=file_path,
            status="processed",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        
        return DocumentResponse(
            document_id=doc.id,
            status="success",
            result=result,
            created_at=doc.created_at,
            updated_at=doc.updated_at
        )
        
    except Exception as e:
        # 记录错误详情
        print(f"Error processing document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 