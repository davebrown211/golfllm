#!/usr/bin/env python3
"""
Generic video analysis script for golf videos.
Usage: python analyze_video.py <youtube_url>
"""

import os
import sys
import tempfile
import argparse
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
        return url.split('/')[-1].split('?')[0]
    query = urlparse(url).query
    return parse_qs(query).get('v', [None])[0]

def download_video(youtube_url: str, temp_dir: str) -> str:
    """Download a video for analysis."""
    video_id = get_video_id(youtube_url)
    if not video_id:
        raise ValueError(f"Could not extract video ID from URL: {youtube_url}")
    
    output_path = os.path.join(temp_dir, f"{video_id}.mp4")
    
    ydl_opts = {
        'outtmpl': output_path,
        'format': 'worst[height>=360][height<=480]',  # Much smaller for Flash
        'no_warnings': True,
        'quiet': True,  # Suppress download progress
    }
    
    print(f"Downloading video {video_id}...")
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.download([youtube_url])
            print(f"Download completed: {video_id}")
            return output_path
        except Exception as e:
            raise Exception(f"Download failed: {e}")

def analyze_video(youtube_url: str):
    """Analyze a YouTube video using AI."""
    video_id = get_video_id(youtube_url)
    
    print(f"Starting analysis for video: {video_id}")
    print(f"URL: {youtube_url}")
    
    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # Download video
            video_path = download_video(youtube_url, temp_dir)
            
            if not video_path or not os.path.exists(video_path):
                raise Exception("Video download failed")
            
            print(f"Running AI analysis...")
            
            # Run the AI analysis
            result = analyze_golf_video_direct(video_path)
            
            print("\n" + "="*60)
            print("ANALYSIS COMPLETED SUCCESSFULLY")
            print("="*60)
            print(f"Video ID: {video_id}")
            print(f"URL: {youtube_url}")
            print("\nResults:")
            print(result)
            print("="*60)
            
            return result
            
        except Exception as e:
            print(f"\nANALYSIS FAILED: {e}")
            import traceback
            traceback.print_exc()
            return None

def main():
    parser = argparse.ArgumentParser(description='Analyze a golf video using AI')
    parser.add_argument('url', help='YouTube URL to analyze')
    parser.add_argument('--quiet', '-q', action='store_true', help='Suppress verbose output')
    
    args = parser.parse_args()
    
    if not args.url:
        print("Error: YouTube URL is required")
        parser.print_help()
        sys.exit(1)
    
    # Validate URL
    video_id = get_video_id(args.url)
    if not video_id:
        print(f"Error: Invalid YouTube URL: {args.url}")
        sys.exit(1)
    
    # Set quiet mode
    if args.quiet:
        # Redirect stdout to suppress non-essential output
        import io
        import contextlib
        
        @contextlib.contextmanager
        def suppress_output():
            with io.StringIO() as buf, contextlib.redirect_stdout(buf):
                yield buf
        
        # Run analysis with suppressed output
        with suppress_output():
            result = analyze_video(args.url)
    else:
        result = analyze_video(args.url)
    
    # Exit code based on success
    if result:
        print(f"\nSUCCESS: Analysis completed for video {video_id}")
        sys.exit(0)
    else:
        print(f"\nFAILED: Analysis failed for video {video_id}")
        sys.exit(1)

if __name__ == "__main__":
    main()