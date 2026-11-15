"""
Scheduler Module
----------------
Runs the full pipeline once a day at the configured time.
Can run as a persistent daemon or via Windows Task Scheduler.
"""

import logging
import time
from datetime import datetime

logger = logging.getLogger(__name__)


def start_scheduler(run_pipeline_fn, config: dict):
    """
    Block and run run_pipeline_fn every day at upload_time.
    upload_time format: "HH:MM" in 24h (e.g. "10:30")
    """
    upload_time = config.get("upload_time", "10:30")
    logger.info(f"Scheduler started. Daily upload at {upload_time} IST")
    print(f"\n✅ Scheduler running. Will upload daily at {upload_time} IST")
    print("Press Ctrl+C to stop.\n")

    try:
        import schedule
        schedule.every().day.at(upload_time).do(run_pipeline_fn)

        while True:
            schedule.run_pending()
            # Show next run time periodically
            next_run = schedule.next_run()
            if next_run:
                now = datetime.now()
                wait = (next_run - now).total_seconds()
                if int(wait) % 3600 == 0:  # Log every hour
                    logger.info(f"Next upload in {wait/3600:.1f} hours ({next_run.strftime('%Y-%m-%d %H:%M')})")
            time.sleep(30)

    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user (Ctrl+C)")
        print("\nScheduler stopped.")
    except ImportError:
        logger.warning("'schedule' package not found, using basic sleep loop")
        _basic_scheduler(run_pipeline_fn, upload_time)


def _basic_scheduler(run_pipeline_fn, upload_time: str):
    """Fallback scheduler without the 'schedule' package."""
    target_hour, target_minute = map(int, upload_time.split(":"))
    logger.info(f"Basic scheduler: will run at {upload_time} daily")

    while True:
        now = datetime.now()
        if now.hour == target_hour and now.minute == target_minute:
            logger.info("Trigger time reached, running pipeline...")
            run_pipeline_fn()
            time.sleep(61)  # Avoid double-trigger within same minute
        time.sleep(30)
