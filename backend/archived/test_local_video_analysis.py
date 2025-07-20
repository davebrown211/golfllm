#!/usr/bin/env python3
"""
Test script for direct video analysis using a local video file.
This bypasses YouTube download issues and tests just the Gemini analysis.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the youtube_analyzer module to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'youtube_analyzer'))

from youtube_analyzer.app.ai_processing import analyze_golf_video_direct

def main():
    # Check if GOOGLE_API_KEY is loaded from .env
    if not os.getenv("GOOGLE_API_KEY"):
        print("ERROR: GOOGLE_API_KEY not found in environment variables.")
        print("Please make sure you have a .env file in the project root with:")
        print("GOOGLE_API_KEY=your_actual_api_key_here")
        return 1
    
    # Ask for local video file path
    video_path = input("Enter path to a local golf video file (mp4): ").strip()
    
    if not video_path:
        print("No video path provided. Exiting.")
        return 1
    
    if not os.path.exists(video_path):
        print(f"Video file not found: {video_path}")
        return 1
    
    try:
        print(f"\nAnalyzing local video: {video_path}")
        print("This will upload the video to Gemini and analyze it...")
        
        # Analyze the video directly
        analysis_result = analyze_golf_video_direct(video_path)
        
        print("\n" + "="*50)
        print("GOLF VIDEO ANALYSIS RESULT:")
        print("="*50)
        print(analysis_result)
        print("="*50)
        
        print("\nDirect video analysis completed successfully!")
        
    except Exception as e:
        print(f"Error during analysis: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())