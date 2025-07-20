#!/usr/bin/env python3
"""
Check which golf channels we're tracking and their stats.
"""

from youtube_analyzer.app.database import SessionLocal
from youtube_analyzer.app.models import YouTubeChannel, YouTubeVideo
from sqlalchemy import func, desc

def check_channels():
    print("=== GOLF YOUTUBE CHANNELS IN DATABASE ===\n")
    
    with SessionLocal() as session:
        # Get all channels with stats
        channel_stats = session.query(
            YouTubeChannel.id,
            YouTubeChannel.title,
            YouTubeChannel.subscriber_count,
            func.count(YouTubeVideo.id).label('videos_collected'),
            func.sum(YouTubeVideo.view_count).label('total_views'),
            func.avg(YouTubeVideo.view_count).label('avg_views'),
            func.max(YouTubeVideo.view_count).label('best_video_views')
        ).outerjoin(
            YouTubeVideo
        ).group_by(
            YouTubeChannel.id, YouTubeChannel.title, YouTubeChannel.subscriber_count
        ).order_by(
            func.sum(YouTubeVideo.view_count).desc().nullslast()
        ).all()
        
        print(f"Total channels tracked: {len(channel_stats)}\n")
        
        print("CHANNELS BY TOTAL VIEWS:")
        print("-" * 100)
        print(f"{'Channel':<30} {'Videos':<10} {'Total Views':<15} {'Avg Views':<15} {'Best Video':<15}")
        print("-" * 100)
        
        for stats in channel_stats:
            if stats.videos_collected > 0:
                print(f"{stats.title[:29]:<30} {stats.videos_collected:<10} "
                      f"{int(stats.total_views or 0):>14,} "
                      f"{int(stats.avg_views or 0):>14,} "
                      f"{int(stats.best_video_views or 0):>14,}")
        
        # Show channels we're planning to add
        print("\n\n=== RECOMMENDED CHANNELS TO ADD ===")
        print("\nMAJOR GOLF YOUTUBERS:")
        recommended = {
            "UCq-Rqdgna3OJxPg3aBt3c3Q": "Rick Shiels Golf (2.5M subs)",
            "UCfi-mPMOmche6WI-jkvnGXw": "Good Good (1.8M subs)",
            "UC9ywmLLYtiWKC0nHPWA_53g": "GM Golf (1.2M subs)",
            "UCgUueMmSpcl-aCTt5CuCKQw": "Grant Horvat Golf (1M subs)",
            "UCl4Z0A7wt0aw-gHPcPXBxKA": "Luke Kwon Golf (500K subs)",
            "UCDnv_1DzQGaHCPz6Jc6cfjQ": "TXG - Tour Experience Golf (800K subs)",
            "UCVZMKsVxmgYpgtfcbkq1mZg": "Peter Finch Golf (950K subs)",
            "UCZelGnfKLXic4gDP8xfwXKg": "Golf Sidekick (650K subs)",
            "UCaioJ73g8HlZ8d3apaiCMxg": "Micah Morris Golf (400K subs)",
            "UC0QLmupAq9GktezSAk_oVCw": "Bryan Bros Golf (300K subs)",
        }
        
        print("\nINSTRUCTION FOCUSED:")
        instruction = {
            "UCXPXrE2M8jmr1kUGQ0vuPEw": "Danny Maude (500K subs)",
            "UCQd_qgUk2olgFhH3RXvYmhg": "Me and My Golf (450K subs)",
            "UCbQQKqbwJp3N_m7LwmJzYrw": "Clay Ballard - Top Speed Golf (350K subs)",
            "UC9FgOZOz1vRGJCaReNQXKmA": "Athletic Motion Golf (200K subs)",
            "UCAE0t7yWXUgXyKC3w5VeHKw": "Chris Ryan Golf (300K subs)",
        }
        
        print("\nTOUR/PROFESSIONAL:")
        tour = {
            "UCKwGZZMrhNYKzucCtTPY2Nw": "PGA TOUR (1.5M subs)",
            "UCRBxbDlh5-1-9mXz1Dd7UCA": "DP World Tour (500K subs)",
            "UCxu1btBKsH-iGJmqN3hf1Gw": "USGA (300K subs)",
            "UC7TqDvBSuz9e_dKOaNGauJQ": "The Open (250K subs)",
        }
        
        print("\nENTERTAINMENT/VLOG:")
        entertainment = {
            "UCaS8PbJ4skMeqsNJN7xAQmg": "Foreplay Golf (400K subs)",
            "UCHmAKsNPQ1FdJ0hQ4WhZMPQ": "No Laying Up (350K subs)",
            "UC2Xqy5e1NjdGNwTjmXTLkuA": "Random Golf Club (250K subs)",
            "UCW21y7vjvMOJEGQzTK3MXQA": "Golf Life TV (200K subs)",
        }
        
        print("\nRISING/NEWER CHANNELS:")
        rising = {
            "UC79Zncey_Jlk": "George Bryan (150K subs)",
            "UCCHuiIcQ24gAyqJJa4fcJFA": "Divot Dudes (100K subs)",
            "UCUOqlmPAo8h4pVQ4cuRECUg": "Big Wedge Golf (80K subs)",
            "UCZ7o35MlY0u5b5ksIgfJzBg": "Tubes & Ange Golf Life (150K subs)",
        }
        
        # Check which we already have
        existing_ids = [stats.id for stats in channel_stats]
        
        for category, channels in [
            ("MAJOR", recommended),
            ("INSTRUCTION", instruction),
            ("TOUR", tour),
            ("ENTERTAINMENT", entertainment),
            ("RISING", rising)
        ]:
            print(f"\n{category}:")
            for channel_id, info in channels.items():
                status = "✓ Tracked" if channel_id in existing_ids else "○ Not tracked"
                print(f"  {status} {info}")
        
        # Show collection commands
        print("\n\n=== COLLECTION COMMANDS ===")
        print("\nTo collect from a specific channel:")
        print("python -c \"from youtube_analyzer.app.expanded_collector import ExpandedGolfCollector; "
              "c = ExpandedGolfCollector(); c.collect_historical_channel_data('CHANNEL_ID', max_videos=50)\"")
        
        print("\nTo collect from all recommended channels:")
        print("python -m youtube_analyzer.app.expanded_collector")


if __name__ == "__main__":
    check_channels()