from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

from app.core.logger import setup_logger
from app.core.scheduler import scheduler
from app.core.database import initialize_db_schema, database_engine
from app.core.exceptions import register_exception_handlers
from app.controllers.meeting_controller import router as meeting_router
from app.controllers.task_controller import router as task_router

logger = setup_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        initialize_db_schema()
        scheduler.start()

        jobs = scheduler.get_jobs()
        if not jobs:
            logger.info("📋 目前排程器中沒有任何待處理任務。")
        else:
            logger.info(f"📋 偵測到已存在的任務數 : {len(jobs)}")

    except Exception as e:
        logger.critical(f"Failed to initialize database schema: {e}")
        raise e

    yield

    database_engine.dispose()
    logger.info("Database engine disposed.")


# 2. 初始化應用程式
app = FastAPI(
    title="會議錄音管理系統",
    description="""
    這是一個用於管理會議錄音與自動化任務的 API 服務。
    支援功能：
    - **會議管理**: 上傳、查詢錄音檔
    - **任務追蹤**: 監控處理進度
    """,
    version="1.0.0",
    lifespan=lifespan,
)

# 3. 中介軟體設定 (Middleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)


app.include_router(meeting_router)
app.include_router(task_router)


@app.get("/", include_in_schema=False)
async def redirect_to_docs():
    """自動導向至 Swagger API 文件"""
    return RedirectResponse(url="/docs")
