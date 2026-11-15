"""
Windows Task Scheduler Setup
-----------------------------
Creates a scheduled task that runs the YouTube AI Bot
at the configured time every day, even if no one is logged in.

Run once:  python setup_scheduler.py
Remove:    python setup_scheduler.py --remove
"""

import subprocess
import sys
import os

PYTHON_EXE = r"C:\Users\dipan roy\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
PROJECT_DIR = r"C:\Users\dipan roy\.gemini\antigravity\scratch\youtube-ai-bot"
FFMPEG_BIN = r"C:\Users\dipan roy\.gemini\antigravity\scratch\youtube-ai-bot\ffmpeg\ffmpeg-master-latest-win64-gpl\bin"
TASK_NAME = "YouTubeAIBot_DailyUpload"


def create_task():
    """Create a Windows scheduled task to run the bot daily at 09:00."""
    # Build a one-liner bat command that sets PATH and runs main.py --now
    bat_cmd = (
        f'cmd /c "set PATH={FFMPEG_BIN};%PATH% && '
        f'cd /d {PROJECT_DIR} && '
        f'"{PYTHON_EXE}" main.py --now"'
    )

    # schtasks command
    cmd = [
        "schtasks", "/create",
        "/tn", TASK_NAME,
        "/tr", bat_cmd,
        "/sc", "DAILY",
        "/st", "10:30",         # 10:30 AM
        "/f",                    # Force overwrite if exists
        "/rl", "HIGHEST",        # Run with highest privileges
    ]

    print(f"Creating scheduled task: {TASK_NAME}")
    print(f"Schedule: Daily at 09:00")
    print(f"Command: {bat_cmd[:100]}...")
    print()

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"✅ Scheduled task '{TASK_NAME}' created successfully!")
        print(f"   The bot will run every day at 10:30 AM automatically.")
        print()
        print("To verify: Open Task Scheduler → look for YouTubeAIBot_DailyUpload")
        print("To test now: schtasks /run /tn YouTubeAIBot_DailyUpload")
    else:
        print(f"❌ Failed to create task: {result.stderr}")
        print("Try running this script as Administrator.")


def remove_task():
    """Remove the scheduled task."""
    cmd = ["schtasks", "/delete", "/tn", TASK_NAME, "/f"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"✅ Task '{TASK_NAME}' removed.")
    else:
        print(f"❌ Could not remove task: {result.stderr}")


if __name__ == "__main__":
    if "--remove" in sys.argv:
        remove_task()
    else:
        create_task()
