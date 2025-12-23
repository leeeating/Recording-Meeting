from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler

from shared.config import config

JOB_STORES = {"default": SQLAlchemyJobStore(url=config.SCHEDULER_DB_URL)}

EXECUTORS = {"default": ThreadPoolExecutor(20)}  # 設置 20 個線程來運行 Job


def create_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler(
        jobstores=JOB_STORES,
        executors=EXECUTORS,
        job_defaults={
            "coalesce": True,
            "max_instances": 3,
        },
    )

    return scheduler


scheduler = create_scheduler()
