import os

from fastapi import Header, Depends, HTTPException
from jose import jwt, JWTError

SECRET_KEY = os.getenv("SECRET_KEY", "change-me")
ALGORITHM = "HS256"


class CurrentUser:
    """Petit objet qui represente l'utilisateur connecte (lu dans le jeton)."""
    def __init__(self, user_id, role, email, name):
        self.id = user_id
        self.role = role
        self.email = email
        self.name = name


def get_current_user(authorization: str = Header(default="")):
    # Le jeton arrive dans l'en-tete "Authorization: Bearer <jeton>"
    token = authorization.replace("Bearer ", "")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Jeton invalide.")
    return CurrentUser(
        user_id=int(payload["sub"]),
        role=payload.get("role", "client"),
        email=payload.get("email", ""),
        name=payload.get("name", ""),
    )


def require_agent(user: CurrentUser = Depends(get_current_user)):
    """Bloque l'acces si l'utilisateur n'est pas un agent."""
    if user.role != "agent":
        raise HTTPException(status_code=403, detail="Acces reserve aux agents.")
    return user
