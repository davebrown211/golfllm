#!/usr/bin/env python3
"""
Demo the Golf Directory with mock data that simulates real YouTube results.
This shows what the directory would look like with actual YouTube data.
"""

import json
from datetime import datetime

# Mock data that represents what we'd get from YouTube API
MOCK_RESULTS = {
    "daily_trending": [
        {
            "rank": 1,
            "title": "I Played With Tiger Woods at Augusta National!",
            "channel": "Good Good",
            "views": "2,847,392",
            "likes": "187,294",
            "engagement": "6.84%",
            "published": "2025-07-04",
            "url": "https://youtube.com/watch?v=abc123",
            "thumbnail": "https://i.ytimg.com/vi/abc123/maxresdefault.jpg"
        },
        {
            "rank": 2,
            "title": "Testing the NEW TaylorMade Qi10 Driver",
            "channel": "Rick Shiels Golf",
            "views": "892,471",
            "likes": "42,847",
            "engagement": "5.02%",
            "published": "2025-07-03",
            "url": "https://youtube.com/watch?v=def456",
            "thumbnail": "https://i.ytimg.com/vi/def456/maxresdefault.jpg"
        },
        {
            "rank": 3,
            "title": "How to Break 80 - Course Management Secrets",
            "channel": "Golf Sidekick",
            "views": "423,891",
            "likes": "28,947",
            "engagement": "7.12%",
            "published": "2025-07-04",
            "url": "https://youtube.com/watch?v=ghi789",
            "thumbnail": "https://i.ytimg.com/vi/ghi789/maxresdefault.jpg"
        }
    ],
    "top_channels": [
        {
            "channel": "Rick Shiels Golf",
            "videos_tracked": 47,
            "total_views": "127,394,821",
            "avg_engagement": "5.83%",
            "url": "https://youtube.com/channel/UCg123"
        },
        {
            "channel": "Good Good",
            "videos_tracked": 38,
            "total_views": "98,472,193",
            "avg_engagement": "6.94%",
            "url": "https://youtube.com/channel/UCg456"
        },
        {
            "channel": "TXG - Tour Experience Golf",
            "videos_tracked": 52,
            "total_views": "84,729,481",
            "avg_engagement": "4.27%",
            "url": "https://youtube.com/channel/UCg789"
        }
    ],
    "categories": {
        "instruction": 234,
        "equipment": 189,
        "vlogs": 312,
        "tour": 98,
        "highlights": 143
    }
}

def display_mock_directory():
    print("=== GOLF YOUTUBE DIRECTORY (MOCK DATA DEMO) ===\n")
    print("This demonstrates what your directory would look like with real YouTube data.\n")
    
    print("📊 DAILY TRENDING GOLF VIDEOS")
    print("━" * 60)
    for video in MOCK_RESULTS["daily_trending"]:
        print(f"\n{video['rank']}. {video['title']}")
        print(f"   📺 {video['channel']} • {video['views']} views")
        print(f"   👍 {video['likes']} likes • {video['engagement']} engagement")
        print(f"   📅 Published: {video['published']}")
        print(f"   🔗 {video['url']}")
    
    print("\n\n🏆 TOP GOLF CHANNELS")
    print("━" * 60)
    for channel in MOCK_RESULTS["top_channels"]:
        print(f"\n• {channel['channel']}")
        print(f"  📹 {channel['videos_tracked']} videos tracked")
        print(f"  👁️ {channel['total_views']} total views")
        print(f"  💯 {channel['avg_engagement']} avg engagement")
        print(f"  🔗 {channel['url']}")
    
    print("\n\n📈 CONTENT BREAKDOWN")
    print("━" * 60)
    total_videos = sum(MOCK_RESULTS["categories"].values())
    print(f"Total videos indexed: {total_videos}")
    for category, count in MOCK_RESULTS["categories"].items():
        percentage = (count / total_videos) * 100
        print(f"  • {category.capitalize()}: {count} ({percentage:.1f}%)")
    
    print("\n\n💡 KEY INSIGHTS FROM THIS APPROACH")
    print("━" * 60)
    print("✅ No expensive video analysis needed")
    print("✅ Can index 10,000+ videos daily")
    print("✅ Real-time trending detection")
    print("✅ Multiple ranking algorithms")
    print("✅ Instant search on cached data")
    print("✅ Cost: ~$0 (just API quota)")
    
    print("\n\n🚀 API ENDPOINTS AVAILABLE")
    print("━" * 60)
    print("GET /rankings/daily_trending    - Today's trending videos")
    print("GET /rankings/weekly_trending   - This week's fastest growing")
    print("GET /rankings/all_time_views    - Most viewed ever")
    print("GET /rankings/high_engagement   - Best like/comment ratios")
    print("GET /channels/top              - Top golf channels")
    print("GET /search?q=putting          - Search videos")
    print("GET /stats                     - Directory statistics")
    
    print("\n\n📝 NEXT STEPS")
    print("━" * 60)
    print("1. Enable YouTube Data API v3 in Google Cloud Console")
    print("2. Run: python populate_directory.py")
    print("3. Start API: uvicorn youtube_analyzer.app.directory_api:app --reload")
    print("4. Visit: http://localhost:8000/docs for interactive API docs")
    
    # Save mock data to file for reference
    with open("mock_youtube_data.json", "w") as f:
        json.dump(MOCK_RESULTS, f, indent=2)
    print("\n\n💾 Mock data saved to mock_youtube_data.json")


if __name__ == "__main__":
    display_mock_directory()