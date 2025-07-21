# Golf Directory Python Backend

Python implementation of the refined golf video scheduler with 3 main tasks:

## Features

### 🎯 Refined Tasks (Matches Next.js Logic Exactly)
1. **View Count Updates** (every 2 minutes) - Smart user-facing video selection
2. **Today Collection + AI** (every 30 minutes) - Today's videos + AI analysis  
3. **Daily Maintenance** (3 AM) - Older popular video updates

### 🚀 Key Improvements Over Next.js
- **Native yt-dlp**: Better transcript downloading
- **Mature YouTube API**: google-api-python-client
- **Rich AI ecosystem**: Better Gemini & ElevenLabs integration
- **Robust database**: psycopg2 PostgreSQL integration
- **Better error handling**: More resilient processing

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys and database URL

# Run scheduler
python golf_scheduler.py
```

## Environment Variables

```bash
# Required
DATABASE_URL=postgresql://user:pass@host:port/db
YOUTUBE_API_KEY=your_youtube_api_key
GOOGLE_API_KEY=your_google_api_key

# Optional
ELEVENLABS_API_KEY=your_elevenlabs_key
CRON_SECRET=secure_random_string
```

## Architecture

### Components

- **`golf_scheduler.py`** - Main scheduler with 3 refined tasks
- **`youtube_client.py`** - YouTube API wrapper with exact Next.js logic
- **`ai_processor.py`** - AI generation (Gemini + ElevenLabs)

### Database Operations

- **Smart video selection** - Exact SQL queries from Next.js
- **Quota tracking** - YouTube API usage management
- **Batch processing** - 50 videos per API request
- **AI analysis storage** - Transcript summaries and audio

### AI Processing

- **Transcript download** - yt-dlp with VTT parsing
- **Announcer-style summaries** - Gemini API with exact prompt
- **Audio generation** - ElevenLabs with same voice

## Deployment

### DigitalOcean Setup

```bash
# Install system dependencies
sudo apt update
sudo apt install python3 python3-pip python3-venv postgresql-client ffmpeg

# Install yt-dlp
pip3 install yt-dlp

# Create virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit with your settings

# Run as systemd service
sudo cp golf-scheduler.service /etc/systemd/system/
sudo systemctl enable golf-scheduler
sudo systemctl start golf-scheduler
```

### Systemd Service

Create `/etc/systemd/system/golf-scheduler.service`:

```ini
[Unit]
Description=Golf Directory Scheduler
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/backend
Environment=PATH=/path/to/backend/venv/bin
ExecStart=/path/to/backend/venv/bin/python golf_scheduler.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## Task Details

### 1. View Count Updates (Every 2 Minutes)

- **Smart selection**: Only user-facing videos (curated + video of day candidates)
- **Priority logic**: Whitelisted channels, recent uploads, engagement thresholds
- **Batch processing**: 50 videos per YouTube API call
- **Quota management**: Tracks API usage, respects daily limits

### 2. Today Collection + AI (Every 30 Minutes)

- **Video collection**: Search today's golf videos with content filtering
- **Video of the day**: Momentum-based scoring with heavy recency bias
- **AI generation**: Automatic transcript summary + audio for featured video
- **Database updates**: Channels, videos, AI analyses

### 3. Daily Maintenance (3 AM)

- **Target selection**: Older popular videos (>500K views, >90 days old)
- **Batch updates**: Process up to 100 videos in batches of 50
- **Rate limiting**: Delays between batches to respect API limits

## Monitoring

```bash
# View logs
tail -f golf_scheduler.log

# Check systemd status
sudo systemctl status golf-scheduler

# Monitor database
psql $DATABASE_URL -c "SELECT COUNT(*) FROM youtube_videos;"
```

## Migration from Next.js

This Python backend completely replaces the Next.js scheduler. To migrate:

1. **Stop Next.js scheduler** - Remove scheduler.ts auto-start
2. **Deploy Python backend** - Run on DigitalOcean or similar
3. **Update database** - Same schema, no changes needed
4. **Verify functionality** - Monitor logs and database updates

The Python implementation matches the Next.js logic exactly but with better reliability and performance.