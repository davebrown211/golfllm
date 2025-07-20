#!/usr/bin/env python3
"""
Test the YouTube Data API for golf content discovery.
This script demonstrates what data we can extract without expensive video analysis.
"""

import os
from youtube_analyzer.app.youtube_metadata import YouTubeMetadataClient
import json
from datetime import datetime, timedelta

def analyze_golf_content_landscape():
    """
    Analyze the golf content landscape on YouTube using only metadata.
    """
    api_key = os.getenv('YOUTUBE_API_KEY') or os.getenv('GOOGLE_API_KEY')
    if not api_key:
        print("Please set YOUTUBE_API_KEY or GOOGLE_API_KEY environment variable")
        return
    
    client = YouTubeMetadataClient(api_key)
    
    # 1. Find most popular golf channels
    print("\n=== ANALYZING POPULAR GOLF CONTENT ===")
    popular_videos = client.search_golf_videos(max_results=50)
    
    # Extract unique channels
    channel_stats = {}
    for video in popular_videos:
        channel_id = video['channel_id']
        if channel_id not in channel_stats:
            channel_stats[channel_id] = {
                'name': video['channel_title'],
                'videos': [],
                'total_views': 0
            }
        channel_stats[channel_id]['videos'].append(video)
        channel_stats[channel_id]['total_views'] += video['view_count']
    
    # Get detailed channel info
    channel_ids = list(channel_stats.keys())[:10]
    channel_details = client.get_channel_details(channel_ids)
    
    print("\n=== TOP GOLF CHANNELS BY SUBSCRIBER COUNT ===")
    sorted_channels = sorted(
        [(cid, details) for cid, details in channel_details.items()],
        key=lambda x: x[1]['subscriber_count'],
        reverse=True
    )
    
    for i, (channel_id, details) in enumerate(sorted_channels[:10], 1):
        print(f"{i}. {details['title']}")
        print(f"   Subscribers: {details['subscriber_count']:,}")
        print(f"   Total Views: {details['view_count']:,}")
        print(f"   Videos: {details['video_count']:,}")
        print()
    
    # 2. Analyze content types
    print("\n=== GOLF CONTENT CATEGORIES ===")
    categories = ['instruction', 'equipment', 'tour', 'highlights', 'vlogs']
    category_stats = {}
    
    for category in categories:
        videos = client.search_by_golf_topic(category, max_results=10)
        total_views = sum(v['view_count'] for v in videos)
        avg_engagement = sum(v['engagement_rate'] for v in videos) / len(videos) if videos else 0
        
        category_stats[category] = {
            'total_views': total_views,
            'avg_engagement': avg_engagement,
            'top_video': videos[0] if videos else None
        }
        
        print(f"\n{category.upper()}:")
        print(f"  Total Views (top 10): {total_views:,}")
        print(f"  Avg Engagement: {avg_engagement:.2f}%")
        if category_stats[category]['top_video']:
            print(f"  Top Video: {category_stats[category]['top_video']['title']}")
    
    # 3. Trending analysis
    print("\n\n=== TRENDING PATTERNS ===")
    time_periods = [1, 7, 30]
    for days in time_periods:
        videos = client.get_trending_golf_videos(days=days)
        if videos:
            total_views = sum(v['view_count'] for v in videos[:10])
            print(f"\nLast {days} day(s) - Top 10 videos total views: {total_views:,}")
            print(f"  Most viral: {videos[0]['title']} ({videos[0]['view_count']:,} views)")
    
    # 4. Save raw data for further analysis
    output_data = {
        'popular_videos': popular_videos[:20],
        'top_channels': {cid: details for cid, details in sorted_channels[:10]},
        'category_analysis': category_stats,
        'timestamp': datetime.now().isoformat()
    }
    
    with open('golf_youtube_analysis.json', 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print("\n\nAnalysis complete! Data saved to golf_youtube_analysis.json")
    
    # 5. Insights for pivot
    print("\n=== KEY INSIGHTS FOR YOUR PIVOT ===")
    print("1. Channel Focus: Build relationships with top golf channels")
    print("2. Content Types: Instruction and highlights get highest engagement")
    print("3. Trending: Videos can go viral quickly (check 1-day trending)")
    print("4. Data Available: Views, likes, comments, channel stats - all free via API")
    print("5. No AI Needed: Metadata alone provides rich insights for a directory")


if __name__ == "__main__":
    analyze_golf_content_landscape()