# 🤖 YouTube AI Bot — Fully Autonomous YouTube Shorts Uploader

Automatically finds trending topics, downloads video clips, edits them into YouTube Shorts, and uploads to your channel — every day at a fixed time with **zero manual work**.

## 🔥 What It Does

Every day at 9:00 AM (configurable):
1. 🔍 Finds today's trending topic (Google Trends / YouTube)
2. 📥 Downloads relevant video clips (Pixabay API)
3. ✂️ Edits clips into a vertical YouTube Short (1080x1920)
4. 💬 Adds watermark, title overlay
5. 📝 AI generates SEO title, description & tags (Gemini AI)
6. 📤 Uploads automatically to YouTube via API
7. 😴 Sleeps until tomorrow

## 📦 Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Install FFmpeg
Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH.

### 3. Get API Keys (all FREE)
- **Gemini AI**: [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
- **Pixabay**: [pixabay.com/api/docs](https://pixabay.com/api/docs/)
- **YouTube Data API v3**: [Google Cloud Console](https://console.cloud.google.com/)

### 4. Configure
Copy `config.example.yaml` to `config.yaml` and fill in your API keys.

### 5. Authorize YouTube
```bash
python main.py --auth
```

### 6. Run
```bash
python main.py          # Start daily scheduler
python main.py --now    # Run once immediately (test)
```

## 📁 Project Structure

```
├── main.py                  # Entry point
├── config.yaml              # Your API keys (not tracked by git)
├── modules/
│   ├── trend_finder.py      # Google Trends + YouTube trending
│   ├── content_generator.py # Pixabay clips / D-ID AI video
│   ├── video_editor.py      # MoviePy + FFmpeg
│   ├── caption_generator.py # Whisper AI + Gemini scripts
│   ├── metadata_writer.py   # AI-generated titles/tags
│   ├── youtube_uploader.py  # YouTube Data API v3
│   └── scheduler.py         # Daily trigger
├── credentials/             # OAuth2 tokens (not tracked)
├── output/                  # Generated videos
└── assets/                  # Intro/outro, music
```

## ⚠️ Important Notes
- Keep uploads to **1 video/day** to avoid YouTube strikes
- Use **royalty-free** clips only (Pixabay is safe)
- Your `config.yaml` and `credentials/` folder contain secrets — never share them

## 🛠 Built With
- Python 3.12+
- MoviePy + FFmpeg
- Google Gemini AI
- YouTube Data API v3
- Pixabay API

## 📄 License
MIT License — use freely!
