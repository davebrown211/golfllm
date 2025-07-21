# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a golf video directory application with a Python backend scheduler and Next.js frontend. The system collects, analyzes, and curates golf videos from YouTube using AI-powered content analysis.

### Architecture

- **Backend** (`/backend/`): Python scheduler that collects YouTube videos, analyzes content with AI, and manages the database
- **Frontend** (`/frontend/golf-directory/`): Next.js application that displays curated golf videos with AI-generated summaries and audio

## Common Development Commands

### Frontend (Next.js)
```bash
cd frontend/golf-directory

# Development
npm run dev                    # Start development server on localhost:3000
npm run build                  # Build for production
npm run build:clean           # Clean build (removes .next and cache)
npm run start                  # Start production server
npm run lint                   # Run ESLint

# Database setup
npm run db:setup              # Set up database schema
npm run db:migrate            # Run database migrations
```

### Backend (Python)
```bash
cd backend

# Setup
pip install -r requirements.txt    # Install dependencies
python golf_scheduler.py           # Run the main scheduler

# Database
docker-compose up -d               # Start PostgreSQL and Redis containers
```

## Database Architecture

The application uses PostgreSQL with these core tables:
- `youtube_videos` - Video metadata with view acceleration tracking
- `video_view_history` - Historical view count snapshots
- `video_analyses` - AI-generated transcripts and summaries
- `youtube_channels` - Channel information and whitelisting

Database schema is managed through SQL files in `/frontend/golf-directory/src/lib/migrations/`.

## Key Components

### Backend Scheduler (`golf_scheduler.py`)
Three main tasks running on different intervals:
1. **View Count Updates** (every 2 minutes) - Updates view counts for user-facing videos
2. **Today Collection + AI** (every 30 minutes) - Collects new videos and generates AI content
3. **Daily Maintenance** (3 AM) - Updates older popular videos

### Frontend Architecture
- **App Router** - Next.js 15 with TypeScript
- **Database Layer** - PostgreSQL with direct connections via `pg`
- **AI Integration** - Google Gemini for summaries, ElevenLabs for audio generation
- **Styling** - Tailwind CSS with Radix UI components

## Environment Configuration

Both frontend and backend require environment variables:

**Backend** (`.env`):
- `DATABASE_URL` - PostgreSQL connection string
- `YOUTUBE_API_KEY` - YouTube Data API v3 key
- `GOOGLE_API_KEY` - Google Gemini API key
- `ELEVENLABS_API_KEY` - ElevenLabs API key (optional)

**Frontend** (`.env` and `.env.production`):
- Database and API keys for server-side operations
- Vercel deployment configuration

## Development Workflow

1. **Database**: Start with `docker-compose up -d` for local PostgreSQL
2. **Backend**: Run `python golf_scheduler.py` for video collection
3. **Frontend**: Use `npm run dev` for development server
4. **Testing**: No specific test framework - verify functionality through logs and database inspection

## Content Processing Pipeline

1. **Video Discovery** - Search YouTube for golf content using curated search terms
2. **Content Filtering** - Apply whitelist/blacklist and engagement thresholds
3. **AI Analysis** - Generate transcript summaries using Gemini API
4. **Audio Generation** - Create Jim Nantz-style audio summaries via ElevenLabs
5. **Curation** - Select "Video of the Day" based on momentum scoring

## Deployment

- **Frontend**: Deployed on Vercel with automatic builds
- **Backend**: Runs as systemd service on DigitalOcean droplet
- **Database**: DigitalOcean Managed PostgreSQL

The system is designed to run continuously with the Python backend handling all data collection and the Next.js frontend serving the curated content to users.