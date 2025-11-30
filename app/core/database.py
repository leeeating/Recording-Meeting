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
    """
    統一的 ORM 基礎類，用於單一資料庫架構。
    所有 ORM 模型 (Meeting 和 Task) 都將繼承此類。
    """
    # Auditing Columns - 適用於所有表格 (Meeting, Task)
    created_at: Mapped[datetime] = mapped_column(
        default=func.now(), 
        doc="數據創建時間"
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(), 
        onupdate=func.now(),
        doc="數據最後更新時間"
    )

def create_db_resources(url: str, db_name: str):
    """創建 Engine 和 SessionLocal 的輔助函數。"""
    db_logger.info(f"Initializing {db_name} DB engine.")
    
    def is_sqlite_url(url: str) -> bool:
        return url.lower().startswith("sqlite")

    engine = create_engine(
        url, 
        connect_args={"check_same_thread": False} if is_sqlite_url(url) else {}
    )

    SessionLocal = sessionmaker(
        autocommit=False, 
        autoflush=False, 
        bind=engine
    )
    db_logger.info(f"{db_name} Engine initialized.")
    return engine, SessionLocal

database_engine, SessionLocal = create_db_resources(
    config.DATABASE_URL, "SCHEDULER"
)

def get_scheduler_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db # 將 Session 實例傳遞給 API 或 Service 路由
        db.commit() # 成功時提交事務

    except Exception as e:
        db.rollback() # 發生錯誤時回滾
        db_logger.error(f"Scheduler DB Transaction Error: {e}", exc_info=True)
        raise # 重新拋出異常給 FastAPI 處理

    finally:
        db.close() # 關閉 Session

def initialize_db_schema():
    """
    集中處理創建所有資料庫表格的邏輯。
    注意：此函數應在 main.py 應用啟動時被呼叫，且在呼叫前必須載入所有 ORM 模型。
    """
    db_logger.info("Initializing database schemas...")
    
    Base.metadata.create_all(bind=database_engine)

    db_logger.info("Database schemas created successfully.")