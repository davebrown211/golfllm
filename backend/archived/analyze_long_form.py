#!/usr/bin/env python3
"""
Analyze top long-form golf content (>5 minutes) across all channels
"""

from youtube_analyzer.app.database import SessionLocal
from youtube_analyzer.app.models import YouTubeVideo, YouTubeChannel

def analyze_long_form():
    print("=== TOP LONG-FORM GOLF CONTENT ANALYSIS ===\n")
    
    with SessionLocal() as session:
        # Get all videos longer than 5 minutes, sorted by views
        long_form_videos = session.query(YouTubeVideo).filter(
            YouTubeVideo.duration_seconds > 300
        ).order_by(
            YouTubeVideo.view_count.desc()
        ).limit(20).all()
        
        print("TOP 20 LONG-FORM VIDEOS (>5 minutes):")
        print(f"{'Rank':<4} {'Title':<55} {'Channel':<25} {'Views':<12} {'Duration':<10}")
        print("-" * 120)
        
        for i, video in enumerate(long_form_videos, 1):
            duration = video.duration_seconds
            duration_str = f"{duration//60}:{duration%60:02d}" if duration else "Unknown"
            title_short = video.title[:52] + "..." if len(video.title) > 55 else video.title
            channel_short = video.channel.title[:22] + "..." if len(video.channel.title) > 25 else video.channel.title
            
            print(f"{i:<4} {title_short:<55} {channel_short:<25} {video.view_count:<12,} {duration_str:<10}")
        
        # Analysis by channel
        print(f"\n=== LONG-FORM PERFORMANCE BY CHANNEL ===")
        channel_stats = {}
        
        for video in long_form_videos:
            channel = video.channel.title
            if channel not in channel_stats:
                channel_stats[channel] = {
                    'videos': [],
                    'total_views': 0,
                    'avg_views': 0
                }
            channel_stats[channel]['videos'].append(video)
            channel_stats[channel]['total_views'] += video.view_count
        
        # Calculate averages and sort
        for channel, stats in channel_stats.items():
            stats['avg_views'] = stats['total_views'] / len(stats['videos'])
            stats['count'] = len(stats['videos'])
        
        sorted_channels = sorted(channel_stats.items(), key=lambda x: x[1]['avg_views'], reverse=True)
        
        print(f"{'Channel':<25} {'Videos':<8} {'Avg Views':<12} {'Best Video Views':<15}")
        print("-" * 70)
        
        for channel, stats in sorted_channels:
            best_video = max(stats['videos'], key=lambda x: x.view_count)
            channel_short = channel[:22] + "..." if len(channel) > 25 else channel
            
            print(f"{channel_short:<25} {stats['count']:<8} {stats['avg_views']:<12,.0f} {best_video.view_count:<15,}")
        
        # Content category analysis
        print(f"\n=== LONG-FORM CONTENT CATEGORIES ===")
        categories = {}
        
        for video in long_form_videos:
            cat = video.category or 'uncategorized'
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(video)
        
        for category, videos in categories.items():
            avg_views = sum(v.view_count for v in videos) / len(videos)
            best_video = max(videos, key=lambda x: x.view_count)
            
            print(f"\n{category.upper()}: {len(videos)} videos")
            print(f"  Average views: {avg_views:,.0f}")
            print(f"  Best performer: {best_video.view_count:,} views")
            print(f"  Best video: '{best_video.title[:60]}...'")
        
        # Duration analysis
        print(f"\n=== DURATION ANALYSIS ===")
        duration_ranges = {
            '5-10 min': [v for v in long_form_videos if 300 <= v.duration_seconds < 600],
            '10-20 min': [v for v in long_form_videos if 600 <= v.duration_seconds < 1200], 
            '20-30 min': [v for v in long_form_videos if 1200 <= v.duration_seconds < 1800],
            '30+ min': [v for v in long_form_videos if v.duration_seconds >= 1800]
        }
        
        for range_name, videos in duration_ranges.items():
            if videos:
                avg_views = sum(v.view_count for v in videos) / len(videos)
                print(f"{range_name}: {len(videos)} videos, {avg_views:,.0f} avg views")
        
        # Engagement analysis
        print(f"\n=== ENGAGEMENT ANALYSIS ===")
        top_engagement = sorted(long_form_videos, key=lambda x: x.engagement_rate, reverse=True)[:5]
        
        print("Top 5 by engagement rate:")
        for i, video in enumerate(top_engagement, 1):
            duration_str = f"{video.duration_seconds//60}:{video.duration_seconds%60:02d}"
            print(f"{i}. {video.title[:50]}...")
            print(f"   {video.engagement_rate:.2f}% engagement | {video.view_count:,} views | {duration_str}")


if __name__ == "__main__":
    analyze_long_form()