from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

class InvoiceItemBase(BaseModel):
    item_name: str
    quantity: Optional[float] = None
    unit: Optional[str] = None
    unit_price: Optional[float] = None
    amount: Optional[float] = None

class InvoiceItemCreate(InvoiceItemBase):
    pass

class InvoiceItem(InvoiceItemBase):
    id: int
    invoice_id: int

    class Config:
        orm_mode = True

class InvoiceBase(BaseModel):
    invoice_code: Optional[str] = None
    invoice_number: Optional[str] = None
    invoice_date: Optional[str] = None
    total_amount: Optional[str] = None
    tax_amount: Optional[str] = None
    seller: Optional[str] = None
    buyer: Optional[str] = None
    file_path: Optional[str] = None

class InvoiceCreate(InvoiceBase):
    pass

class Invoice(InvoiceBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    items: List[InvoiceItem] = []

    class Config:
        orm_mode = True