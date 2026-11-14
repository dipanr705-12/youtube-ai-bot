"""
Content Generator Module
------------------------
Two modes:
  1. AI Video (D-ID API) - AI avatar + voiceover
  2. Stock Clip Finder   - Downloads free clips from Pexels/Pixabay

Returns: list of local video clip file paths
"""

import os
import logging
import requests
import time
from pathlib import Path

logger = logging.getLogger(__name__)

RAW_DIR = Path("output/raw_clips")
RAW_DIR.mkdir(parents=True, exist_ok=True)


def get_video_content(topic_data: dict, script: str, config: dict) -> list:
    """
    Master function: tries AI video first, falls back to stock clips.
    Returns list of downloaded clip paths.
    """
    mode = config.get("content_mode", "clip_only")
    clips = []

    if mode == "ai_first":
        # Try D-ID AI avatar video
        clips = _generate_did_video(script, topic_data, config)
        if clips:
            logger.info(f"AI video generated: {clips}")
            return clips
        logger.warning("D-ID AI video failed, falling back to stock clips")

    # Use stock clips from Pixabay (primary) then Pexels (fallback)
    clips = _get_pixabay_clips(topic_data, config)
    if not clips:
        clips = _get_pexels_clips(topic_data, config)

    logger.info(f"Stock clips downloaded: {len(clips)} clips")
    return clips


# ----------------------------------------------------------------
# MODE 1: D-ID AI Avatar Video
# ----------------------------------------------------------------

def _generate_did_video(script: str, topic_data: dict, config: dict) -> list:
    """Generate a talking-head AI video using D-ID API."""
    api_key = config.get("did_api_key", "")
    if not api_key or api_key == "YOUR_DID_API_KEY":
        logger.info("D-ID API key not set, skipping AI video")
        return []

    try:
        headers = {
            "Authorization": f"Basic {api_key}",
            "Content-Type": "application/json"
        }

        # Create a talk video with D-ID
        payload = {
            "script": {
                "type": "text",
                "input": script[:900],  # D-ID character limit
                "provider": {
                    "type": "microsoft",
                    "voice_id": "en-US-JennyNeural"
                }
            },
            "source_url": "https://create-images-results.d-id.com/DefaultPresenters/Emma_f/image.jpeg",
            "config": {"fluent": True, "pad_audio": 0}
        }

        resp = requests.post(
            "https://api.d-id.com/talks",
            headers=headers,
            json=payload,
            timeout=30
        )

        if resp.status_code != 201:
            logger.warning(f"D-ID create failed: {resp.status_code} {resp.text}")
            return []

        talk_id = resp.json().get("id")
        logger.info(f"D-ID talk created: {talk_id}, polling for result...")

        # Poll until ready (max 2 minutes)
        for _ in range(24):
            time.sleep(5)
            status_resp = requests.get(
                f"https://api.d-id.com/talks/{talk_id}",
                headers=headers,
                timeout=15
            )
            data = status_resp.json()
            if data.get("status") == "done":
                video_url = data.get("result_url")
                output_path = RAW_DIR / "ai_video.mp4"
                _download_file(video_url, output_path)
                return [str(output_path)]
            elif data.get("status") == "error":
                logger.error(f"D-ID error: {data}")
                return []

        logger.warning("D-ID timed out")
        return []

    except Exception as e:
        logger.error(f"D-ID exception: {e}")
        return []


# ----------------------------------------------------------------
# MODE 2: Pexels Stock Clips
# ----------------------------------------------------------------

def _get_pexels_clips(topic_data: dict, config: dict) -> list:
    """Search Pexels for free video clips matching the topic."""
    api_key = config.get("pexels_api_key", "")
    if not api_key or api_key == "YOUR_PEXELS_API_KEY":
        logger.warning("Pexels API key not set")
        return []

    topic = topic_data.get("topic", "technology")
    keywords = topic_data.get("keywords", [topic])
    search_query = " ".join(keywords[:3])

    try:
        headers = {"Authorization": api_key}
        params = {
            "query": search_query,
            "per_page": 5,
            "orientation": "portrait",  # Vertical for Shorts
            "size": "medium"
        }
        resp = requests.get(
            "https://api.pexels.com/videos/search",
            headers=headers,
            params=params,
            timeout=15
        )

        if resp.status_code != 200:
            logger.warning(f"Pexels API error: {resp.status_code}")
            return []

        videos = resp.json().get("videos", [])
        clips = []

        for i, video in enumerate(videos[:4]):
            # Pick the HD file
            video_files = video.get("video_files", [])
            hd_file = next(
                (f for f in video_files if f.get("quality") == "hd"),
                video_files[0] if video_files else None
            )
            if hd_file:
                url = hd_file["link"]
                path = RAW_DIR / f"pexels_clip_{i}.mp4"
                if _download_file(url, path):
                    clips.append(str(path))

        return clips

    except Exception as e:
        logger.error(f"Pexels error: {e}")
        return []


# ----------------------------------------------------------------
# MODE 2b: Pixabay Stock Clips (Fallback)
# ----------------------------------------------------------------

def _get_pixabay_clips(topic_data: dict, config: dict) -> list:
    """Fallback: search Pixabay for free video clips."""
    api_key = config.get("pixabay_api_key", "")
    if not api_key or api_key == "YOUR_PIXABAY_API_KEY":
        return []

    topic = topic_data.get("topic", "technology")

    try:
        params = {
            "key": api_key,
            "q": topic,
            "video_type": "film",
            "per_page": 5,
            "lang": "en"
        }
        resp = requests.get(
            "https://pixabay.com/api/videos/",
            params=params,
            timeout=15
        )

        if resp.status_code != 200:
            return []

        hits = resp.json().get("hits", [])
        clips = []

        for i, hit in enumerate(hits[:4]):
            videos = hit.get("videos", {})
            medium = videos.get("medium") or videos.get("small")
            if medium:
                path = RAW_DIR / f"pixabay_clip_{i}.mp4"
                if _download_file(medium["url"], path):
                    clips.append(str(path))

        return clips

    except Exception as e:
        logger.error(f"Pixabay error: {e}")
        return []


# ----------------------------------------------------------------
# Utility
# ----------------------------------------------------------------

def _download_file(url: str, path: Path) -> bool:
    """Download a file from URL to local path."""
    try:
        resp = requests.get(url, stream=True, timeout=60)
        if resp.status_code == 200:
            with open(path, 'wb') as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
            logger.info(f"Downloaded: {path}")
            return True
        logger.warning(f"Download failed ({resp.status_code}): {url}")
        return False
    except Exception as e:
        logger.error(f"Download exception: {e}")
        return False
