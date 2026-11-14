"""
Video Editor Module (MoviePy v2 Compatible)
--------------------------------------------
Takes video clips and:
1. Trims, resizes to 1080x1920 (Shorts vertical)
2. Concatenates clips
3. Adds background music
4. Burns captions via FFmpeg
5. Adds watermark via FFmpeg

Requires: moviepy v2+, ffmpeg (in PATH)
"""

import os
import logging
import random
import subprocess
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

OUTPUT_DIR = Path("output/edited_videos")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def edit_video(clips: list, captions_path: Optional[str], topic_data: dict, config: dict) -> Optional[str]:
    """
    Master editor: merge clips, add music, watermark, and captions.
    Returns path to final video file.
    """
    if not clips:
        logger.error("No clips provided to editor")
        return None

    try:
        from moviepy import VideoFileClip, AudioFileClip, concatenate_videoclips, CompositeVideoClip, TextClip

        target_duration = config.get("video_length_seconds", 58)
        resolution = tuple(config.get("video_resolution", [1080, 1920]))
        fps = config.get("fps", 30)

        # --- Step 1: Load & process clips ---
        processed_clips = []
        per_clip_duration = target_duration / min(len(clips), 5)

        for clip_path in clips[:5]:
            try:
                clip = VideoFileClip(clip_path)
                duration = min(per_clip_duration, clip.duration)
                clip = clip.subclipped(0, duration)
                clip = _resize_to_vertical(clip, resolution)
                processed_clips.append(clip)
                logger.info(f"Processed clip: {clip_path} ({duration:.1f}s)")
            except Exception as e:
                logger.warning(f"Skipping clip {clip_path}: {e}")

        if not processed_clips:
            logger.error("No clips could be processed")
            return None

        # --- Step 2: Concatenate ---
        final = concatenate_videoclips(processed_clips)
        if final.duration > target_duration:
            final = final.subclipped(0, target_duration)

        # --- Step 3: Add background music ---
        music_path = _pick_background_music()
        if music_path:
            try:
                music = AudioFileClip(music_path)
                music = music.with_volume_scaled(config.get("audio_volume", 0.3))
                if music.duration < final.duration:
                    music = music.with_effects([lambda c: c.loop(duration=final.duration)])
                else:
                    music = music.subclipped(0, final.duration)
                if final.audio:
                    from moviepy import CompositeAudioClip
                    final = final.with_audio(CompositeAudioClip([final.audio, music]))
                else:
                    final = final.with_audio(music)
                logger.info("Background music added")
            except Exception as e:
                logger.warning(f"Music failed (continuing without): {e}")

        # --- Step 4: Export base video ---
        timestamp = _today_str()
        base_output = OUTPUT_DIR / f"base_{timestamp}.mp4"
        final.write_videofile(
            str(base_output), fps=fps, codec="libx264",
            audio_codec="aac", logger=None
        )

        for c in processed_clips:
            c.close()
        final.close()

        # --- Step 5: Add watermark + captions with FFmpeg ---
        final_output = OUTPUT_DIR / f"final_short_{timestamp}.mp4"
        _ffmpeg_post_process(str(base_output), str(final_output), captions_path, topic_data, config)

        # Cleanup base
        if os.path.exists(str(final_output)):
            os.remove(str(base_output))
            logger.info(f"Final video: {final_output}")
            return str(final_output)
        else:
            logger.info(f"FFmpeg post failed, using base: {base_output}")
            return str(base_output)

    except Exception as e:
        logger.error(f"Video editing failed: {e}", exc_info=True)
        # Try pure FFmpeg fallback
        return _ffmpeg_only_edit(clips, captions_path, topic_data, config)


def _resize_to_vertical(clip, resolution: tuple):
    """Resize and crop clip to vertical resolution."""
    target_w, target_h = resolution
    clip_ratio = clip.w / clip.h
    target_ratio = target_w / target_h

    if clip_ratio > target_ratio:
        new_h = target_h
        new_w = int(clip.w * target_h / clip.h)
        clip = clip.resized((new_w, new_h))
        x_center = (new_w - target_w) // 2
        clip = clip.cropped(x1=x_center, y1=0, x2=x_center + target_w, y2=target_h)
    else:
        new_w = target_w
        new_h = int(clip.h * target_w / clip.w)
        clip = clip.resized((new_w, new_h))
        y_center = (new_h - target_h) // 2
        clip = clip.cropped(x1=0, y1=y_center, x2=target_w, y2=y_center + target_h)
    return clip


def _pick_background_music() -> Optional[str]:
    music_dir = Path("assets/background_music")
    music_files = list(music_dir.glob("*.mp3")) + list(music_dir.glob("*.wav"))
    return str(random.choice(music_files)) if music_files else None


def _ffmpeg_post_process(input_path: str, output_path: str, srt_path: Optional[str], topic_data: dict, config: dict):
    """Use FFmpeg to add watermark text and burn subtitles."""
    watermark = config.get("watermark_text", "@AIDailyTrends")
    font_size = config.get("caption_font_size", 55)

    # Build filter chain
    filters = []
    # Watermark at top-right
    filters.append(f"drawtext=text='{watermark}':fontsize=28:fontcolor=white:borderw=1:bordercolor=black:x=w-tw-10:y=10")

    # Topic title for first 3 seconds
    topic_text = topic_data.get("topic", "")[:60].replace("'", "")
    if topic_text:
        filters.append(f"drawtext=text='{topic_text}':fontsize=42:fontcolor=yellow:borderw=2:bordercolor=black:x=(w-tw)/2:y=h*0.15:enable='lt(t,3)'")

    # Subtitles
    if srt_path and os.path.exists(srt_path):
        srt_escaped = srt_path.replace("\\", "/").replace(":", "\\:")
        filters.append(f"subtitles='{srt_escaped}':force_style='Fontsize={font_size},PrimaryColour=&HFFFFFF,OutlineColour=&H000000,Outline=2,Bold=1'")

    vf = ",".join(filters)
    cmd = ["ffmpeg", "-i", input_path, "-vf", vf, "-c:a", "copy", "-y", output_path]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        logger.warning(f"FFmpeg post-process failed: {result.stderr[-200:]}")
        # Try without subtitles
        filters_no_subs = [f for f in filters if "subtitles" not in f]
        if filters_no_subs:
            vf2 = ",".join(filters_no_subs)
            cmd2 = ["ffmpeg", "-i", input_path, "-vf", vf2, "-c:a", "copy", "-y", output_path]
            subprocess.run(cmd2, capture_output=True, text=True, timeout=120)
    else:
        logger.info("FFmpeg post-processing complete (watermark + captions)")


def _ffmpeg_only_edit(clips: list, captions_path: Optional[str], topic_data: dict, config: dict) -> Optional[str]:
    """Pure FFmpeg fallback if MoviePy fails entirely."""
    if not clips:
        return None

    logger.info("Using pure FFmpeg fallback editor")
    timestamp = _today_str()
    target_duration = config.get("video_length_seconds", 58)

    # If single clip, just trim and resize
    output_path = str(OUTPUT_DIR / f"final_short_{timestamp}.mp4")
    input_clip = clips[0]

    cmd = [
        "ffmpeg", "-i", input_clip,
        "-t", str(target_duration),
        "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2",
        "-c:v", "libx264", "-preset", "fast",
        "-c:a", "aac",
        "-y", output_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    if result.returncode == 0 and os.path.exists(output_path):
        logger.info(f"FFmpeg fallback video: {output_path}")
        return output_path

    logger.error("FFmpeg fallback also failed")
    return None


def _today_str() -> str:
    from datetime import datetime
    return datetime.now().strftime("%Y%m%d_%H%M%S")
