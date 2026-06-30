import os
from datetime import datetime, timezone

import requests
from fastapi import FastAPI, Depends, HTTPException, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import select, Session

from .database import engine, get_db, init_db
from . import models, schemas, events
from .auth import get_current_user, require_agent, CurrentUser

INTERNAL_TOKEN = os.getenv("INTERNAL_TOKEN", "change-me")
ACCOUNT_URL = os.getenv("ACCOUNT_SERVICE_URL", "http://account-service:8000")


app = FastAPI(title="MAZE BANK - Operation Service")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.on_event("startup")
def demarrage():
    init_db()


def check_internal(x_internal_token: str = Header(default="")):
    if x_internal_token != INTERNAL_TOKEN:
        raise HTTPException(status_code=403, detail="Appel interne non autorise.")


@app.post("/operations", response_model=schemas.OperationOut, status_code=201)
def create_operation(payload: schemas.OperationCreate, request: Request,
                     user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    auth_header = request.headers.get("authorization", "")

    # 1. On verifie le compte source et on recupere son IBAN (appel au service des comptes)
    r = requests.get(ACCOUNT_URL + "/accounts/" + str(payload.account_id),
                     headers={"Authorization": auth_header}, timeout=5)
    if r.status_code != 200:
        raise HTTPException(status_code=400, detail="Compte source invalide.")
    account = r.json()

    # 2. Pour un virement, on retrouve le compte destinataire grace a son IBAN
    target_id = None
    target_number = None
    target_name = None
    if payload.type == "transfer":
        if not payload.target_number:
            raise HTTPException(status_code=400, detail="IBAN destinataire requis pour un virement.")
        tr = requests.get(ACCOUNT_URL + "/internal/resolve/" + payload.target_number,
                          headers={"X-Internal-Token": INTERNAL_TOKEN}, timeout=5)
        if tr.status_code != 200:
            raise HTTPException(status_code=400, detail="IBAN destinataire introuvable.")
        tgt = tr.json()
        target_id = tgt["id"]
        target_number = tgt["number"]
        target_name = tgt["owner_name"]
        if target_id == payload.account_id:
            raise HTTPException(status_code=400, detail="Impossible de virer vers le meme compte.")

    op = models.Operation(
        account_id=payload.account_id,
        account_number=account["number"],
        owner_id=user.id,
        type=payload.type,
        amount=payload.amount,
        target_account_id=target_id,
        target_number=target_number,
        target_owner_name=target_name,
        created_by=user.name or user.email,
        status="pending",
    )

    # 3. Le depot est credite tout de suite ; retrait et virement attendent un agent.
    if payload.type == "deposit":
        cr = requests.post(ACCOUNT_URL + "/internal/credit",
                           headers={"X-Internal-Token": INTERNAL_TOKEN},
                           json={"account_id": payload.account_id, "amount": payload.amount}, timeout=5)
        if cr.status_code != 200:
            raise HTTPException(status_code=400, detail=cr.json().get("detail", "Depot impossible."))
        op.status = "approved"
        op.decided_at = datetime.now(timezone.utc)

    db.add(op)
    db.commit()
    db.refresh(op)
    events.publish_log("INFO", "operation_created", op.type + " de " + str(op.amount) + " (" + op.status + ")")
    return op


@app.get("/operations/mine", response_model=list[schemas.OperationOut])
def my_operations(user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.exec(
        select(models.Operation).where(models.Operation.owner_id == user.id).order_by(models.Operation.created_at.desc())
    ).all()


@app.get("/operations/pending", response_model=list[schemas.OperationOut])
def pending_operations(user: CurrentUser = Depends(require_agent), db: Session = Depends(get_db)):
    return db.exec(
        select(models.Operation).where(models.Operation.status == "pending").order_by(models.Operation.created_at)
    ).all()


@app.get("/operations/account/{account_id}", response_model=list[schemas.OperationOut])
def account_operations(account_id: int, user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.exec(
        select(models.Operation).where(models.Operation.account_id == account_id).order_by(models.Operation.created_at.desc())
    ).all()
    if user.role != "agent":
        rows = [o for o in rows if o.owner_id == user.id]
    return rows


@app.get("/operations/{operation_id}", response_model=schemas.OperationOut)
def get_operation(operation_id: int, user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    op = db.get(models.Operation, operation_id)
    if not op:
        raise HTTPException(status_code=404, detail="Operation introuvable.")
    if user.role != "agent" and op.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Acces refuse.")
    return op


@app.patch("/operations/{operation_id}/status", response_model=schemas.OperationOut, dependencies=[Depends(check_internal)])
def set_status(operation_id: int, payload: schemas.StatusIn, db: Session = Depends(get_db)):
    op = db.get(models.Operation, operation_id)
    if not op:
        raise HTTPException(status_code=404, detail="Operation introuvable.")
    op.status = payload.status
    op.decided_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(op)
    return op
