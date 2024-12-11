from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from .base import BaseModel

class Document(BaseModel):
    __tablename__ = "documents"
    
    doc_type = Column(String(20))  # 合同/发票/银行流水
    doc_number = Column(String(50))
    file_path = Column(String(255))
    status = Column(String(20))
    
    # 添加与Invoice的关联
    invoice = relationship("Invoice", back_populates="document", uselist=False) 