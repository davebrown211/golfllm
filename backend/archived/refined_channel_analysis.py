#!/usr/bin/env python3
"""
More sophisticated channel analysis that accounts for viral shorts vs. consistent content
"""

from youtube_analyzer.app.database import SessionLocal
from youtube_analyzer.app.models import YouTubeVideo, YouTubeChannel

def refined_analysis():
    print("=== REFINED CHANNEL ANALYSIS ===\n")
    
    with SessionLocal() as session:
        channels = session.query(YouTubeChannel).all()
        
        print("Analyzing channels for consistent content creation vs. viral outliers...\n")
        
        consistent_creators = []
        viral_outliers = []
        
        for channel in channels:
            videos = session.query(YouTubeVideo).filter_by(channel_id=channel.id).all()
            
            if len(videos) == 0:
                continue
                
            # Calculate stats
            total_views = sum(v.view_count for v in videos)
            avg_views = total_views / len(videos)
            median_views = sorted([v.view_count for v in videos])[len(videos)//2]
            avg_engagement = sum(v.engagement_rate for v in videos) / len(videos)
            max_views = max(v.view_count for v in videos)
            min_views = min(v.view_count for v in videos)
            
            # Check for viral outliers (max view much higher than median)
            view_variance = max_views / median_views if median_views > 0 else 1
            
            stats = {
                'name': channel.title,
                'video_count': len(videos),
                'total_views': total_views,
                'avg_views': avg_views,
                'median_views': median_views,
                'avg_engagement': avg_engagement,
                'max_views': max_views,
                'min_views': min_views,
                'view_variance': view_variance,
                'videos': videos
            }
            
            # Categorize
            if view_variance > 10 and len(videos) < 5:
                viral_outliers.append(stats)
            elif len(videos) >= 3 and avg_engagement > 2.0:
                consistent_creators.append(stats)
        
        # Show consistent creators
        print("🎯 CONSISTENT HIGH-QUALITY CREATORS:")
        print("(Multiple videos with good engagement)")
        consistent_sorted = sorted(consistent_creators, key=lambda x: x['avg_engagement'], reverse=True)
        
        for creator in consistent_sorted[:10]:
            print(f"\n{creator['name']}:")
            print(f"  Videos: {creator['video_count']}")
            print(f"  Avg Views: {creator['avg_views']:,.0f}")
            print(f"  Median Views: {creator['median_views']:,.0f}")
            print(f"  Avg Engagement: {creator['avg_engagement']:.1f}%")
            
            # Show their video range
            if creator['videos']:
                recent_titles = [v.title[:50] + "..." for v in creator['videos'][:3]]
                print(f"  Sample videos: {', '.join(recent_titles)}")
        
        # Show viral outliers (might be shorts or one-hit wonders)
        print(f"\n\n⚡ VIRAL OUTLIERS (Possibly shorts or one-hit wonders):")
        viral_sorted = sorted(viral_outliers, key=lambda x: x['max_views'], reverse=True)
        
        for outlier in viral_sorted[:5]:
            print(f"\n{outlier['name']}:")
            print(f"  Max Views: {outlier['max_views']:,}")
            print(f"  Median Views: {outlier['median_views']:,}")
            print(f"  View Variance: {outlier['view_variance']:.1f}x")
            print(f"  Videos: {outlier['video_count']}")
            
            # Show the viral video
            viral_video = max(outlier['videos'], key=lambda x: x.view_count)
            print(f"  Viral Video: '{viral_video.title}'")
            print(f"  Duration: {viral_video.duration_seconds}s" if viral_video.duration_seconds else "  Duration: Unknown")
        
        # Find channels worth expanding (consistent + undersampled)
        print(f"\n\n📈 CHANNELS WORTH EXPANDING:")
        print("(Consistent quality but we have few videos)")
        
        expand_candidates = [c for c in consistent_creators if c['video_count'] < 10 and c['avg_views'] > 500000]
        expand_sorted = sorted(expand_candidates, key=lambda x: x['avg_views'], reverse=True)
        
        for candidate in expand_sorted[:8]:
            print(f"\n• {candidate['name']}")
            print(f"  Current: {candidate['video_count']} videos, {candidate['avg_views']:,.0f} avg views")
            print(f"  Potential: High-quality creator, collect more content")
        
        # True discovery recommendations
        print(f"\n\n🔍 DISCOVERY RECOMMENDATIONS:")
        print(f"1. Focus on consistent creators, not viral outliers")
        print(f"2. Look for creators with 3+ videos and >2% engagement")
        print(f"3. Prioritize channels where median views ≈ average views (consistent performance)")
        print(f"4. Viral shorts don't predict ongoing content quality")


if __name__ == "__main__":
    refined_analysis()