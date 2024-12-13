from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class InvoiceBase(BaseModel):
    invoice_code: str
    invoice_number: str
    invoice_date: str
    total_amount: str
    tax_amount: str
    seller: str
    buyer: str
    file_path: str

class InvoiceCreate(InvoiceBase):
    pass

class Invoice(InvoiceBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True  # 允许从ORM模型创建