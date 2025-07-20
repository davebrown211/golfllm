#!/usr/bin/env python3
"""
Test script for the new direct video analysis approach using Gemini 1.5 Pro.
This tests the core functionality without the full Celery/database setup.
"""

import os
import sys
import tempfile
import yt_dlp
from urllib.parse import urlparse, parse_qs
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the youtube_analyzer module to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'youtube_analyzer'))

from youtube_analyzer.app.ai_processing import analyze_golf_video_direct

def get_video_id(url):
    """Extract video ID from YouTube URL."""
    if 'youtu.be' in url:
        return url.split('/')[-1]
    query = urlparse(url).query
    return parse_qs(query).get('v', [None])[0]

def download_test_video(youtube_url: str, temp_dir: str) -> str:
    """Download a video for testing."""
    video_id = get_video_id(youtube_url)
    if not video_id:
        raise ValueError("Could not extract video ID.")

    video_path = os.path.join(temp_dir, f"{video_id}.mp4")
    
    print(f"Downloading video: {youtube_url}")
    print("This will use Chrome cookies and may prompt for your system password...")
    
    # Use Chrome cookies to bypass bot detection
    download_opts = {
        'format': 'best[ext=mp4]/best',
        'outtmpl': video_path,
        'quiet': False,  # Show progress
        'ignoreconfig': True,
        'nocheckcertificate': True,
        'no_cachedir': True,
        'cookiesfrombrowser': ('chrome',),  # Use Chrome cookies
    }
    
    try:
        with yt_dlp.YoutubeDL(download_opts) as ydl:
            ydl.download([youtube_url])
    except Exception as e:
        print(f"Download failed: {e}")
        raise
    
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video download failed: {video_path}")
    
    print(f"Video downloaded: {video_path}")
    return video_path

def main():
    # Check if GOOGLE_API_KEY is loaded from .env
    if not os.getenv("GOOGLE_API_KEY"):
        print("ERROR: GOOGLE_API_KEY not found in environment variables.")
        print("Please make sure you have a .env file in the project root with:")
        print("GOOGLE_API_KEY=your_actual_api_key_here")
        return 1
    
    # Test with a short golf video (replace with actual golf video URL)
    test_url = input("Enter a YouTube golf video URL to test: ").strip()
    
    if not test_url:
        print("No URL provided. Exiting.")
        return 1
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            print(f"Using temporary directory: {temp_dir}")
            
            # Download the video
            video_path = download_test_video(test_url, temp_dir)
            
            # Analyze the video directly
            print("\nStarting direct video analysis with Gemini 1.5 Pro...")
            analysis_result = analyze_golf_video_direct(video_path)
            
            print("\n" + "="*50)
            print("GOLF VIDEO ANALYSIS RESULT:")
            print("="*50)
            print(analysis_result)
            print("="*50)
            
            print("\nDirect video analysis completed successfully!")
            
    except Exception as e:
        print(f"Error during test: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())