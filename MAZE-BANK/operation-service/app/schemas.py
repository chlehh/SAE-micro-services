from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class OperationCreate(BaseModel):
    account_id: int
    type: Literal["deposit", "withdrawal", "transfer"]
    amount: float = Field(gt=0)
    target_number: Optional[str] = None  # IBAN destinataire (virement)


class OperationOut(BaseModel):
    id: int
    account_id: int
    account_number: str
    owner_id: int
    type: str
    amount: float
    target_account_id: Optional[int] = None
    target_number: Optional[str] = None
    target_owner_name: Optional[str] = None
    status: str
    created_by: Optional[str] = None
    created_at: datetime
    decided_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class StatusIn(BaseModel):
    status: Literal["approved", "rejected"]
