from app.services.scheduler_manager import scheduler_manager
from app.services.alert_service import check_and_send_alerts

from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler(
    job_defaults={
        "coalesce": True,
        "max_instances": 1,
        "misfire_grace_time": 60
    }
)

_scheduler_started = False


def start_scheduler():
    global _scheduler_started

    if _scheduler_started:
        return  # prevent double start

    scheduler.start()
    _scheduler_started = True