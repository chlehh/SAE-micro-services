import os
import json
from datetime import datetime, timezone

import nats
from sqlmodel import Session

from .database import engine
from . import models

NATS_URL = os.getenv("NATS_URL", "nats://nats:4222")

_nc = None   # garde la connexion ouverte


def _date(valeur):
    """Transforme le texte de date recu en vraie date (sinon : maintenant)."""
    if not valeur:
        return datetime.now(timezone.utc)
    try:
        return datetime.fromisoformat(valeur)
    except Exception:
        return datetime.now(timezone.utc)


async def _reception(msg):
    # Appele automatiquement a chaque log recu sur NATS
    try:
        data = json.loads(msg.data.decode())
    except Exception:
        return
    with Session(engine) as db:
        entry = models.LogEntry(
            service=data.get("service", "inconnu"),
            level=data.get("level", "INFO"),
            action=data.get("action", ""),
            message=data.get("message", ""),
            event_time=_date(data.get("timestamp")),
        )
        db.add(entry)
        db.commit()


async def start():
    global _nc
    try:
        _nc = await nats.connect(NATS_URL)
        await _nc.subscribe("logs.>", cb=_reception)
        print("[log-service] Abonne a NATS sur le sujet 'logs.>'")
    except Exception as exc:
        print("[log-service] NATS indisponible au demarrage :", exc)
