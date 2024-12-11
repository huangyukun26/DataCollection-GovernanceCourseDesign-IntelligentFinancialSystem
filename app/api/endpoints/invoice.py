from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from ...db.session import get_db
from ...services.invoice_service import InvoiceService
from ...schemas.invoice import Invoice as InvoiceSchema
from typing import List

router = APIRouter()
invoice_service = InvoiceService()

@router.post("/upload/")
async def upload_invoice(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """上传发票图片并进行OCR识别"""
    try:
        contents = await file.read()
        
        # 提取发票信息
        invoice_data = invoice_service.extract_invoice_info(contents)
        
        # 保存到数据库和MinIO
        invoice = invoice_service.create_invoice(db, contents, invoice_data)
        
        return InvoiceSchema.from_orm(invoice)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[InvoiceSchema])
async def list_invoices(db: Session = Depends(get_db)):
    """获取所有发票列表"""
    invoices = db.query(Invoice).all()
    return [InvoiceSchema.from_orm(invoice) for invoice in invoices]

@router.get("/{invoice_id}", response_model=InvoiceSchema)
async def get_invoice(invoice_id: int, db: Session = Depends(get_db)):
    """获取单个发票详情"""
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return InvoiceSchema.from_orm(invoice) 