"""
YouTube AI Bot - Main Entry Point
==================================
Autonomous YouTube Shorts uploader:
- Finds daily trending topics
- Sources or generates AI video content
- Edits with music, captions, watermark
- Uploads to YouTube at 9:00 AM IST daily

Usage:
  python main.py           # Start scheduler (runs daily at 9:00 AM)
  python main.py --now     # Run pipeline immediately (test mode)
  python main.py --auth    # Set up YouTube OAuth2
"""

import os
import sys
import logging
import shutil
import argparse
from datetime import datetime
from pathlib import Path

import yaml

# ----------------------------------------------------------------
# Logging Setup
# ----------------------------------------------------------------

def setup_logging(config: dict):
    log_file = config.get("log_file", "logs/daily_log.txt")
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=getattr(logging, config.get("log_level", "INFO")),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout)
        ]
    )

logger = logging.getLogger("main")


# ----------------------------------------------------------------
# Load Config
# ----------------------------------------------------------------

def load_config(path: str = "config.yaml") -> dict:
    if not os.path.exists(path):
        print(f"ERROR: config.yaml not found at {path}")
        sys.exit(1)
    with open(path, "r") as f:
        return yaml.safe_load(f)


# ----------------------------------------------------------------
# Full Pipeline
# ----------------------------------------------------------------

def run_pipeline(config: dict):
    """Run the full automated pipeline: trend -> content -> edit -> upload."""
    logger.info("=" * 60)
    logger.info(f"Pipeline started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)

    # Cleanup previous raw clips
    raw_dir = Path("output/raw_clips")
    if raw_dir.exists():
        shutil.rmtree(raw_dir)
    raw_dir.mkdir(parents=True)

    # STEP 1: Trending topic
    logger.info("STEP 1: Finding trending topic...")
    from modules.trend_finder import get_trending_topic
    topic_data = get_trending_topic(config)
    logger.info(f"Topic: {topic_data['topic']} (via {topic_data['source']})")

    # STEP 2: Generate script
    logger.info("STEP 2: Generating script...")
    from modules.caption_generator import generate_script
    script = generate_script(topic_data, config)
    logger.info(f"Script ({len(script)} chars)")

    # STEP 3: Get video content
    logger.info("STEP 3: Getting video content...")
    from modules.content_generator import get_video_content
    clips = get_video_content(topic_data, script, config)
    if not clips:
        logger.error("No video clips obtained. Pipeline aborted.")
        return False
    logger.info(f"Got {len(clips)} clip(s)")

    # STEP 4: Generate captions
    logger.info("STEP 4: Generating captions...")
    from modules.caption_generator import generate_captions
    captions_path = generate_captions(clips[0], config)

    # STEP 5: Edit video
    logger.info("STEP 5: Editing video...")
    from modules.video_editor import edit_video
    final_video = edit_video(clips, captions_path, topic_data, config)
    if not final_video:
        logger.error("Video editing failed. Pipeline aborted.")
        return False
    logger.info(f"Edited video: {final_video}")

    # STEP 6: Generate metadata
    logger.info("STEP 6: Generating metadata...")
    from modules.metadata_writer import generate_metadata
    metadata = generate_metadata(topic_data, config)
    logger.info(f"Title: {metadata['title']}")

    # STEP 7: Upload
    logger.info("STEP 7: Uploading to YouTube...")
    from modules.youtube_uploader import upload_to_youtube
    video_url = upload_to_youtube(final_video, metadata, config)

    if video_url:
        logger.info(f"SUCCESS! Video live at: {video_url}")
        _log_success(topic_data, metadata, video_url, config)
        return True
    else:
        logger.error("YouTube upload failed.")
        return False


def _log_success(topic_data: dict, metadata: dict, url: str, config: dict):
    summary = f"\n{'='*60}\nDATE: {datetime.now()}\nTOPIC: {topic_data.get('topic')}\nTITLE: {metadata.get('title')}\nURL: {url}\n{'='*60}\n"
    with open(config.get("log_file", "logs/daily_log.txt"), "a") as f:
        f.write(summary)


# ----------------------------------------------------------------
# Entry Point
# ----------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="YouTube AI Bot")
    parser.add_argument("--now", action="store_true", help="Run pipeline immediately")
    parser.add_argument("--auth", action="store_true", help="Set up YouTube OAuth2")
    parser.add_argument("--config", default="config.yaml", help="Config file path")
    args = parser.parse_args()

    config = load_config(args.config)
    setup_logging(config)

    if args.auth:
        from modules.youtube_uploader import authenticate_youtube
        authenticate_youtube(config)
        return

    if args.now:
        logger.info("Running pipeline NOW (test mode)...")
        success = run_pipeline(config)
        sys.exit(0 if success else 1)

    from modules.scheduler import start_scheduler
    start_scheduler(lambda: run_pipeline(config), config)


if __name__ == "__main__":
    main()
