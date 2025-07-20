#!/usr/bin/env python3
"""
Simple analysis of our data to find interesting patterns
"""

from youtube_analyzer.app.database import SessionLocal
from youtube_analyzer.app.models import YouTubeVideo, YouTubeChannel
from collections import Counter
import re

def simple_analysis():
    print("=== HIDDEN CHANNEL DISCOVERY FROM OUR DATA ===\n")
    
    with SessionLocal() as session:
        videos = session.query(YouTubeVideo).all()
        channels = session.query(YouTubeChannel).all()
        
        print(f"Analyzing {len(videos)} videos from {len(channels)} channels...\n")
        
        # 1. Find @mentions
        print("1. @MENTIONS IN TITLES:")
        mentions = []
        for video in videos:
            found = re.findall(r'@([A-Za-z0-9_\-]+)', video.title)
            mentions.extend(found)
        
        mention_counts = Counter(mentions)
        for mention, count in mention_counts.most_common():
            print(f"  @{mention} - {count} times")
        
        # 2. Collaboration videos
        print(f"\n2. COLLABORATION VIDEOS ({len([v for v in videos if any(word in v.title.lower() for word in ['vs', 'with', 'ft.', '&'])])} found):")
        collab_videos = [v for v in videos if any(word in v.title.lower() for word in ['vs', 'with', 'ft.', '&'])]
        for video in collab_videos[:8]:
            print(f"  • {video.title}")
            print(f"    {video.channel.title} - {video.view_count:,} views")
        
        # 3. High engagement channels with few videos
        print(f"\n3. HIGH-POTENTIAL CHANNELS:")
        channel_stats = []
        
        for channel in channels:
            channel_videos = [v for v in videos if v.channel_id == channel.id]
            if len(channel_videos) > 0:
                avg_engagement = sum(v.engagement_rate for v in channel_videos) / len(channel_videos)
                total_views = sum(v.view_count for v in channel_videos)
                
                channel_stats.append({
                    'name': channel.title,
                    'video_count': len(channel_videos),
                    'avg_engagement': avg_engagement,
                    'total_views': total_views,
                    'avg_views': total_views / len(channel_videos)
                })
        
        # Sort by engagement rate
        top_engagement = sorted(channel_stats, key=lambda x: x['avg_engagement'], reverse=True)[:10]
        print("By engagement rate:")
        for ch in top_engagement:
            print(f"  {ch['name']}: {ch['avg_engagement']:.1f}% engagement, {ch['video_count']} videos")
        
        # Channels with few videos but high performance
        print(f"\nChannels with ≤3 videos but high performance:")
        few_videos = [ch for ch in channel_stats if ch['video_count'] <= 3 and ch['avg_views'] > 500000]
        for ch in sorted(few_videos, key=lambda x: x['avg_views'], reverse=True):
            print(f"  {ch['name']}: {ch['avg_views']:,.0f} avg views, {ch['video_count']} videos")
        
        # 4. Content categories
        print(f"\n4. CONTENT CATEGORIES:")
        categories = Counter([v.category for v in videos if v.category])
        for cat, count in categories.most_common():
            print(f"  {cat}: {count} videos")
        
        # 5. Find unique golf terms in titles
        print(f"\n5. POTENTIAL SEARCH TERMS FROM TITLES:")
        all_titles = ' '.join([v.title for v in videos])
        
        # Extract golf-related terms
        golf_terms = re.findall(r'\b\w*golf\w*\b', all_titles, re.IGNORECASE)
        unique_golf_terms = set([term.lower() for term in golf_terms if len(term) > 4])
        
        for term in sorted(unique_golf_terms)[:15]:
            print(f"  • {term}")
        
        # 6. Recommendations
        print(f"\n\n=== DISCOVERY RECOMMENDATIONS ===")
        
        print("🎯 EXPAND THESE CHANNELS (collect more videos):")
        expand_candidates = [ch for ch in channel_stats if ch['video_count'] < 10 and ch['total_views'] > 5000000]
        for ch in sorted(expand_candidates, key=lambda x: x['total_views'], reverse=True)[:5]:
            print(f"  • {ch['name']} - {ch['video_count']} videos, {ch['total_views']:,} total views")
        
        print("\n🔍 SEARCH FOR THESE MENTIONED CHANNELS:")
        if mention_counts:
            for mention, count in mention_counts.most_common(5):
                print(f"  • Search '@{mention}' or '{mention} golf channel'")
        
        print("\n📈 HIGH ENGAGEMENT NICHES TO EXPLORE:")
        print("  • Equipment testing channels (like TXG)")
        print("  • Course vlog channels")
        print("  • Amateur improvement channels")
        print("  • Regional/local golf channels")
        print("  • Women's golf content")
        print("  • Golf fitness/training")


if __name__ == "__main__":
    simple_analysis()