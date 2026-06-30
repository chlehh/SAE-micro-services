from datetime import datetime

from pydantic import BaseModel


class ValidationOut(BaseModel):
    id: int
    operation_id: int
    decision: str
    agent_id: int
    agent_name: str | None = None
    detail: str | None = None
    decided_at: datetime

    class Config:
        from_attributes = True
