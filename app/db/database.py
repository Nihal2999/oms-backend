from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from app.core.config import settings

DATABASE_URL = settings.DATABASE_URL

Base = declarative_base()

_engine = None
_SessionLocal = None


def initialize_db():
    global _engine, _SessionLocal

    _engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        echo=False,
    )

    _SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=_engine,
    )


def shutdown_db():
    global _engine

    if _engine is not None:
        _engine.dispose()
        _engine = None


def get_db() -> Generator[Session, None, None]:
    if _SessionLocal is None:
        raise RuntimeError("Database not initialized. Call initialize_db() during app startup.")

    db = _SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        try:
            db.close()
        except Exception:
            pass