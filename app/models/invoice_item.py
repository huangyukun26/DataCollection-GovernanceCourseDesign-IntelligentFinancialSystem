from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class InvoiceItem(Base):
    __tablename__ = "invoice_items"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False)
    item_name = Column(String(500))  # 商品名称
    quantity = Column(Float, nullable=True)  # 数量
    unit = Column(String(50), nullable=True)  # 单位
    unit_price = Column(Float, nullable=True)  # 单价
    amount = Column(Float, nullable=True)  # 金额

    # 关联关系
    invoice = relationship("Invoice", back_populates="items") 