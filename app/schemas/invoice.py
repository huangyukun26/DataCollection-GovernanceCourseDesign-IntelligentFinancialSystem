from pydantic import BaseModel
from datetime import date
from decimal import Decimal
from typing import Optional

class InvoiceBase(BaseModel):
    invoice_number: str
    invoice_code: str
    seller: str
    buyer: str
    amount: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    invoice_date: date

class InvoiceCreate(InvoiceBase):
    pass

class Invoice(InvoiceBase):
    id: int
    doc_id: int

    class Config:
        from_attributes = True  # 允许从ORM模型创建 