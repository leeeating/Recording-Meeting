import logging
from contextlib import contextmanager


@contextmanager
def action(action_name: str, logger: logging.Logger):
    """
    統一處理每步驟的error
    """
    logger.debug(f"開始執行操作: [{action_name}]")
    try:
        yield
        logger.info(f"成功執行操作: [{action_name}]")

    except Exception as e:
        logger.error(f"操作失敗 [{action_name}]: {e}")
        raise
