#!/usr/bin/env python3
"""
Populate the Golf Directory with real YouTube data.
"""

import os
from dotenv import load_dotenv
from youtube_analyzer.app.golf_directory import GolfDirectory

# Load environment variables
load_dotenv()

def main():
    print("=== POPULATING GOLF DIRECTORY WITH REAL DATA ===\n")
    
    directory = GolfDirectory()
    
    if not directory.youtube_client:
        print("ERROR: No YouTube API key found!")
        print("Please ensure GOOGLE_API_KEY is set in .env file")
        return
    
    print("Step 1: Fetching golf videos from YouTube...")
    search_terms = [
        "golf",
        "PGA tour 2024",
        "golf swing tips",
        "golf course vlog",
        "golf equipment review 2024",
        "golf highlights",
        "Rick Shiels",
        "Good Good golf",
        "golf instruction",
        "breaking 80 golf"
    ]
    
    directory.update_video_catalog(search_terms)
    print("\n✓ Video catalog updated!")
    
    print("\nStep 2: Calculating rankings...")
    directory.update_rankings()
    print("✓ Rankings calculated!")
    
    print("\n=== TOP TRENDING GOLF VIDEOS ===")
    for video in directory.get_rankings('weekly_trending', limit=10):
        print(f"{video['rank']}. {video['title']}")
        print(f"   Channel: {video['channel']} | Views: {video['views']}")
        print(f"   Engagement: {video['engagement']} | Published: {video['published']}")
        print(f"   URL: {video['url']}\n")
    
    print("\n=== TOP GOLF CHANNELS ===")
    for channel in directory.get_top_channels(limit=10):
        print(f"• {channel['channel']}")
        print(f"  Videos: {channel['videos_tracked']} | Total Views: {channel['total_views']}")
        print(f"  URL: {channel['url']}\n")
    
    print("\nDirectory populated successfully!")
    print("You can now run the API server: uvicorn youtube_analyzer.app.directory_api:app --reload")


if __name__ == "__main__":
    main()