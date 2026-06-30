from datetime import datetime, timezone
from typing import Optional

from sqlmodel import SQLModel, Field


class Operation(SQLModel, table=True):
    __tablename__ = "operations"

    id: Optional[int] = Field(default=None, primary_key=True)
    account_id: int = Field(index=True)
    account_number: str
    owner_id: int = Field(index=True)
    type: str                                         # deposit | withdrawal | transfer
    amount: float
    target_account_id: Optional[int] = Field(default=None)
    target_number: Optional[str] = Field(default=None)
    target_owner_name: Optional[str] = Field(default=None)
    status: str = Field(default="pending")            # pending | approved | rejected
    created_by: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    decided_at: Optional[datetime] = Field(default=None)
