import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Build DATABASE_URL from individual env vars when they are present
# (Docker Compose sets POSTGRES_HOST, POSTGRES_USER, etc. but not DATABASE_URL)
_pg_host = os.getenv("POSTGRES_HOST")
if _pg_host:
    _pg_user = os.getenv("POSTGRES_USER", "dataprismai")
    _pg_pass = os.getenv("POSTGRES_PASSWORD", "dataprismai")
    _pg_port = os.getenv("POSTGRES_PORT", "5432")
    _pg_db   = os.getenv("POSTGRES_DB", "dataprismai")
    DATABASE_URL = f"postgresql://{_pg_user}:{_pg_pass}@{_pg_host}:{_pg_port}/{_pg_db}"
else:
    DATABASE_URL = settings.database_url

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
