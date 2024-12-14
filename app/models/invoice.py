from sqlalchemy import Column, Integer, String, DateTime, Float, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    invoice_code = Column(String(50), index=True)  # 发票代码
    invoice_number = Column(String(50), index=True)  # 发票号码
    invoice_date = Column(String(20))  # 开票日期
    total_amount = Column(String(20))  # 金额
    tax_amount = Column(String(20))  # 税额
    seller = Column(String(200))  # 销售方
    buyer = Column(String(200))  # 购买方
    file_path = Column(String(500))  # 文件存储路径
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关联商品明细
    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")