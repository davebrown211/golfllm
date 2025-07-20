#!/bin/bash

echo "=== HISTORICAL GOLF DATA COLLECTION ==="
echo
echo "This will collect comprehensive historical data from golf channels"
echo

# Check environment
if [ ! -f .env ]; then
    echo "❌ No .env file found"
    exit 1
fi

export $(cat .env | xargs)

if [ -z "$GOOGLE_API_KEY" ]; then
    echo "❌ No GOOGLE_API_KEY found in .env"
    exit 1
fi

echo "Choose collection level:"
echo "1) Light collection (~1000 videos, ~20% quota)"
echo "2) Medium collection (~2500 videos, ~50% quota)" 
echo "3) Heavy collection (~5000 videos, ~80% quota)"
echo "4) Maximum collection (~8000 videos, ~90% quota)"
echo "5) Custom channel collection (specify channel)"
echo "6) Discovery only (find new channels)"

read -p "Enter choice (1-6): " choice

case $choice in
    1)
        echo "Starting light historical collection..."
        python -c "
from youtube_analyzer.app.historical_collector import HistoricalCollector
collector = HistoricalCollector()
collector.daily_quota_limit = 2000  # Light collection
priority_list = collector.get_collection_priority_list()
print('Top 5 priority channels:')
for i, ch in enumerate(priority_list[:5], 1):
    print(f'{i}. {ch[\"title\"]} - {ch[\"current_videos\"]} videos')
total = 0
for channel in priority_list[:8]:
    collected = collector.collect_channel_deep_dive(channel['channel_id'], target_videos=25)
    total += collected
    if collector.api_quota_used >= collector.daily_quota_limit:
        break
collector.directory.update_rankings()
print(f'Light collection complete: {total} videos')
"
        ;;
    2)
        echo "Starting medium historical collection..."
        python -c "
from youtube_analyzer.app.historical_collector import HistoricalCollector
collector = HistoricalCollector()
collector.daily_quota_limit = 5000  # Medium collection
total = collector.run_comprehensive_collection()
print(f'Medium collection complete: {total} videos')
"
        ;;
    3)
        echo "Starting heavy historical collection..."
        python -c "
from youtube_analyzer.app.historical_collector import HistoricalCollector
collector = HistoricalCollector()
collector.daily_quota_limit = 8000  # Heavy collection
total = collector.run_comprehensive_collection()
print(f'Heavy collection complete: {total} videos')
"
        ;;
    4)
        echo "Starting maximum historical collection..."
        echo "This will use most of your daily quota. Continue? (y/n)"
        read -p "> " confirm
        if [ "$confirm" = "y" ]; then
            python -m youtube_analyzer.app.historical_collector
        fi
        ;;
    5)
        echo "Enter YouTube channel ID (e.g., UCq-Rqdgna3OJxPg3aBt3c3Q):"
        read -p "> " channel_id
        echo "Enter number of videos to collect (e.g., 50):"
        read -p "> " num_videos
        python -c "
from youtube_analyzer.app.historical_collector import HistoricalCollector
collector = HistoricalCollector()
collected = collector.collect_channel_deep_dive('$channel_id', target_videos=$num_videos)
print(f'Collected {collected} videos from specified channel')
"
        ;;
    6)
        echo "Starting discovery-only collection..."
        python -c "
from youtube_analyzer.app.historical_collector import HistoricalCollector
collector = HistoricalCollector()
discovered = collector.discover_and_collect_similar_channels()
print(f'Discovery complete: found {len(discovered)} new channels')
for channel_id, name in discovered[:10]:
    print(f'  • {name}')
"
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo
echo "Collection complete! Check results with:"
echo "  python check_collected_data.py"
echo
echo "Start API server to view data:"
echo "  uvicorn youtube_analyzer.app.directory_api:app --reload"