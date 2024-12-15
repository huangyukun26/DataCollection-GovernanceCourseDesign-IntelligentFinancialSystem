from typing import List, Optional
from pydantic import BaseModel, Field
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
    total_amount: Optional[float] = Field(None, description="发票金额")
    tax_amount: Optional[float] = Field(None, description="税额")
    seller: Optional[str] = None
    buyer: Optional[str] = None
    file_path: Optional[str] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.strftime("%Y-%m-%d") if v else None
        }

class InvoiceCreate(InvoiceBase):
    pass

class Invoice(InvoiceBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    items: List[InvoiceItem] = []

    class Config:
        orm_mode = True