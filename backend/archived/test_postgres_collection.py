#!/usr/bin/env python3
"""
Test YouTube data collection in PostgreSQL database.
"""

import os
from dotenv import load_dotenv
from youtube_analyzer.app.data_collector import GolfDataCollector
from youtube_analyzer.app.database import SessionLocal
from youtube_analyzer.app.models import YouTubeVideo, YouTubeChannel
from sqlalchemy import func

load_dotenv()

def test_collection():
    print("=== TESTING YOUTUBE DATA COLLECTION IN POSTGRESQL ===\n")
    
    # Initialize collector
    collector = GolfDataCollector()
    
    if not collector.directory.youtube_client:
        print("ERROR: No API key found. Set GOOGLE_API_KEY in .env")
        return
    
    print("✓ API key found")
    print("✓ Connected to PostgreSQL database")
    
    # Collect a small sample
    print("\nCollecting sample golf videos...")
    try:
        videos = collector.directory.youtube_client.search_golf_videos(
            query="PGA tour highlights",
            max_results=5
        )
        
        print(f"Found {len(videos)} videos from YouTube API")
        
        # Save to database
        with SessionLocal() as session:
            for video_data in videos:
                collector.directory._upsert_video(session, video_data)
            session.commit()
            
            # Query stats
            video_count = session.query(func.count(YouTubeVideo.id)).scalar()
            channel_count = session.query(func.count(YouTubeChannel.id)).scalar()
            
            print(f"\n✓ Data saved to PostgreSQL!")
            print(f"  Total videos in database: {video_count}")
            print(f"  Total channels in database: {channel_count}")
            
            # Show sample
            print("\nSample videos:")
            videos = session.query(YouTubeVideo).limit(3).all()
            for v in videos:
                print(f"  • {v.title}")
                print(f"    Views: {v.view_count:,} | Channel: {v.channel.title}")
    
    except Exception as e:
        print(f"Error: {str(e)}")
        print("\nMake sure to enable YouTube Data API v3:")
        print("https://console.cloud.google.com/apis/library/youtube.googleapis.com")


if __name__ == "__main__":
    test_collection()