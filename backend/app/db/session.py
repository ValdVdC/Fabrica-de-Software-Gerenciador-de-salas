"""
Configuração da engine e sessão SQLAlchemy 2.0.
"""

from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from app.config import settings

db_url = settings.DATABASE_URL
if db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)

engine = create_engine(
    db_url,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Classe base declarativa compartilhada por todos os modelos."""
    pass


def get_db() -> Generator[Session, None, None]:
    """Dependency injection para sessões de banco no FastAPI."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
