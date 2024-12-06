from fastapi import APIRouter, UploadFile, File
from app.services.ocr.service import OCRService

router = APIRouter()

@router.post("/upload/")
async def upload_document(
    file: UploadFile = File(...),
    doc_type: str = None
):
    # 实现文件上传逻辑
    pass 