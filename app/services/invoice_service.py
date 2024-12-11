from paddleocr import PaddleOCR
import re
from datetime import datetime
from ..models import Document, Invoice
from sqlalchemy.orm import Session
from ..utils.storage import MinioStorage
import os
from uuid import uuid4

class InvoiceService:
    def __init__(self):
        self.ocr = PaddleOCR(use_angle_cls=True, lang="ch")
        self.storage = MinioStorage()
    
    def create_invoice(self, db: Session, file_data: bytes, invoice_data: dict):
        """创建发票记录"""
        # 生成唯一的文件名
        file_name = f"{uuid4()}.jpg"
        
        # 上传文件到MinIO
        file_path = self.storage.upload_file(
            file_data,
            file_name,
            content_type="image/jpeg"
        )
        
        # 创建document记录
        doc = Document(
            doc_type="invoice",
            doc_number=invoice_data['invoice_number'],
            file_path=file_path,
            status="processed"
        )
        db.add(doc)
        db.flush()
        
        # 创建invoice记录
        invoice = Invoice(
            doc_id=doc.id,
            **invoice_data
        )
        db.add(invoice)
        db.commit()
        db.refresh(invoice)
        
        return invoice
    
    def extract_invoice_info(self, image_data: bytes):
        """从发票图片中提取信息"""
        # 保存临时文件
        temp_file = f"temp_{uuid4()}.jpg"
        try:
            with open(temp_file, "wb") as f:
                f.write(image_data)
            
            result = self.ocr.ocr(temp_file, cls=True)
            
            # 初始化提取的字段
            invoice_data = {
                'invoice_number': None,
                'invoice_code': None,
                'seller': None,
                'buyer': None,
                'amount': None,
                'tax_amount': None,
                'total_amount': None,
                'invoice_date': None
            }
            
            # 解析OCR结果
            for line in result:
                text = line[1][0].strip()
                
                # 发票号码
                if "发票号码" in text:
                    invoice_data['invoice_number'] = re.findall(r'\d{8}', text)[0]
                
                # 发票代码
                if "发票代码" in text:
                    invoice_data['invoice_code'] = re.findall(r'\d{12}', text)[0]
                
                # 销售方
                if "销售方" in text or "名称" in text:
                    invoice_data['seller'] = text.split("：")[-1]
                
                # 购买方
                if "购买方" in text:
                    invoice_data['buyer'] = text.split("：")[-1]
                
                # 金额
                if "金额" in text and "¥" in text:
                    amount_str = re.findall(r'¥\s*([\d.]+)', text)[0]
                    invoice_data['amount'] = float(amount_str)
                
                # 税额
                if "税额" in text and "¥" in text:
                    tax_str = re.findall(r'¥\s*([\d.]+)', text)[0]
                    invoice_data['tax_amount'] = float(tax_str)
                
                # 价税合计
                if "价税合计" in text and "¥" in text:
                    total_str = re.findall(r'¥\s*([\d.]+)', text)[0]
                    invoice_data['total_amount'] = float(total_str)
                
                # 开票日期
                if "开票日期" in text:
                    date_str = re.findall(r'\d{4}年\d{1,2}月\d{1,2}日', text)[0]
                    invoice_data['invoice_date'] = datetime.strptime(date_str, '%Y年%m月%d日').date()
            
            return invoice_data
            
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file) 