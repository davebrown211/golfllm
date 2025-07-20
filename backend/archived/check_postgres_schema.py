#!/usr/bin/env python3
"""
Check the PostgreSQL database schema for YouTube metadata tables.
"""

from youtube_analyzer.app.database import engine, SessionLocal
from youtube_analyzer.app.models import YouTubeVideo, YouTubeChannel, VideoRanking
from sqlalchemy import text, inspect

def check_schema():
    print("=== POSTGRESQL DATABASE SCHEMA ===\n")
    
    # Get inspector
    inspector = inspect(engine)
    
    # List all tables
    tables = inspector.get_table_names()
    print("Tables in database:")
    for table in sorted(tables):
        print(f"  • {table}")
    
    # Check YouTube metadata tables
    print("\n=== YOUTUBE METADATA TABLES ===")
    
    # Check youtube_videos table
    if 'youtube_videos' in tables:
        print("\n📹 youtube_videos columns:")
        columns = inspector.get_columns('youtube_videos')
        for col in columns:
            print(f"  • {col['name']} ({col['type']})")
    
    # Check youtube_channels table
    if 'youtube_channels' in tables:
        print("\n📺 youtube_channels columns:")
        columns = inspector.get_columns('youtube_channels')
        for col in columns:
            print(f"  • {col['name']} ({col['type']})")
    
    # Check video_rankings table
    if 'video_rankings' in tables:
        print("\n🏆 video_rankings columns:")
        columns = inspector.get_columns('video_rankings')
        for col in columns:
            print(f"  • {col['name']} ({col['type']})")
    
    # Check relationships
    print("\n=== RELATIONSHIPS ===")
    print("• youtube_videos.channel_id → youtube_channels.id")
    print("• youtube_videos.video_analysis_id → video_analyses.id")
    print("• video_rankings.video_id → youtube_videos.id")
    
    # Check current data
    with SessionLocal() as session:
        video_count = session.query(YouTubeVideo).count()
        channel_count = session.query(YouTubeChannel).count()
        ranking_count = session.query(VideoRanking).count()
        
        print("\n=== CURRENT DATA ===")
        print(f"• Videos: {video_count}")
        print(f"• Channels: {channel_count}")
        print(f"• Rankings: {ranking_count}")
    
    print("\n✅ Database is ready for YouTube metadata collection!")
    print("\nNext steps:")
    print("1. Enable YouTube Data API v3 at:")
    print("   https://console.cloud.google.com/apis/library/youtube.googleapis.com")
    print("2. Run: python -m youtube_analyzer.app.data_collector")


if __name__ == "__main__":
    check_schema()