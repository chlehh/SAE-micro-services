from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class AccountCreate(BaseModel):
    label: str = Field(default="Compte courant", max_length=60)
    owner_id: Optional[int] = None   # un agent peut créer un compte pour un client
    owner_name: Optional[str] = None


class AccountUpdate(BaseModel):
    label: str = Field(min_length=1, max_length=60)


class AccountOut(BaseModel):
    id: int
    owner_id: int
    owner_name: str
    number: str
    label: str
    balance: float
    last_operation_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class MoveIn(BaseModel):
    account_id: int
    amount: float = Field(gt=0)


class TransferIn(BaseModel):
    from_id: int
    to_id: int
    amount: float = Field(gt=0)
