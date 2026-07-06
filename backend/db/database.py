# backend/db/database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# Anchor the default SQLite DB to the repo root so it resolves the same no matter
# which directory the server is launched from (avoids a blank DB when run from ~).
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_DEFAULT_DB = f"sqlite:///{os.path.join(_REPO_ROOT, 'dev.db')}"

DATABASE_URL = os.getenv("DATABASE_URL", _DEFAULT_DB)

_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=_connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
