from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
import logging

logger = logging.getLogger(__name__)


class SchedulerManager:
    def __init__(self):
        self.scheduler = BackgroundScheduler(
            jobstores={"default": MemoryJobStore()},
            executors={"default": ThreadPoolExecutor(5)},
            job_defaults={
                "coalesce": True,          # merge missed runs
                "max_instances": 1,        # prevent duplicates
                "misfire_grace_time": 300  # allow 5 min delay recovery
            },
        )

    def start(self):
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("🚀 Scheduler started")

    def shutdown(self):
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("🛑 Scheduler stopped")


scheduler_manager = SchedulerManager()