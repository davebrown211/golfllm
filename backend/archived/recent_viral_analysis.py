#!/usr/bin/env python3
"""
Find recent viral golf content (last 1 month) that's substantial (not shorts)
"""

from youtube_analyzer.app.database import SessionLocal
from youtube_analyzer.app.models import YouTubeVideo, YouTubeChannel
from datetime import datetime, timedelta, timezone

def find_recent_viral():
    print("=== RECENT VIRAL GOLF CONTENT (LAST 1 MONTH) ===\n")
    
    with SessionLocal() as session:
        # Videos from last 30 days
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)
        
        recent_videos = session.query(YouTubeVideo).filter(
            YouTubeVideo.published_at >= cutoff_date
        ).all()
        
        print(f"Found {len(recent_videos)} videos from last 30 days\n")
        
        if not recent_videos:
            print("No videos from last 30 days. Expanding to last 3 months for analysis...")
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=90)
            recent_videos = session.query(YouTubeVideo).filter(
                YouTubeVideo.published_at >= cutoff_date
            ).all()
            print(f"Found {len(recent_videos)} videos from last 90 days\n")
        
        # Filter out shorts (< 60 seconds) and get substantial content
        substantial_videos = []
        
        for video in recent_videos:
            # Skip shorts
            if video.duration_seconds and video.duration_seconds < 60:
                continue
                
            # Calculate performance metrics
            channel_videos = session.query(YouTubeVideo).filter_by(
                channel_id=video.channel_id
            ).all()
            
            if len(channel_videos) > 1:
                # Calculate channel average (excluding this video)
                other_videos = [v for v in channel_videos if v.id != video.id]
                if other_videos:
                    channel_avg_views = sum(v.view_count for v in other_videos) / len(other_videos)
                    channel_avg_engagement = sum(v.engagement_rate for v in other_videos) / len(other_videos)
                    
                    # Performance multiplier vs channel average
                    view_multiplier = video.view_count / channel_avg_views if channel_avg_views > 0 else 1
                    engagement_multiplier = video.engagement_rate / channel_avg_engagement if channel_avg_engagement > 0 else 1
                else:
                    view_multiplier = 1
                    engagement_multiplier = 1
                    channel_avg_views = 0
                    channel_avg_engagement = 0
            else:
                # New channel or single video
                view_multiplier = 1
                engagement_multiplier = 1
                channel_avg_views = 0
                channel_avg_engagement = 0
            
            substantial_videos.append({
                'video': video,
                'view_multiplier': view_multiplier,
                'engagement_multiplier': engagement_multiplier,
                'channel_avg_views': channel_avg_views,
                'channel_avg_engagement': channel_avg_engagement,
                'days_since_upload': (datetime.now(timezone.utc) - video.published_at).days
            })
        
        # Sort by different viral indicators
        print("🔥 VIRAL BY VIEW COUNT (Absolute numbers):")
        view_sorted = sorted(substantial_videos, key=lambda x: x['video'].view_count, reverse=True)
        
        for i, item in enumerate(view_sorted[:10], 1):
            video = item['video']
            days_old = item['days_since_upload']
            print(f"\n{i}. {video.title}")
            print(f"   Channel: {video.channel.title}")
            print(f"   Views: {video.view_count:,} ({days_old} days ago)")
            print(f"   Engagement: {video.engagement_rate:.1f}%")
            print(f"   Duration: {video.duration_seconds//60}:{video.duration_seconds%60:02d}" if video.duration_seconds else "   Duration: Unknown")
        
        print("\n\n📈 VIRAL BY PERFORMANCE VS CHANNEL AVERAGE:")
        multiplier_sorted = sorted(
            [item for item in substantial_videos if item['view_multiplier'] > 1.5],
            key=lambda x: x['view_multiplier'], 
            reverse=True
        )
        
        for i, item in enumerate(multiplier_sorted[:10], 1):
            video = item['video']
            days_old = item['days_since_upload']
            print(f"\n{i}. {video.title}")
            print(f"   Channel: {video.channel.title}")
            print(f"   Views: {video.view_count:,} (vs {item['channel_avg_views']:,.0f} avg)")
            print(f"   Performance: {item['view_multiplier']:.1f}x above channel average")
            print(f"   Engagement: {video.engagement_rate:.1f}% (vs {item['channel_avg_engagement']:.1f}% avg)")
            print(f"   Age: {days_old} days")
        
        print("\n\n⚡ HIGH VELOCITY (Views per day since upload):")
        velocity_videos = []
        for item in substantial_videos:
            video = item['video']
            days_old = max(item['days_since_upload'], 1)  # Avoid division by zero
            velocity = video.view_count / days_old
            velocity_videos.append((video, velocity, days_old))
        
        velocity_sorted = sorted(velocity_videos, key=lambda x: x[1], reverse=True)
        
        for i, (video, velocity, days_old) in enumerate(velocity_sorted[:10], 1):
            print(f"\n{i}. {video.title}")
            print(f"   Channel: {video.channel.title}")
            print(f"   Velocity: {velocity:,.0f} views/day")
            print(f"   Total Views: {video.view_count:,} in {days_old} days")
            print(f"   Engagement: {video.engagement_rate:.1f}%")
        
        # Summary insights
        print("\n\n=== INSIGHTS ===")
        
        if substantial_videos:
            total_views = sum(item['video'].view_count for item in substantial_videos)
            avg_engagement = sum(item['video'].engagement_rate for item in substantial_videos) / len(substantial_videos)
            
            print(f"• {len(substantial_videos)} substantial videos (>60s) in recent period")
            print(f"• Total views: {total_views:,}")
            print(f"• Average engagement: {avg_engagement:.1f}%")
            
            # Channels with multiple recent hits
            channel_counts = {}
            for item in substantial_videos:
                channel = item['video'].channel.title
                if channel not in channel_counts:
                    channel_counts[channel] = 0
                channel_counts[channel] += 1
            
            active_channels = [(ch, count) for ch, count in channel_counts.items() if count > 1]
            if active_channels:
                print(f"\n• Most active channels recently:")
                for channel, count in sorted(active_channels, key=lambda x: x[1], reverse=True)[:5]:
                    print(f"  - {channel}: {count} videos")
        
        else:
            print("• No substantial recent videos found")
            print("• Consider expanding time window or checking data collection")


if __name__ == "__main__":
    find_recent_viral()