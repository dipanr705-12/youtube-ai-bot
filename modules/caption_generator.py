"""
Caption Generator Module
------------------------
Uses OpenAI Whisper (local, free) to:
1. Transcribe video audio -> .srt subtitles

Also generates AI voiceover scripts using Google Genai.
"""

import os
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

CAPTIONS_DIR = Path("output")
CAPTIONS_DIR.mkdir(parents=True, exist_ok=True)


def generate_captions(video_path: str, config: dict) -> Optional[str]:
    """
    Transcribe video audio → .srt subtitle file.
    Returns path to .srt file, or None on failure.
    """
    # Try faster-whisper first (lighter, CPU-friendly)
    result = _try_faster_whisper(video_path)
    if result:
        return result

    # Try openai-whisper
    result = _try_openai_whisper(video_path)
    if result:
        return result

    logger.warning("All whisper engines failed. Proceeding without captions.")
    return None


def _try_openai_whisper(video_path: str) -> Optional[str]:
    try:
        import whisper
        logger.info("Loading Whisper model (base)...")
        model = whisper.load_model("base")
        result = model.transcribe(video_path, language="en")
        srt_path = str(CAPTIONS_DIR / "captions.srt")
        _write_srt(result["segments"], srt_path)
        logger.info(f"Captions (whisper): {srt_path}")
        return srt_path
    except ImportError:
        logger.info("openai-whisper not available")
    except Exception as e:
        logger.warning(f"Whisper failed: {e}")
    return None


def _try_faster_whisper(video_path: str) -> Optional[str]:
    try:
        from faster_whisper import WhisperModel
        logger.info("Loading faster-whisper (base, CPU)...")
        model = WhisperModel("base", device="cpu", compute_type="int8")
        segments, _ = model.transcribe(video_path, language="en")
        seg_list = [{"start": s.start, "end": s.end, "text": s.text} for s in segments]
        srt_path = str(CAPTIONS_DIR / "captions.srt")
        _write_srt(seg_list, srt_path)
        logger.info(f"Captions (faster-whisper): {srt_path}")
        return srt_path
    except ImportError:
        logger.info("faster-whisper not available")
    except Exception as e:
        logger.warning(f"faster-whisper failed: {e}")
    return None


def _write_srt(segments: list, output_path: str):
    with open(output_path, "w", encoding="utf-8") as f:
        for i, seg in enumerate(segments, 1):
            start = _format_time(seg["start"])
            end = _format_time(seg["end"])
            text = seg["text"].strip()
            f.write(f"{i}\n{start} --> {end}\n{text}\n\n")


def _format_time(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"


def generate_script(topic_data: dict, config: dict) -> str:
    """
    Use Google Genai to write a voiceover script for the video.
    """
    try:
        from google import genai

        client = genai.Client(api_key=config.get("gemini_api_key", ""))

        topic = topic_data.get("topic", "today's trending topic")

        prompt = f"""Write a short, engaging 50-second YouTube Shorts voiceover script about: "{topic}"

Requirements:
- Conversational and energetic tone
- Start with a hook (attention-grabbing first sentence)
- Include 3-4 key facts or points
- End with a call to action ("Follow for daily updates!")
- Maximum 120 words
- NO stage directions, just the spoken words

Topic context: {topic_data.get('description', '')}
"""
        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=prompt
        )
        script = response.text.strip()
        logger.info(f"Script generated ({len(script)} chars)")
        return script

    except Exception as e:
        logger.warning(f"Script generation failed: {e}")
        topic = topic_data.get("topic", "trending topic")
        return (f"You won't believe what's trending today! "
                f"Everyone is talking about {topic}. "
                f"Here's everything you need to know. "
                f"This is huge news that's going viral right now. "
                f"Follow our channel for daily trending updates!")
