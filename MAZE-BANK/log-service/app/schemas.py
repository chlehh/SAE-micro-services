from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class LogOut(BaseModel):
    id: int
    service: str
    level: str
    action: Optional[str] = None
    message: Optional[str] = None
    event_time: datetime

    class Config:
        from_attributes = True
