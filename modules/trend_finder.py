"""
Trend Finder Module
-------------------
Finds the #1 trending topic for the day using:
1. Google Trends (pytrends)
2. Reddit trending posts
3. YouTube trending videos

Returns the best topic with metadata for video creation.
"""

import logging
import random
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


def get_trending_topic(config: dict) -> dict:
    """
    Master function: tries multiple sources and returns the best trending topic.
    Returns a dict with keys: topic, source, keywords, description
    """
    niche = _pick_niche(config)
    logger.info(f"Searching trends for niche: {niche}")

    topic = None

    # Try Google Trends first
    topic = _get_google_trend(niche)
    if topic:
        logger.info(f"[Google Trends] Topic: {topic['topic']}")
        return topic

    # Fallback: Reddit
    topic = _get_reddit_trend(config, niche)
    if topic:
        logger.info(f"[Reddit] Topic: {topic['topic']}")
        return topic

    # Fallback: YouTube trending
    topic = _get_youtube_trend(niche)
    if topic:
        logger.info(f"[YouTube] Topic: {topic['topic']}")
        return topic

    # Last resort: use a fixed niche keyword
    fallback = {
        "topic": niche,
        "source": "fallback",
        "keywords": [niche],
        "description": f"Today's top content about {niche}"
    }
    logger.warning(f"All trend sources failed. Using fallback: {niche}")
    return fallback


def _pick_niche(config: dict) -> str:
    """Pick today's niche. Rotates through niches daily if config is 'all'."""
    niche = config.get("channel_niche", "all")
    if niche == "all":
        niches = config.get("niches", ["technology"])
        # Rotate by day of year so it's consistent per day
        day_index = datetime.now().timetuple().tm_yday % len(niches)
        return niches[day_index]
    return niche


def _get_google_trend(niche: str) -> Optional[dict]:
    """Get #1 trending topic from Google Trends for the niche."""
    try:
        from pytrends.request import TrendReq
        pytrends = TrendReq(hl='en-US', tz=330)  # IST offset

        # Get trending searches for India
        trending_df = pytrends.trending_searches(pn='india')
        if trending_df is not None and not trending_df.empty:
            top_topic = trending_df.iloc[0][0]
            return {
                "topic": top_topic,
                "source": "google_trends",
                "keywords": [top_topic, niche],
                "description": f"Today's #1 Google trend: {top_topic}"
            }
    except Exception as e:
        logger.warning(f"Google Trends failed: {e}")
    return None


def _get_reddit_trend(config: dict, niche: str) -> Optional[dict]:
    """Get top trending post from Reddit for the niche."""
    try:
        import praw
        reddit = praw.Reddit(
            client_id=config.get("reddit_client_id", ""),
            client_secret=config.get("reddit_secret", ""),
            user_agent=config.get("reddit_user_agent", "YouTubeAIBot/1.0")
        )

        # Map niche to relevant subreddits
        subreddit_map = {
            "AI technology": "artificial+technology+MachineLearning",
            "finance cryptocurrency": "CryptoCurrency+investing+finance",
            "motivation self improvement": "selfimprovement+motivation+getmotivated",
            "sports highlights": "sports+nba+soccer",
            "world news": "worldnews+news",
            "entertainment celebrity": "entertainment+celebrity+movies"
        }
        subreddit_name = subreddit_map.get(niche, "popular")
        subreddit = reddit.subreddit(subreddit_name)

        top_post = next(subreddit.hot(limit=1))
        return {
            "topic": top_post.title[:100],
            "source": "reddit",
            "keywords": [niche] + top_post.title.split()[:5],
            "description": top_post.title
        }
    except Exception as e:
        logger.warning(f"Reddit trend failed: {e}")
    return None


def _get_youtube_trend(niche: str) -> Optional[dict]:
    """Get trending topic from YouTube trending RSS (no auth needed)."""
    try:
        import requests
        url = "https://www.youtube.com/feeds/videos.xml?chart=mostpopular&regionCode=IN"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(resp.text)
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            entries = root.findall('atom:entry', ns)
            if entries:
                title = entries[0].find('atom:title', ns).text
                return {
                    "topic": title,
                    "source": "youtube_trending",
                    "keywords": [niche, title],
                    "description": f"Trending on YouTube: {title}"
                }
    except Exception as e:
        logger.warning(f"YouTube trend failed: {e}")
    return None
