import os

from sqlmodel import SQLModel, create_engine, Session

# On utilise SQLite : un simple fichier, aucune base a installer.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./local.db")

# check_same_thread=False : indispensable avec FastAPI quand on utilise SQLite.
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


def get_db():
    """Donne une session de base de donnees (cf. TD5 : Session(engine))."""
    with Session(engine) as session:
        yield session


def init_db():
    """Cree les tables au demarrage si elles n'existent pas encore."""
    SQLModel.metadata.create_all(engine)
