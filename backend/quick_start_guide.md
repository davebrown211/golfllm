# Quick Start Guide - Golf YouTube Directory

## 🚀 Start Collecting Data

### Option 1: Quick Start (Recommended)
```bash
# First, enable YouTube Data API v3 in Google Cloud Console
# Visit: https://console.cloud.google.com/apis/library/youtube.googleapis.com

# Then run:
./start_collecting.sh
# Choose option 1 for initial collection
```

### Option 2: Manual Collection
```bash
# One-time collection
python -m youtube_analyzer.app.data_collector

# Continuous collection (every 6 hours)
python -m youtube_analyzer.app.data_collector --schedule
```

### Option 3: Using Cron (Production)
```bash
# Add to crontab for automatic daily updates
crontab -e

# Add these lines:
0 2 * * * cd /Users/dbrown/golfllm && python -m youtube_analyzer.app.data_collector >> logs/collection.log 2>&1
0 */6 * * * cd /Users/dbrown/golfllm && python -c "from youtube_analyzer.app.data_collector import GolfDataCollector; GolfDataCollector().collect_trending_videos()" >> logs/trending.log 2>&1
```

## 📊 What Gets Collected

1. **Trending Videos** (Every 6 hours)
   - Latest golf videos with high view counts
   - Videos from the past week

2. **Top Channel Updates** (Daily)
   - New videos from major golf channels
   - Rick Shiels, Good Good, GM Golf, etc.

3. **Category Collection** (Daily)
   - Instruction videos
   - Equipment reviews
   - Tournament highlights

4. **Stats Updates** (Daily)
   - View counts, likes, comments
   - Engagement rates

## 📈 Monitor Progress

```bash
# View collection stats
cat collection_stats.json

# Watch logs in real-time
tail -f data_collection.log

# Check database size
sqlite3 golf_directory.db "SELECT COUNT(*) FROM youtube_videos;"
```

## 🔧 API Quota Management

- **Daily Limit**: 10,000 units
- **Search**: 100 units per request
- **Video Details**: 1 unit per video
- **Expected Usage**: ~2,000-3,000 units/day

The collector automatically stops before hitting quota limits.

## 🌐 View Your Data

```bash
# Start the API server
uvicorn youtube_analyzer.app.directory_api:app --reload

# Visit in browser
# http://localhost:8000/docs - API documentation
# http://localhost:8000/rankings/daily_trending - Today's trending
# http://localhost:8000/channels/top - Top channels
# http://localhost:8000/stats - Collection statistics
```

## 💡 Collection Strategy

The system collects data efficiently:

1. **High-Value Content First**: Focuses on trending and popular videos
2. **Channel Tracking**: Monitors top golf YouTubers
3. **Category Balance**: Ensures diverse content types
4. **Smart Updates**: Only refreshes stale data

## 🛠️ Troubleshooting

**"API not enabled" error**: 
- Enable YouTube Data API v3 in Google Cloud Console
- Wait 5 minutes for activation

**"Quota exceeded" error**:
- Wait until midnight PST for quota reset
- Reduce collection frequency

**No data appearing**:
- Check data_collection.log for errors
- Ensure GOOGLE_API_KEY is in .env file
- Verify API key has YouTube access

## 📅 Recommended Schedule

- **Initial Setup**: Run full collection once
- **Daily**: Automatic updates at 2 AM
- **Throughout Day**: Trending updates every 6 hours
- **Weekly**: Review and adjust tracked channels