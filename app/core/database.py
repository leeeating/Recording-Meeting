import logging
from datetime import datetime
from typing import Generator

from sqlalchemy import DateTime, TypeDecorator, create_engine, func
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from shared.config import TAIPEI_TZ, config


class TZDateTime(TypeDecorator):
    """自動將 datetime 轉為 TAIPEI_TZ aware"""

    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value, dialect):
        """存入 DB 前：轉為 naive（去掉 tzinfo，保留 Taipei 時間值）"""
        if value is not None and value.tzinfo is not None:
            value = value.replace(tzinfo=None)
        return value

    def process_result_value(self, value, dialect):
        """從 DB 讀出後：附加 TAIPEI_TZ"""
        if value is not None and value.tzinfo is None:
            value = value.replace(tzinfo=TAIPEI_TZ)
        return value

db_logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    created_at: Mapped[datetime] = mapped_column(default=func.now(), doc="數據創建時間")
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(), onupdate=func.now(), doc="數據最後更新時間"
    )


def create_db_resources(url: str, db_name: str):
    # db_logger.debug(f"Initializing {db_name} DB engine.")

    def is_sqlite_url(url: str) -> bool:
        return url.lower().startswith("sqlite")

    engine = create_engine(
        url, connect_args={"check_same_thread": False} if is_sqlite_url(url) else {}
    )

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    # db_logger.debug(f"{db_name} Engine initialized.")
    return engine, SessionLocal


database_engine, SessionLocal = create_db_resources(config.MEETING_DB_URL, "Meeting")


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
        db.commit()

    except Exception:
        db.rollback()
        db_logger.error("Scheduler DB Transaction Error", exc_info=True)
        raise

    finally:
        db.close()


def initialize_db_schema():
    # db_logger.info("Initializing database schemas...")

    Base.metadata.create_all(bind=database_engine)

    # db_logger.info("Database schemas created successfully.")
