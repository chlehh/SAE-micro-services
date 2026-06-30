import os
import random
from datetime import datetime, timezone

from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import select, Session

from .database import engine, get_db, init_db
from . import models, schemas, events
from .auth import get_current_user, CurrentUser

INTERNAL_TOKEN = os.getenv("INTERNAL_TOKEN", "change-me")


app = FastAPI(title="MAZE BANK - Account Service")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.on_event("startup")
def demarrage():
    init_db()


def check_internal(x_internal_token: str = Header(default="")):
    """Securite simple : seuls les autres services (qui connaissent le jeton) peuvent appeler /internal."""
    if x_internal_token != INTERNAL_TOKEN:
        raise HTTPException(status_code=403, detail="Appel interne non autorise.")


def generer_iban():
    return "FR76" + "".join(str(random.randint(0, 9)) for _ in range(18))


@app.get("/accounts", response_model=list[schemas.AccountOut])
def my_accounts(user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.exec(select(models.Account).where(models.Account.owner_id == user.id)).all()


@app.post("/accounts", response_model=schemas.AccountOut, status_code=201)
def create_account(payload: schemas.AccountCreate, user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    # Un client cree son propre compte ; un agent peut le creer pour un client.
    if user.role == "agent" and payload.owner_id:
        owner_id = payload.owner_id
        owner_name = payload.owner_name or ("Client #" + str(payload.owner_id))
    else:
        owner_id = user.id
        owner_name = user.name

    account = models.Account(
        owner_id=owner_id,
        owner_name=owner_name,
        number=generer_iban(),
        label=payload.label,
        balance=0.0,
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    events.publish_log("INFO", "account_created", "Compte " + account.number + " cree pour " + owner_name)
    return account


@app.get("/accounts/{account_id}", response_model=schemas.AccountOut)
def get_account(account_id: int, user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    account = db.get(models.Account, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Compte introuvable.")
    if user.role != "agent" and account.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Acces refuse a ce compte.")
    return account


@app.patch("/accounts/{account_id}", response_model=schemas.AccountOut)
def update_account(account_id: int, payload: schemas.AccountUpdate, user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    """Renommer un compte (le proprietaire ou un agent)."""
    account = db.get(models.Account, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Compte introuvable.")
    if user.role != "agent" and account.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Vous ne pouvez modifier que vos propres comptes.")
    account.label = payload.label.strip()
    db.commit()
    db.refresh(account)
    events.publish_log("INFO", "account_renamed", "Compte " + account.number + " renomme")
    return account


@app.delete("/accounts/{account_id}")
def delete_account(account_id: int, user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    account = db.get(models.Account, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Compte introuvable.")
    # Un client ne supprime que ses comptes ; un agent peut supprimer n'importe quel compte.
    if user.role != "agent" and account.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Vous ne pouvez supprimer que vos propres comptes.")
    if account.balance != 0:
        raise HTTPException(status_code=400, detail="Impossible de supprimer un compte qui contient de l'argent. Videz-le d'abord.")
    numero = account.number
    db.delete(account)
    db.commit()
    events.publish_log("INFO", "account_deleted", "Compte " + numero + " supprime par " + user.name)
    return {"deleted": True, "id": account_id, "number": numero}


@app.get("/clients/{client_id}/accounts", response_model=list[schemas.AccountOut])
def client_accounts(client_id: int, user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    """Reserve aux agents : voir les comptes d'un client (solde, derniere operation)."""
    if user.role != "agent":
        raise HTTPException(status_code=403, detail="Acces reserve aux agents.")
    return db.exec(select(models.Account).where(models.Account.owner_id == client_id)).all()


# ---------------- Endpoints internes (appeles par les autres services) ----------------

@app.get("/internal/resolve/{number}", dependencies=[Depends(check_internal)])
def resolve_by_number(number: str, db: Session = Depends(get_db)):
    account = db.exec(select(models.Account).where(models.Account.number == number)).first()
    if not account:
        raise HTTPException(status_code=404, detail="IBAN destinataire introuvable.")
    return {"id": account.id, "number": account.number, "owner_name": account.owner_name}


@app.post("/internal/credit", dependencies=[Depends(check_internal)])
def credit(payload: schemas.MoveIn, db: Session = Depends(get_db)):
    account = db.get(models.Account, payload.account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Compte introuvable.")
    account.balance = round(account.balance + payload.amount, 2)
    account.last_operation_at = datetime.now(timezone.utc)
    db.commit()
    return {"balance": account.balance}


@app.post("/internal/debit", dependencies=[Depends(check_internal)])
def debit(payload: schemas.MoveIn, db: Session = Depends(get_db)):
    account = db.get(models.Account, payload.account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Compte introuvable.")
    if account.balance < payload.amount:
        raise HTTPException(status_code=400, detail="Solde insuffisant.")
    account.balance = round(account.balance - payload.amount, 2)
    account.last_operation_at = datetime.now(timezone.utc)
    db.commit()
    return {"balance": account.balance}


@app.post("/internal/transfer", dependencies=[Depends(check_internal)])
def transfer(payload: schemas.TransferIn, db: Session = Depends(get_db)):
    src = db.get(models.Account, payload.from_id)
    dst = db.get(models.Account, payload.to_id)
    if not src or not dst:
        raise HTTPException(status_code=404, detail="Compte source ou destination introuvable.")
    if src.balance < payload.amount:
        raise HTTPException(status_code=400, detail="Solde insuffisant.")
    maintenant = datetime.now(timezone.utc)
    src.balance = round(src.balance - payload.amount, 2)
    dst.balance = round(dst.balance + payload.amount, 2)
    src.last_operation_at = maintenant
    dst.last_operation_at = maintenant
    db.commit()
    return {"from_balance": src.balance, "to_balance": dst.balance}
