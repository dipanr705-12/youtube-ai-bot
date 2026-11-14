"""
API Key Setup Wizard
---------------------
Interactive script to collect and save all API keys to config.yaml.
Run: python setup_keys.py
"""

import yaml
import os
import webbrowser


CONFIG_PATH = "config.yaml"


def main():
    print()
    print("=" * 55)
    print("  YouTube AI Bot - API Key Setup Wizard")
    print("=" * 55)
    print()

    # Load existing config
    with open(CONFIG_PATH, "r") as f:
        config = yaml.safe_load(f)

    # ---- 1. Gemini API Key ----
    print("━" * 55)
    print("1️⃣  GEMINI API KEY (FREE)")
    print("━" * 55)
    print("Used for: Writing video titles, descriptions, tags, scripts")
    print("Get it free: https://aistudio.google.com/app/apikey")
    print()
    key = input("Paste your Gemini API key (or press Enter to skip): ").strip()
    if key:
        config["gemini_api_key"] = key
        print("✅ Gemini key saved!")
    print()

    # ---- 2. Pexels API Key ----
    print("━" * 55)
    print("2️⃣  PEXELS API KEY (FREE)")
    print("━" * 55)
    print("Used for: Downloading free stock video clips")
    print("Get it free: https://www.pexels.com/api/")
    print()
    key = input("Paste your Pexels API key (or press Enter to skip): ").strip()
    if key:
        config["pexels_api_key"] = key
        print("✅ Pexels key saved!")
    print()

    # ---- 3. Pixabay API Key ----
    print("━" * 55)
    print("3️⃣  PIXABAY API KEY (FREE) - Optional fallback")
    print("━" * 55)
    print("Used for: Backup video clip source")
    print("Get it free: https://pixabay.com/api/docs/")
    print()
    key = input("Paste your Pixabay API key (or press Enter to skip): ").strip()
    if key:
        config["pixabay_api_key"] = key
        print("✅ Pixabay key saved!")
    print()

    # ---- 4. Reddit API ----
    print("━" * 55)
    print("4️⃣  REDDIT API (FREE)")
    print("━" * 55)
    print("Used for: Finding trending topics from Reddit")
    print("Get it free: https://www.reddit.com/prefs/apps")
    print("  → Click 'Create app' → Choose 'script' → Copy client ID & secret")
    print()
    cid = input("Reddit Client ID (or Enter to skip): ").strip()
    if cid:
        config["reddit_client_id"] = cid
        secret = input("Reddit Secret: ").strip()
        config["reddit_secret"] = secret
        print("✅ Reddit credentials saved!")
    print()

    # ---- 5. D-ID API Key (Optional, Paid) ----
    print("━" * 55)
    print("5️⃣  D-ID API KEY (OPTIONAL - Paid)")
    print("━" * 55)
    print("Used for: AI-generated talking avatar videos")
    print("Get it: https://www.d-id.com/ (has free trial)")
    print()
    key = input("D-ID API key (or Enter to skip for free stock clips only): ").strip()
    if key:
        config["did_api_key"] = key
        print("✅ D-ID key saved!")
    else:
        print("ℹ️  Skipped. Bot will use free stock clips from Pexels/Pixabay.")
    print()

    # ---- 6. Channel Settings ----
    print("━" * 55)
    print("6️⃣  CHANNEL SETTINGS")
    print("━" * 55)
    name = input(f"Channel name [{config.get('channel_name', 'AI Daily Trends')}]: ").strip()
    if name:
        config["channel_name"] = name
        config["watermark_text"] = f"@{name.replace(' ', '')}"

    time_str = input(f"Upload time (24h format) [{config.get('upload_time', '09:00')}]: ").strip()
    if time_str:
        config["upload_time"] = time_str
    print()

    # ---- Save ----
    with open(CONFIG_PATH, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    print("=" * 55)
    print("✅ All settings saved to config.yaml!")
    print("=" * 55)
    print()
    print("NEXT STEPS:")
    print("  1. Set up YouTube OAuth2:")
    print("     → Go to https://console.cloud.google.com/")
    print("     → Create project → Enable 'YouTube Data API v3'")
    print("     → Create OAuth2 credentials (Desktop App)")
    print("     → Download JSON → save as credentials/client_secret.json")
    print()
    print("  2. Authorize YouTube:")
    print("     run.bat --auth")
    print()
    print("  3. Test the bot:")
    print("     run.bat --now")
    print()
    print("  4. Start the daily scheduler:")
    print("     run.bat")
    print()

    open_browser = input("Open API key pages in browser now? (y/n): ").strip().lower()
    if open_browser == 'y':
        webbrowser.open("https://aistudio.google.com/app/apikey")
        webbrowser.open("https://www.pexels.com/api/")
        webbrowser.open("https://console.cloud.google.com/")


if __name__ == "__main__":
    main()
