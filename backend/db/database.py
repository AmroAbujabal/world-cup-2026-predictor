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


# .strip() guards against a trailing space/newline pasted into the host's env var
# (e.g. "...sslmode=require " → psycopg2 "invalid sslmode value").
DATABASE_URL = os.getenv("DATABASE_URL", _DEFAULT_DB).strip()

# Neon / Render / Heroku hand out `postgres://` URLs; SQLAlchemy 2.0 needs `postgresql://`.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
# Recycle connections so serverless Postgres (Neon) doesn't hand back a dead socket
_engine_kwargs = {"connect_args": _connect_args}
if not DATABASE_URL.startswith("sqlite"):
    _engine_kwargs["pool_pre_ping"] = True
    _engine_kwargs["pool_recycle"] = 300
engine = create_engine(DATABASE_URL, **_engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
