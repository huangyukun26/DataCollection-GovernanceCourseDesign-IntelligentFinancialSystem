from sqlalchemy import Column, Integer, String, Numeric, Date, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class Invoice(Base):
    __tablename__ = "invoices"
    
    id = Column(Integer, primary_key=True, index=True)
    doc_id = Column(Integer, ForeignKey("documents.id"))
    invoice_number = Column(String(50), unique=True, index=True)
    invoice_code = Column(String(50))
    seller = Column(String(100))
    buyer = Column(String(100))
    amount = Column(Numeric(15, 2))
    tax_amount = Column(Numeric(15, 2))
    total_amount = Column(Numeric(15, 2))
    invoice_date = Column(Date)
    
    # 关联到documents表
    document = relationship("Document", back_populates="invoice") 