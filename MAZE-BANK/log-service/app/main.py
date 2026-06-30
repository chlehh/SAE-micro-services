from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import select, Session

from .database import engine, get_db, init_db
from . import models, schemas, subscriber
from .auth import require_agent, CurrentUser


app = FastAPI(title="MAZE BANK - Log Service")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.on_event("startup")
async def demarrage():
    init_db()
    await subscriber.start()   # on se connecte a NATS et on ecoute les logs


@app.get("/logs", response_model=list[schemas.LogOut])
def list_logs(
    user: CurrentUser = Depends(require_agent),
    db: Session = Depends(get_db),
    service: Optional[str] = None,
    level: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    limit: int = 200,
):
    """Consultation des logs avec selection du type et de la periode (agents)."""
    requete = select(models.LogEntry)
    if service:
        requete = requete.where(models.LogEntry.service == service)
    if level:
        requete = requete.where(models.LogEntry.level == level)
    if date_from:
        requete = requete.where(models.LogEntry.event_time >= date_from)
    if date_to:
        requete = requete.where(models.LogEntry.event_time <= date_to)
    requete = requete.order_by(models.LogEntry.event_time.desc()).limit(limit)
    return db.exec(requete).all()


@app.get("/stats")
def stats(user: CurrentUser = Depends(require_agent), db: Session = Depends(get_db)):
    """Statistiques simples : on compte les logs en parcourant la liste."""
    tous = db.exec(select(models.LogEntry)).all()
    par_service = {}
    par_niveau = {}
    for log in tous:
        par_service[log.service] = par_service.get(log.service, 0) + 1
        par_niveau[log.level] = par_niveau.get(log.level, 0) + 1
    return {"total": len(tous), "par_service": par_service, "par_niveau": par_niveau}
