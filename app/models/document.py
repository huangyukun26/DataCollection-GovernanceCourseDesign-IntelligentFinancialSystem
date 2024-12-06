from sqlalchemy import Column, Integer, String, DateTime, Enum
from app.db.database import Base

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    doc_type = Column(String(20))  # 合同/发票/银行流水
    doc_number = Column(String(50))
    file_path = Column(String(255))
    status = Column(String(20))
    created_at = Column(DateTime)
    updated_at = Column(DateTime) 