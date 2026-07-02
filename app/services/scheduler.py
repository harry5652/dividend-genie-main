from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from pytz import timezone

from app.services.alert_service import check_and_send_alerts


scheduler = BackgroundScheduler(timezone=timezone("Asia/Kolkata"))


def start_scheduler():
    """
    Starts APScheduler job for dividend alerts.
    Runs every day at 09:00 AM IST.
    """

    # Remove old jobs if restart happens
    scheduler.remove_all_jobs()
    

    scheduler.add_job(
        func=check_and_send_alerts,
        trigger=CronTrigger(hour=9, minute=0),
        id="dividend_alert_job",
        replace_existing=True,
    )

    scheduler.start()
    print("🔔 APScheduler started: Dividend alerts scheduled at 09:00 AM IST")