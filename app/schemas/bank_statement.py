from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime

class BankStatementBase(BaseModel):
    account_number: Optional[str] = None
    transaction_date: Optional[datetime] = None
    transaction_type: Optional[str] = None
    amount: Optional[float] = Field(None, description="交易金额")
    balance: Optional[float] = Field(None, description="账户余额")
    counterparty: Optional[str] = None
    description: Optional[str] = None
    bank_name: Optional[str] = None
    file_path: Optional[str] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.strftime("%Y-%m-%d %H:%M:%S") if v else None
        }

class BankStatementCreate(BankStatementBase):
    pass

class BankStatement(BankStatementBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class BankStatementUpdate(BankStatementBase):
    pass

class BankStatementListResponse(BaseModel):
    status: str
    data: List[BankStatement]
    total: int

    class Config:
        orm_mode = True 