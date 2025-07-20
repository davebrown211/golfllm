#!/usr/bin/env python3
"""
Check what YouTube metadata has been collected.
"""

from youtube_analyzer.app.database import SessionLocal
from youtube_analyzer.app.models import YouTubeVideo, YouTubeChannel, VideoRanking
from sqlalchemy import func

def check_data():
    print("=== YOUTUBE METADATA COLLECTION STATUS ===\n")
    
    with SessionLocal() as session:
        # Count data
        video_count = session.query(func.count(YouTubeVideo.id)).scalar()
        channel_count = session.query(func.count(YouTubeChannel.id)).scalar()
        ranking_count = session.query(func.count(VideoRanking.id)).scalar()
        
        print(f"📹 Videos collected: {video_count}")
        print(f"📺 Channels collected: {channel_count}")
        print(f"🏆 Rankings calculated: {ranking_count}")
        
        if video_count > 0:
            # Show top videos by views
            print("\n=== TOP 10 VIDEOS BY VIEWS ===")
            top_videos = session.query(YouTubeVideo).order_by(
                YouTubeVideo.view_count.desc()
            ).limit(10).all()
            
            for i, video in enumerate(top_videos, 1):
                print(f"\n{i}. {video.title}")
                print(f"   Channel: {video.channel.title}")
                print(f"   Views: {video.view_count:,}")
                print(f"   Likes: {video.like_count:,}")
                print(f"   Engagement: {video.engagement_rate:.2f}%")
                print(f"   Published: {video.published_at.strftime('%Y-%m-%d')}")
            
            # Show top channels
            print("\n\n=== TOP 5 CHANNELS BY VIDEO COUNT ===")
            channel_stats = session.query(
                YouTubeChannel.title,
                func.count(YouTubeVideo.id).label('video_count'),
                func.sum(YouTubeVideo.view_count).label('total_views')
            ).join(
                YouTubeVideo
            ).group_by(
                YouTubeChannel.id, YouTubeChannel.title
            ).order_by(
                func.count(YouTubeVideo.id).desc()
            ).limit(5).all()
            
            for channel in channel_stats:
                print(f"\n• {channel.title}")
                print(f"  Videos: {channel.video_count}")
                print(f"  Total Views: {int(channel.total_views):,}")
            
            # Category breakdown
            print("\n\n=== CONTENT CATEGORIES ===")
            categories = session.query(
                YouTubeVideo.category,
                func.count(YouTubeVideo.id).label('count')
            ).group_by(
                YouTubeVideo.category
            ).all()
            
            for cat in categories:
                print(f"{cat.category or 'uncategorized'}: {cat.count} videos")
        else:
            print("\nNo videos collected yet. Run data collection first.")


if __name__ == "__main__":
    check_data()