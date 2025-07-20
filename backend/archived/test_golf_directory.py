#!/usr/bin/env python3
"""
Test the Golf Directory proof of concept without requiring API key.
Creates sample data to demonstrate the concept.
"""

from youtube_analyzer.app.golf_directory import GolfDirectory
from youtube_analyzer.app.models_metadata import YouTubeVideo, YouTubeChannel, Base
from datetime import datetime, timedelta
import random
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def create_sample_data():
    """Create sample golf video data for testing."""
    
    # Create in-memory database
    engine = create_engine("sqlite:///golf_directory_demo.db")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    
    with SessionLocal() as session:
        # Sample channels
        channels = [
            ("UC123", "Rick Shiels Golf", 2500000),
            ("UC456", "GoodGood", 1800000),
            ("UC789", "GM Golf", 1200000),
            ("UC101", "TXG - Tour Experience Golf", 800000),
            ("UC202", "Peter Finch Golf", 950000),
        ]
        
        for channel_id, name, subs in channels:
            channel = YouTubeChannel(
                id=channel_id,
                title=name,
                subscriber_count=subs,
                video_count=random.randint(500, 2000),
                view_count=subs * random.randint(100, 300)
            )
            session.add(channel)
        
        # Sample videos with realistic data
        video_templates = [
            ("I Played Augusta National", "vlog", 2500000, "UC456"),
            ("The TRUTH About New TaylorMade Drivers", "equipment", 1800000, "UC123"),
            ("Breaking 90 - Course Management Tips", "instruction", 950000, "UC202"),
            ("PGA Tour Highlights - Final Round", "highlights", 3200000, "UC789"),
            ("Testing ILLEGAL Golf Balls", "equipment", 1400000, "UC101"),
            ("My Swing Changes After 30 Days", "instruction", 680000, "UC123"),
            ("Playing With Tiger Woods", "vlog", 5200000, "UC456"),
            ("Best Putting Drill Ever", "instruction", 420000, "UC202"),
            ("2024 Masters Tournament Recap", "tour", 2100000, "UC789"),
            ("$500 vs $5000 Golf Clubs", "equipment", 1900000, "UC101"),
        ]
        
        for i, (title, category, base_views, channel_id) in enumerate(video_templates):
            # Randomize publish dates
            days_ago = random.randint(1, 30)
            published = datetime.now() - timedelta(days=days_ago)
            
            # Randomize view counts around base
            views = base_views + random.randint(-500000, 500000)
            likes = int(views * random.uniform(0.03, 0.08))  # 3-8% like rate
            comments = int(views * random.uniform(0.001, 0.003))  # 0.1-0.3% comment rate
            
            video = YouTubeVideo(
                id=f"vid{i:03d}",
                title=title,
                description=f"Sample description for {title}",
                channel_id=channel_id,
                published_at=published,
                view_count=views,
                like_count=likes,
                comment_count=comments,
                engagement_rate=(likes + comments) / views * 100,
                view_velocity=views / days_ago,
                duration_seconds=random.randint(300, 1800),
                category=category,
                thumbnail_url=f"https://i.ytimg.com/vi/vid{i:03d}/maxresdefault.jpg"
            )
            session.add(video)
        
        session.commit()
    
    return "golf_directory_demo.db"


def main():
    """Run the demo."""
    print("=== GOLF YOUTUBE DIRECTORY PROOF OF CONCEPT ===\n")
    
    # Create sample data
    print("Creating sample data...")
    db_path = create_sample_data()
    
    # Initialize directory with sample database
    directory = GolfDirectory(f"sqlite:///{db_path}")
    
    # Update rankings
    print("Calculating rankings...")
    directory.update_rankings()
    
    # Display results
    print("\n=== TOP TRENDING GOLF VIDEOS (BY VIEW VELOCITY) ===")
    trending = directory.get_rankings('weekly_trending', limit=5)
    for video in trending:
        print(f"{video['rank']}. {video['title']}")
        print(f"   Channel: {video['channel']}")
        print(f"   Views: {video['views']} | Engagement: {video['engagement']}")
        print(f"   Published: {video['published']}")
        print()
    
    print("\n=== MOST VIEWED GOLF VIDEOS ===")
    most_viewed = directory.get_rankings('all_time_views', limit=5)
    for video in most_viewed:
        print(f"{video['rank']}. {video['title']}")
        print(f"   Views: {video['views']} | Likes: {video['likes']}")
        print()
    
    print("\n=== HIGHEST ENGAGEMENT VIDEOS ===")
    high_engagement = directory.get_rankings('high_engagement', limit=5)
    for video in high_engagement:
        print(f"{video['rank']}. {video['title']}")
        print(f"   Engagement Rate: {video['engagement']}")
        print()
    
    print("\n=== TOP GOLF CHANNELS BY TOTAL VIEWS ===")
    channels = directory.get_top_channels(limit=5)
    for channel in channels:
        print(f"• {channel['channel']}")
        print(f"  Videos Tracked: {channel['videos_tracked']}")
        print(f"  Total Views: {channel['total_views']}")
        print(f"  Avg Engagement: {channel['avg_engagement']}")
        print()
    
    print("\n=== SEARCH DEMO ===")
    print("Searching for 'driver'...")
    results = directory.search_videos("driver")
    for result in results[:3]:
        print(f"• {result['title']} ({result['category']})")
        print(f"  {result['views']} views | {result['channel']}")
        print()
    
    print("\n=== KEY INSIGHTS ===")
    print("• This approach uses only YouTube metadata (no expensive AI)")
    print("• Can process thousands of videos per day within API quotas")
    print("• Provides multiple ranking algorithms for discovery")
    print("• Categories help users find specific content types")
    print("• Search works on cached data (instant results)")
    print("• Total cost: ~$0 (just API quota usage)")
    
    print("\n=== NEXT STEPS ===")
    print("1. Set up YouTube API credentials")
    print("2. Run the full catalog update with real data")
    print("3. Deploy the FastAPI endpoints")
    print("4. Build a simple frontend to display rankings")
    print("5. Add user features (favorites, alerts, etc.)")


if __name__ == "__main__":
    main()