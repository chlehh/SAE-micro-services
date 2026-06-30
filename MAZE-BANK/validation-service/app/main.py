import os

import requests
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import select, Session

from .database import engine, get_db, init_db
from . import models, schemas, events
from .auth import require_agent, CurrentUser

INTERNAL_TOKEN = os.getenv("INTERNAL_TOKEN", "change-me")
ACCOUNT_URL = os.getenv("ACCOUNT_SERVICE_URL", "http://account-service:8000")
OPERATION_URL = os.getenv("OPERATION_SERVICE_URL", "http://operation-service:8000")


app = FastAPI(title="MAZE BANK - Validation Service")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.on_event("startup")
def demarrage():
    init_db()


def recuperer_operation(operation_id, auth):
    r = requests.get(OPERATION_URL + "/operations/" + str(operation_id),
                     headers={"Authorization": auth}, timeout=5)
    if r.status_code != 200:
        raise HTTPException(status_code=404, detail="Operation introuvable.")
    return r.json()


def changer_statut(operation_id, statut):
    r = requests.patch(OPERATION_URL + "/operations/" + str(operation_id) + "/status",
                       headers={"X-Internal-Token": INTERNAL_TOKEN},
                       json={"status": statut}, timeout=5)
    if r.status_code != 200:
        raise HTTPException(status_code=502, detail="Mise a jour du statut impossible.")
    return r.json()


@app.get("/pending")
def list_pending(request: Request, user: CurrentUser = Depends(require_agent)):
    # On demande la liste des operations en attente au service des operations
    auth = request.headers.get("authorization", "")
    r = requests.get(OPERATION_URL + "/operations/pending",
                     headers={"Authorization": auth}, timeout=5)
    if r.status_code != 200:
        raise HTTPException(status_code=502, detail="Impossible de recuperer les operations en attente.")
    return r.json()


@app.post("/{operation_id}/approve", response_model=schemas.ValidationOut)
def approve(operation_id: int, request: Request, user: CurrentUser = Depends(require_agent), db: Session = Depends(get_db)):
    auth = request.headers.get("authorization", "")
    op = recuperer_operation(operation_id, auth)
    if op["status"] != "pending":
        raise HTTPException(status_code=400, detail="Cette operation a deja ete traitee.")

    # On applique le mouvement d'argent au moment de la validation
    if op["type"] == "withdrawal":
        mv = requests.post(ACCOUNT_URL + "/internal/debit",
                           headers={"X-Internal-Token": INTERNAL_TOKEN},
                           json={"account_id": op["account_id"], "amount": op["amount"]}, timeout=5)
    elif op["type"] == "transfer":
        mv = requests.post(ACCOUNT_URL + "/internal/transfer",
                           headers={"X-Internal-Token": INTERNAL_TOKEN},
                           json={"from_id": op["account_id"], "to_id": op["target_account_id"], "amount": op["amount"]}, timeout=5)
    else:  # depot reste eventuellement en attente
        mv = requests.post(ACCOUNT_URL + "/internal/credit",
                           headers={"X-Internal-Token": INTERNAL_TOKEN},
                           json={"account_id": op["account_id"], "amount": op["amount"]}, timeout=5)

    if mv.status_code != 200:
        detail = mv.json().get("detail", "Mouvement refuse (solde insuffisant ?)")
        events.publish_log("WARNING", "validation_failed", "Op #" + str(operation_id) + " : " + detail)
        raise HTTPException(status_code=400, detail=detail)

    changer_statut(operation_id, "approved")

    record = models.Validation(
        operation_id=operation_id, decision="approved",
        agent_id=user.id, agent_name=user.name, detail=op["type"] + " de " + str(op["amount"]),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    events.publish_log("INFO", "validation", "Op #" + str(operation_id) + " approuvee par " + user.name)
    return record


@app.post("/{operation_id}/reject", response_model=schemas.ValidationOut)
def reject(operation_id: int, request: Request, user: CurrentUser = Depends(require_agent), db: Session = Depends(get_db)):
    auth = request.headers.get("authorization", "")
    op = recuperer_operation(operation_id, auth)
    if op["status"] != "pending":
        raise HTTPException(status_code=400, detail="Cette operation a deja ete traitee.")

    changer_statut(operation_id, "rejected")

    record = models.Validation(
        operation_id=operation_id, decision="rejected",
        agent_id=user.id, agent_name=user.name, detail=op["type"] + " de " + str(op["amount"]),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    events.publish_log("INFO", "validation", "Op #" + str(operation_id) + " rejetee par " + user.name)
    return record


@app.get("/history", response_model=list[schemas.ValidationOut])
def history(user: CurrentUser = Depends(require_agent), db: Session = Depends(get_db)):
    return db.exec(select(models.Validation).order_by(models.Validation.decided_at.desc())).all()
