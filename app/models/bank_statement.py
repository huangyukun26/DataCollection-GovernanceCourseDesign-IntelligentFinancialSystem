from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class BankStatement(Base):
    __tablename__ = "bank_statements"

    id = Column(Integer, primary_key=True, index=True)
    account_number = Column(String(50), index=True)  # 账号
    transaction_date = Column(DateTime)  # 交易日期
    transaction_type = Column(String(20))  # 交易类型（收入/支出）
    amount = Column(Float)  # 金额
    balance = Column(Float)  # 余额
    counterparty = Column(String(200))  # 交易对手方
    description = Column(String(500))  # 交易描述
    bank_type = Column(String(50))  # 银行类型
    file_path = Column(String(500))  # 原始文件路径
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now()) 