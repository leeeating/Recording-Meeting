import logging
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Session
from .config import config

db_logger = logging.getLogger(__name__)

def create_db_resources(url: str, db_name: str):
    """創建 Engine 和 SessionLocal 的輔助函數。"""
    db_logger.info(f"Initializing {db_name} DB engine.")
    
    engine = create_engine(
        url, 
        connect_args={"check_same_thread": False}
    )

    SessionLocal = sessionmaker(
        autocommit=False, 
        autoflush=False, 
        bind=engine
    )
    db_logger.info(f"{db_name} Engine initialized.")
    return engine, SessionLocal



# 雙 ORM 基礎類 - 繼承自 Base 並設置抽象，用於隔離模型映射
class SchedulerBase(DeclarativeBase):
    """用於排程元數據資料庫的模型基類。"""
    __abstract__ = True 

class MeetingBase(DeclarativeBase):
    """用於會議業務資料庫的模型基類。"""
    __abstract__ = True 



scheduler_engine, SchedulerSessionLocal = create_db_resources(
    config.SCHEDULER_DB_URL, "SCHEDULER"
)

meeting_engine, MeetingSessionLocal = create_db_resources(
    config.MEETING_DB_URL, "MEETING"
)


def get_scheduler_db() -> Generator[Session, None, None]:
    db = SchedulerSessionLocal()
    try:
        yield db # 將 Session 實例傳遞給 API 或 Service 路由
        db.commit() # 成功時提交事務

    except Exception as e:
        db.rollback() # 發生錯誤時回滾
        db_logger.error(f"Scheduler DB Transaction Error: {e}", exc_info=True)
        raise # 重新拋出異常給 FastAPI 處理

    finally:
        db.close() # 關閉 Session

def get_meeting_db() -> Generator[Session, None, None]:
    db = MeetingSessionLocal()
    try:
        yield db
        db.commit()

    except Exception as e:
        db.rollback()
        db_logger.error(f"Meeting DB Transaction Error: {e}", exc_info=True)
        raise
    
    finally:
        db.close()


def initialize_db_schema():
    """
    集中處理創建所有資料庫表格的邏輯。
    注意：此函數應在 main.py 應用啟動時被呼叫，且在呼叫前必須載入所有 ORM 模型。
    """
    db_logger.info("Initializing database schemas...")
    
    SchedulerBase.metadata.create_all(bind=scheduler_engine)
    MeetingBase.metadata.create_all(bind=meeting_engine)
    
    db_logger.info("Database schemas created successfully.")