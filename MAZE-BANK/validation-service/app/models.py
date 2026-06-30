from datetime import datetime, timezone
from typing import Optional

from sqlmodel import SQLModel, Field


class Validation(SQLModel, table=True):
    __tablename__ = "validations"

    id: Optional[int] = Field(default=None, primary_key=True)
    operation_id: int = Field(index=True)
    decision: str                                     # approved | rejected
    agent_id: int
    agent_name: Optional[str] = Field(default=None)
    detail: Optional[str] = Field(default=None)
    decided_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
