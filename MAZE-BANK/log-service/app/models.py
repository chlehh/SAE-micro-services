from datetime import datetime, timezone
from typing import Optional

from sqlmodel import SQLModel, Field


class LogEntry(SQLModel, table=True):
    __tablename__ = "logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    service: str = Field(index=True)
    level: str = Field(index=True)                     # INFO | WARNING | ERROR
    action: Optional[str] = Field(default=None, index=True)
    message: Optional[str] = Field(default=None)
    event_time: datetime = Field(index=True, default_factory=lambda: datetime.now(timezone.utc))
    received_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
