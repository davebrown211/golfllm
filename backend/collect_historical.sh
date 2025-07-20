#!/bin/bash

echo "=== GOLF YOUTUBE HISTORICAL DATA COLLECTION ==="
echo
echo "This will collect historical data from major golf channels"
echo "and set up trending detection."
echo

# Check environment
if [ ! -f .env ]; then
    echo "❌ No .env file found"
    exit 1
fi

export $(cat .env | xargs)

echo "Choose collection type:"
echo "1) Quick collection (top 10 channels, ~1000 videos)"
echo "2) Full historical collection (30+ channels, ~3000 videos)"
echo "3) Trending only (last 48 hours)"
echo "4) Check current trending"

read -p "Enter choice (1-4): " choice

case $choice in
    1)
        echo "Starting quick collection..."
        python -c "
from youtube_analyzer.app.expanded_collector import ExpandedGolfCollector
c = ExpandedGolfCollector()
# Collect from top channels only
channels = {
    'UCq-Rqdgna3OJxPg3aBt3c3Q': 'Rick Shiels Golf',
    'UCfi-mPMOmche6WI-jkvnGXw': 'Good Good',
    'UC9ywmLLYtiWKC0nHPWA_53g': 'GM Golf',
    'UCgUueMmSpcl-aCTt5CuCKQw': 'Grant Horvat Golf',
    'UCVZMKsVxmgYpgtfcbkq1mZg': 'Peter Finch Golf'
}
for channel_id, name in channels.items():
    print(f'Collecting from {name}...')
    c.collect_historical_channel_data(channel_id, max_videos=20)
c.directory.update_rankings()
print('Quick collection complete!')
"
        ;;
    2)
        echo "Starting full historical collection..."
        echo "This will use significant API quota. Continue? (y/n)"
        read -p "> " confirm
        if [ "$confirm" = "y" ]; then
            python -m youtube_analyzer.app.expanded_collector
        fi
        ;;
    3)
        echo "Collecting trending content..."
        python -c "
from youtube_analyzer.app.trending_detector import TrendingDetector
detector = TrendingDetector()
detector.monitor_real_time()
print('Trending collection complete!')
"
        ;;
    4)
        echo "Checking current trending..."
        python -m youtube_analyzer.app.trending_detector
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo
echo "To view collected data:"
echo "  python check_collected_data.py"
echo
echo "To start API server:"
echo "  uvicorn youtube_analyzer.app.directory_api:app --reload"