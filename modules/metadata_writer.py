"""
Metadata Writer Module
-----------------------
Uses Google Genai (gemini-2.0-flash) to generate:
- SEO-optimized YouTube title
- Video description with hashtags
- Tags list (15 tags)
"""

import logging
import json
import re

logger = logging.getLogger(__name__)


def generate_metadata(topic_data: dict, config: dict) -> dict:
    """
    Generate title, description, and tags for the YouTube video.
    Returns dict with keys: title, description, tags
    """
    try:
        from google import genai

        client = genai.Client(api_key=config.get("gemini_api_key", ""))

        topic = topic_data.get("topic", "trending topic")
        description_hint = topic_data.get("description", "")
        keywords = topic_data.get("keywords", [topic])

        prompt = f"""You are a YouTube SEO expert. Generate metadata for a YouTube Shorts video.

Topic: {topic}
Context: {description_hint}
Keywords: {', '.join(keywords[:5])}
Video format: YouTube Shorts (vertical, 60 seconds)

Generate EXACTLY this JSON format (no markdown, no extra text):
{{
  "title": "Catchy title under 70 chars with power words and emoji",
  "description": "2-3 sentence description. Include relevant hashtags at the end. #Shorts",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5", "tag6", "tag7", "tag8", "tag9", "tag10", "tag11", "tag12", "tag13", "tag14", "tag15"]
}}

Rules for title:
- Include an emoji
- Use power words: "BREAKING", "VIRAL", "SHOCKING", "YOU NEED TO SEE"
- Under 70 characters
- Include main keyword

Rules for tags:
- Mix of broad and specific tags
- Include: Shorts, viral, trending, [topic keywords]
- All lowercase except proper nouns
"""
        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=prompt
        )
        raw = response.text.strip()

        # Parse JSON from response
        json_match = re.search(r'\{.*\}', raw, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            logger.info(f"Metadata generated: title='{data.get('title', '')[:50]}...'")
            return {
                "title": data.get("title", f"🔥 {topic} | Today's Viral Trend #Shorts"),
                "description": data.get("description", _fallback_description(topic)),
                "tags": data.get("tags", _fallback_tags(topic, keywords))
            }

    except Exception as e:
        logger.warning(f"Genai metadata generation failed: {e}")

    # Fallback
    topic = topic_data.get("topic", "trending")
    keywords = topic_data.get("keywords", [topic])
    return {
        "title": f"🔥 {topic[:60]} #Shorts",
        "description": _fallback_description(topic),
        "tags": _fallback_tags(topic, keywords)
    }


def _fallback_description(topic: str) -> str:
    return (f"Today's most viral trending topic: {topic}! "
            f"Watch daily for the latest trends, news, and viral moments. "
            f"Like, follow and turn on notifications!\n\n"
            f"#Shorts #Trending #Viral #{topic.replace(' ', '')} #DailyTrends #TrendingNow")


def _fallback_tags(topic: str, keywords: list) -> list:
    base_tags = ["shorts", "viral", "trending", "daily trends", "trending now",
                 "viral video", "must watch", "today trending", "new trending"]
    topic_tags = [k.lower().replace(" ", "") for k in keywords[:6]]
    all_tags = list(dict.fromkeys(base_tags + topic_tags + [topic.lower()]))
    return all_tags[:15]
