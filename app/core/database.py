import logging
from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Session

from .config import config

db_logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    created_at: Mapped[datetime] = mapped_column(default=func.now(), doc="數據創建時間")
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(), onupdate=func.now(), doc="數據最後更新時間"
    )


def create_db_resources(url: str, db_name: str):
    db_logger.info(f"Initializing {db_name} DB engine.")

    def is_sqlite_url(url: str) -> bool:
        return url.lower().startswith("sqlite")

    engine = create_engine(
        url, connect_args={"check_same_thread": False} if is_sqlite_url(url) else {}
    )

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db_logger.info(f"{db_name} Engine initialized.")
    return engine, SessionLocal


database_engine, SessionLocal = create_db_resources(config.MEETING_DB_URL, "SCHEDULER")


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
        db.commit()

    except Exception as e:
        db.rollback()
        db_logger.error(f"Scheduler DB Transaction Error: {e}", exc_info=True)
        raise

    finally:
        db.close()


def initialize_db_schema():
    db_logger.info("Initializing database schemas...")

    Base.metadata.create_all(bind=database_engine)

    db_logger.info("Database schemas created successfully.")
