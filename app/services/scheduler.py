from app.services.scheduler_manager import scheduler_manager
from app.services.alert_service import check_and_send_alerts

def start_scheduler():
    scheduler = scheduler_manager.scheduler

    # IMPORTANT: prevent duplicate job registration
    if not scheduler.get_job("alert_job"):
        scheduler.add_job(
            check_and_send_alerts,
            "interval",
            minutes=15,
            id="alert_job",
            replace_existing=True,
        )

    scheduler_manager.start()