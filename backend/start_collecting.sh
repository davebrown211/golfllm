#!/bin/bash

echo "=== GOLF YOUTUBE DATA COLLECTION SETUP ==="
echo

# Check if .env file exists
if [ -f .env ]; then
    echo "✓ .env file found"
    export $(cat .env | xargs)
else
    echo "✗ .env file not found"
    echo "Please create .env file with GOOGLE_API_KEY"
    exit 1
fi

# Check if API key is set
if [ -z "$GOOGLE_API_KEY" ]; then
    echo "✗ GOOGLE_API_KEY not set in .env"
    exit 1
else
    echo "✓ GOOGLE_API_KEY found"
fi

# Create logs directory
mkdir -p logs

echo
echo "Choose an option:"
echo "1) Run initial data collection (recommended for first time)"
echo "2) Start scheduled collection (runs continuously)"
echo "3) Run one-time update"
echo "4) View collection stats"

read -p "Enter your choice (1-4): " choice

case $choice in
    1)
        echo "Starting initial data collection..."
        python -m youtube_analyzer.app.data_collector
        ;;
    2)
        echo "Starting scheduled collection (runs every 6 hours)..."
        echo "Press Ctrl+C to stop"
        python -m youtube_analyzer.app.data_collector --schedule
        ;;
    3)
        echo "Running one-time update..."
        python -c "from youtube_analyzer.app.data_collector import GolfDataCollector; GolfDataCollector().run_daily_collection()"
        ;;
    4)
        if [ -f collection_stats.json ]; then
            echo "=== COLLECTION STATS ==="
            cat collection_stats.json
        else
            echo "No stats found. Run collection first."
        fi
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac