import os

from sqlmodel import SQLModel, Session, create_engine

# Konfiguration über Umgebungsvariablen, Default bleibt die lokale SQLite-Datei.
# Für PostgreSQL z. B.: DATABASE_URL=postgresql+psycopg://user:pw@host/db
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./entries.db")
SQL_ECHO = os.getenv("SQL_ECHO", "false").lower() in ("1", "true", "yes")

# check_same_thread ist eine reine SQLite-Option, andere Treiber lehnen sie ab
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, echo=SQL_ECHO, connect_args=connect_args)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
