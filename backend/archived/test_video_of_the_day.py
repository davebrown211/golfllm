#!/usr/bin/env python3
"""
Test script to verify video of the day selection
"""

from youtube_analyzer.app.golf_directory import GolfDirectory
from youtube_analyzer.app.database import SessionLocal
from youtube_analyzer.app.models import VideoRanking

def check_video_of_the_day():
    directory = GolfDirectory()
    
    print("=== VIDEO OF THE DAY SELECTION TEST ===\n")
    
    # Get the top video from daily_trending
    rankings = directory.get_rankings('daily_trending', limit=1)
    
    if rankings:
        video_of_day = rankings[0]
        print("Video of the Day (Top Daily Trending):")
        print(f"Title: {video_of_day['title']}")
        print(f"Channel: {video_of_day['channel']}")
        print(f"Views: {video_of_day['views']}")
        print(f"Published: {video_of_day['published']}")
        print(f"URL: {video_of_day['url']}")
        print(f"Engagement: {video_of_day['engagement']}")
        
        # Check if Phil Mickelson video is in top 5
        print("\n=== Top 5 Daily Trending Videos ===")
        top_5 = directory.get_rankings('daily_trending', limit=5)
        for i, video in enumerate(top_5, 1):
            print(f"\n{i}. {video['title']}")
            print(f"   Views: {video['views']}")
            
            if "Phil Mickelson" in video['title'] or "Garrett & Bryson" in video['title']:
                print("   ⭐ This is the Phil Mickelson video!")
    else:
        print("No rankings found. You may need to run update_rankings() first.")
        
    # Check when rankings were last updated
    with SessionLocal() as session:
        latest_ranking = session.query(VideoRanking).filter_by(
            ranking_type='daily_trending'
        ).order_by(VideoRanking.date.desc()).first()
        
        if latest_ranking:
            print(f"\nRankings last updated: {latest_ranking.date}")
        else:
            print("\nNo rankings found in database.")
            print("Run: directory.update_rankings() to create rankings")


if __name__ == "__main__":
    check_video_of_the_day()