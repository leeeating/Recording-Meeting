import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


class BaseError(Exception):
    def __init__(self, detail: str, name: str | None = None):
        self.detail = detail
        self.name = name or self.__class__.__name__
        super().__init__(self.detail)


class NotFoundError(BaseError):
    pass


class SchedulingError(BaseError):
    pass

class ActionError(BaseError):
    pass

def register_exception_handlers(app: FastAPI):
    @app.exception_handler(NotFoundError)
    async def not_found_handler(request: Request, exc: NotFoundError):
        return JSONResponse(
            status_code=404, content={"error": "找不到資源", "detail": exc.detail}
        )

    @app.exception_handler(SchedulingError)
    async def scheduling_error_handler(request: Request, exc: SchedulingError):
        logger.error(f"Scheduling Error: {exc.detail}")

        return JSONResponse(
            status_code=400, content={"error": "排程失敗", "detail": exc.detail}
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        # 這裡可以加入 logging 紀錄真正的錯誤堆疊
        logger.error(f"Unhandled Exception: {exc}", exc_info=True)

        return JSONResponse(
            status_code=500,
            content={"error": "伺服器內部發生未知錯誤", "detail": str(exc)},
        )

    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
        logger.error(f"Database Error: {exc}", exc_info=True)

        return JSONResponse(
            status_code=500,
            content={
                "error": "Database Error",
                "detail": "資料庫操作失敗，請檢查欄位約束。",
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        error_msg = exc.errors()[0]["msg"]
        logger.warning(f"驗證失敗 : {error_msg}")

        return JSONResponse(
            status_code=422,
            content={"error": "驗證失敗", "detail": error_msg},
        )
