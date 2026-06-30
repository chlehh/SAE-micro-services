from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from jose import jwt, JWTError
from sqlmodel import select, Session

from .database import engine, get_db, init_db
from . import models, schemas, events
from .security import hash_password, verify_password, create_access_token, SECRET_KEY, ALGORITHM


app = FastAPI(title="MAZE BANK - Auth Service")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.on_event("startup")
def demarrage():
    init_db()


def current_user(authorization: str = Header(default=""), db: Session = Depends(get_db)) -> models.User:
    """Lit le jeton, puis retrouve l'utilisateur en base."""
    token = authorization.replace("Bearer ", "")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(status_code=401, detail="Jeton invalide.")
    user = db.get(models.User, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="Utilisateur introuvable.")
    return user


@app.post("/register", response_model=schemas.UserOut, status_code=201)
def register(payload: schemas.RegisterIn, db: Session = Depends(get_db)):
    # On verifie que l'e-mail n'est pas deja pris
    deja = db.exec(select(models.User).where(models.User.email == payload.email)).first()
    if deja:
        raise HTTPException(status_code=400, detail="Cet e-mail est deja utilise.")

    user = models.User(
        full_name=payload.full_name,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=payload.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    events.publish_log("INFO", "register", "Nouveau compte " + user.role + " : " + user.email)
    return user


@app.post("/login", response_model=schemas.TokenOut)
def login(payload: schemas.LoginIn, db: Session = Depends(get_db)):
    user = db.exec(select(models.User).where(models.User.email == payload.email)).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        events.publish_log("WARNING", "login_failed", "Echec de connexion : " + payload.email)
        raise HTTPException(status_code=401, detail="Identifiants invalides.")

    token = create_access_token(
        {"sub": str(user.id), "role": user.role, "email": user.email, "name": user.full_name}
    )
    events.publish_log("INFO", "login", "Connexion reussie : " + user.email)
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user.role,
        "full_name": user.full_name,
        "user_id": user.id,
    }


@app.get("/me", response_model=schemas.UserOut)
def me(user: models.User = Depends(current_user)):
    return user


@app.get("/clients", response_model=list[schemas.UserOut])
def list_clients(user: models.User = Depends(current_user), db: Session = Depends(get_db)):
    """Liste des clients - reservee aux agents (pour consulter leurs comptes)."""
    if user.role != "agent":
        raise HTTPException(status_code=403, detail="Acces reserve aux agents.")
    return db.exec(select(models.User).where(models.User.role == "client")).all()
