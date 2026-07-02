import logging
from app.bot.app import create_app
from app.config import config
from app.database.engine import Base, engine
from app.database.session import get_session

logging.basicConfig(level=logging.INFO)

def main():

    # DB init
    Base.metadata.create_all(bind=engine)

    app = create_app()

    logging.info("Starting webhook bot...")

    app.run_webhook(
        listen="0.0.0.0",
        port=config.PORT,
        url_path=config.TELEGRAM_BOT_TOKEN,
        webhook_url=f"{config.WEBHOOK_URL}/{config.TELEGRAM_BOT_TOKEN}",
        drop_pending_updates=True,
    )

if __name__ == "__main__":
    main()