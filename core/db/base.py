"""Database base configuration using SQLAlchemy."""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from core.config import settings

DATABASE_URL = settings.get_db_url()
engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()


def get_db():
    """Yield a database session and ensure it closes afterwards."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
