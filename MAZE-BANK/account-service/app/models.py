from datetime import datetime, timezone
from typing import Optional

from sqlmodel import SQLModel, Field


class Account(SQLModel, table=True):
    __tablename__ = "accounts"

    id: Optional[int] = Field(default=None, primary_key=True)
    owner_id: int = Field(index=True)                 # id de l'utilisateur (auth-service)
    owner_name: str
    number: str = Field(index=True, unique=True)      # IBAN simplifie
    label: str = Field(default="Compte courant")
    balance: float = Field(default=0.0)               # solde en euros (arrondi a 2 decimales)
    last_operation_at: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
