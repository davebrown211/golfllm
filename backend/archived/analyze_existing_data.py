#!/usr/bin/env python3
"""
Analyze existing data to find hidden channels and patterns
"""

from youtube_analyzer.app.database import SessionLocal
from youtube_analyzer.app.models import YouTubeVideo, YouTubeChannel
from collections import Counter
import re

def analyze_content():
    print("=== ANALYZING EXISTING DATA FOR HIDDEN CHANNELS ===\n")
    
    with SessionLocal() as session:
        videos = session.query(YouTubeVideo).all()
        
        # 1. Channel mentions in titles
        print("1. CHANNELS MENTIONED IN VIDEO TITLES:")
        title_mentions = Counter()
        
        for video in videos:
            # Look for @mentions
            mentions = re.findall(r'@([A-Za-z0-9_\-]+)', video.title)
            for mention in mentions:
                if len(mention) > 3:
                    title_mentions[mention] += 1
        
        for mention, count in title_mentions.most_common(10):
            print(f"  @{mention} - mentioned {count} times")
        
        # 2. Collaboration patterns
        print("\n2. COLLABORATION PATTERNS:")
        collab_keywords = ['vs', 'with', 'ft.', 'feat.', '&', 'and']
        collab_videos = []
        
        for video in videos:
            title_lower = video.title.lower()
            if any(keyword in title_lower for keyword in collab_keywords):
                collab_videos.append(video.title)
        
        print(f"Found {len(collab_videos)} collaboration videos:")
        for title in collab_videos[:10]:
            print(f"  • {title}")
        
        # 3. Channels with high engagement but few videos
        print("\n3. HIGH-POTENTIAL CHANNELS (High engagement, few videos tracked):")
        channel_stats = session.query(
            YouTubeChannel.title,
            YouTubeChannel.id,
            session.query(YouTubeVideo).filter_by(channel_id=YouTubeChannel.id).count().label('video_count'),
            session.query(YouTubeVideo.view_count).filter_by(channel_id=YouTubeChannel.id).func.avg().label('avg_views'),
            session.query(YouTubeVideo.engagement_rate).filter_by(channel_id=YouTubeChannel.id).func.avg().label('avg_engagement')
        ).all()
        
        # Simulate getting stats (SQLAlchemy subquery would be complex)
        high_potential = []
        for channel in session.query(YouTubeChannel).all():
            videos = session.query(YouTubeVideo).filter_by(channel_id=channel.id).all()
            if len(videos) > 0:
                avg_engagement = sum(v.engagement_rate for v in videos) / len(videos)
                avg_views = sum(v.view_count for v in videos) / len(videos)
                
                # High engagement + decent views + few videos = potential
                if avg_engagement > 3.0 and avg_views > 100000 and len(videos) <= 5:
                    high_potential.append({
                        'channel': channel.title,
                        'videos': len(videos),
                        'avg_engagement': avg_engagement,
                        'avg_views': avg_views
                    })
        
        for ch in sorted(high_potential, key=lambda x: x['avg_engagement'], reverse=True):
            print(f"  {ch['channel']}: {ch['avg_engagement']:.1f}% engagement, {ch['avg_views']:,.0f} avg views, {ch['videos']} videos")
        
        # 4. Channels by category distribution
        print("\n4. CHANNEL CONTENT FOCUS:")
        channel_categories = {}
        
        for channel in session.query(YouTubeChannel).all():
            videos = session.query(YouTubeVideo).filter_by(channel_id=channel.id).all()
            if videos:
                categories = [v.category for v in videos if v.category]
                if categories:
                    most_common_cat = Counter(categories).most_common(1)[0][0]
                    if most_common_cat not in channel_categories:
                        channel_categories[most_common_cat] = []
                    channel_categories[most_common_cat].append({
                        'name': channel.title,
                        'video_count': len(videos),
                        'total_views': sum(v.view_count for v in videos)
                    })
        
        for category, channels in channel_categories.items():
            print(f"\n{category.upper()} CHANNELS:")
            sorted_channels = sorted(channels, key=lambda x: x['total_views'], reverse=True)
            for ch in sorted_channels[:5]:
                print(f"  • {ch['name']} ({ch['video_count']} videos, {ch['total_views']:,} total views)")
        
        # 5. Trending indicators
        print("\n5. POTENTIAL TRENDING CONTENT:")
        recent_high_engagement = []
        
        for video in videos:
            if video.engagement_rate > 5.0 and video.view_count > 50000:
                recent_high_engagement.append({
                    'title': video.title,
                    'channel': video.channel.title,
                    'engagement': video.engagement_rate,
                    'views': video.view_count
                })
        
        for video in sorted(recent_high_engagement, key=lambda x: x['engagement'], reverse=True)[:10]:
            print(f"  • {video['title'][:60]}...")
            print(f"    {video['channel']} - {video['engagement']:.1f}% engagement, {video['views']:,} views")
        
        # 6. Recommendations
        print("\n\n=== RECOMMENDATIONS ===")
        print("📈 CHANNELS TO EXPAND (collect more videos):")
        for ch in high_potential[:5]:
            print(f"  • {ch['channel']} - Only {ch['videos']} videos but {ch['avg_engagement']:.1f}% engagement")
        
        print("\n🔍 SEARCH TERMS FOR DISCOVERY:")
        discovered_terms = set()
        for video in videos:
            # Extract potential golf terms
            words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', video.title)
            for word in words:
                if 'golf' in word.lower() or len(word.split()) > 1:
                    discovered_terms.add(word)
        
        golf_terms = [term for term in discovered_terms if 'golf' in term.lower()][:10]
        for term in golf_terms:
            print(f"  • '{term}' channel search")


if __name__ == "__main__":
    analyze_content()