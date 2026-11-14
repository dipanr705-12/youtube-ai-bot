"""
YouTube Uploader Module
-----------------------
Uploads video to YouTube using the YouTube Data API v3.
Handles:
- OAuth2 authentication (first-time setup)
- Token refresh (automatic)
- Video upload with metadata
- Shorts category detection
"""

import os
import logging
import pickle
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def upload_to_youtube(video_path: str, metadata: dict, config: dict) -> Optional[str]:
    """
    Upload video to YouTube.
    Returns the YouTube video URL on success, None on failure.
    """
    try:
        youtube = _get_youtube_client(config)
        if not youtube:
            logger.error("YouTube client initialization failed")
            return None

        logger.info(f"Uploading: {video_path}")
        logger.info(f"Title: {metadata.get('title', '')}")

        from googleapiclient.http import MediaFileUpload

        # Prepare video body
        body = {
            "snippet": {
                "title": metadata.get("title", "Trending Now #Shorts")[:100],
                "description": metadata.get("description", "")[:5000],
                "tags": metadata.get("tags", [])[:500],  # YouTube tag limit
                "categoryId": "25",  # News & Politics (generic)
                "defaultLanguage": "en",
                "defaultAudioLanguage": "en"
            },
            "status": {
                "privacyStatus": "public",    # "public", "unlisted", "private"
                "selfDeclaredMadeForKids": False,
                "madeForKids": False
            }
        }

        # Media upload (resumable for reliability)
        media = MediaFileUpload(
            video_path,
            mimetype="video/mp4",
            resumable=True,
            chunksize=1024 * 1024 * 5  # 5MB chunks
        )

        request = youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media
        )

        # Execute upload with progress
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                progress = int(status.progress() * 100)
                logger.info(f"Upload progress: {progress}%")

        video_id = response.get("id", "")
        video_url = f"https://www.youtube.com/shorts/{video_id}"
        logger.info(f"✅ Video uploaded successfully: {video_url}")
        return video_url

    except Exception as e:
        logger.error(f"YouTube upload failed: {e}")
        return None


def _get_youtube_client(config: dict):
    """
    Get authenticated YouTube API client.
    Handles OAuth2 flow with token caching.
    """
    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build

        creds_file = config.get("youtube_credentials", "credentials/client_secret.json")
        token_file = config.get("youtube_token", "credentials/token.json")
        creds = None

        # Load existing token
        if os.path.exists(token_file):
            creds = Credentials.from_authorized_user_file(token_file, SCOPES)

        # Refresh or re-authenticate
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                logger.info("YouTube token refreshed")
            else:
                if not os.path.exists(creds_file):
                    logger.error(f"YouTube credentials file not found: {creds_file}")
                    logger.error("Run: python main.py --auth  to set up YouTube OAuth2")
                    return None
                flow = InstalledAppFlow.from_client_secrets_file(creds_file, SCOPES)
                creds = flow.run_local_server(port=0)
                logger.info("YouTube OAuth2 authorized!")

            # Save token for next time
            Path(token_file).parent.mkdir(parents=True, exist_ok=True)
            with open(token_file, "w") as f:
                f.write(creds.to_json())

        return build("youtube", "v3", credentials=creds)

    except Exception as e:
        logger.error(f"YouTube client error: {e}")
        return None


def authenticate_youtube(config: dict):
    """
    Run this once interactively to authorize the YouTube account.
    Call: python main.py --auth
    """
    print("\n" + "="*50)
    print("YouTube OAuth2 Setup")
    print("="*50)
    print("1. Go to: https://console.cloud.google.com/")
    print("2. Create a project → Enable 'YouTube Data API v3'")
    print("3. Create OAuth2 credentials → Download as JSON")
    print(f"4. Save the JSON file as: {config.get('youtube_credentials')}")
    print("="*50)
    input("Press Enter once you've saved the credentials file...")
    client = _get_youtube_client(config)
    if client:
        print("✅ YouTube authorization successful! Token saved.")
        print("You can now run: python main.py --daemon")
    else:
        print("❌ Authorization failed. Check the credentials file.")
