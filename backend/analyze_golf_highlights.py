#!/usr/bin/env python3
"""
Analyze Youtube Golf Highlights channel to find channels mentioned in their videos
"""

import os
import sys
import re
from dotenv import load_dotenv
from youtube_client import YouTubeClient
import json

# Load environment variables
load_dotenv()

def extract_channels_from_text(text):
    """Extract potential channel names and handles from text"""
    channels = set()
    
    # Look for @handles
    handle_pattern = r'@[\w\d_-]+'
    handles = re.findall(handle_pattern, text, re.IGNORECASE)
    channels.update(handles)
    
    # Look for common golf channel patterns
    golf_patterns = [
        r'\b(\w+\s+golf)\b',
        r'\b(golf\s+\w+)\b',
        r'\b(\w+\s+pga)\b',
        r'\b(pga\s+\w+)\b',
        r'\b(\w+\s+tour)\b',
        r'\b(tour\s+\w+)\b'
    ]
    
    for pattern in golf_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            if len(match) > 3:  # Filter out very short matches
                channels.add(match.strip())
    
    return list(channels)

def analyze_youtube_golf_highlights():
    """Analyze the Youtube Golf Highlights channel"""
    
    youtube_api_key = os.getenv('YOUTUBE_API_KEY') or os.getenv('GOOGLE_API_KEY')
    if not youtube_api_key:
        print("❌ No YouTube API key found")
        return
    
    youtube_client = YouTubeClient(youtube_api_key)
    
    print("🔍 Analyzing Youtube Golf Highlights channel...")
    
    # Get channel info by handle
    channel = youtube_client.get_channel_by_handle('@youtubegolfhighlights')
    
    if not channel:
        print("❌ Could not find channel @youtubegolfhighlights")
        return
    
    print(f"✅ Found channel: {channel['title']}")
    print(f"📊 Subscribers: {channel['subscriber_count']:,}")
    print(f"📺 Videos: {channel['video_count']:,}")
    print(f"🆔 Channel ID: {channel['id']}")
    print()
    
    # Get recent videos from this channel
    print("📹 Getting recent videos...")
    videos = youtube_client.get_channel_recent_videos(channel['id'], max_results=20, days_back=30)
    
    all_mentioned_channels = set()
    
    print(f"Found {len(videos)} recent videos:")
    print()
    
    for i, video in enumerate(videos, 1):
        title = video.get('title', '')
        description = video.get('description', '')
        
        print(f"{i}. {title}")
        print(f"   Views: {video.get('view_count', 0):,}")
        
        # Extract channels mentioned in title and description
        mentioned_in_title = extract_channels_from_text(title)
        mentioned_in_desc = extract_channels_from_text(description)
        
        all_mentioned = mentioned_in_title + mentioned_in_desc
        
        if all_mentioned:
            print(f"   🏌️ Mentions: {', '.join(all_mentioned[:5])}")  # Show first 5
            all_mentioned_channels.update(all_mentioned)
        
        print()
    
    print("=" * 60)
    print("📋 SUMMARY OF MENTIONED CHANNELS:")
    print("=" * 60)
    
    # Sort and display all mentioned channels
    sorted_channels = sorted(list(all_mentioned_channels))
    
    for channel_mention in sorted_channels:
        print(f"• {channel_mention}")
    
    print()
    print(f"Total unique mentions: {len(sorted_channels)}")
    
    # Try to resolve some handles to actual channels
    print()
    print("🔍 Resolving channel handles...")
    
    resolved_channels = []
    for mention in sorted_channels:
        if mention.startswith('@'):
            try:
                resolved = youtube_client.get_channel_by_handle(mention)
                if resolved:
                    resolved_channels.append({
                        'handle': mention,
                        'title': resolved['title'],
                        'id': resolved['id'],
                        'subscribers': resolved['subscriber_count']
                    })
                    print(f"✅ {mention} → {resolved['title']} ({resolved['subscriber_count']:,} subs)")
                else:
                    print(f"❌ Could not resolve {mention}")
            except Exception as e:
                print(f"❌ Error resolving {mention}: {e}")
    
    # Save results
    results = {
        'channel_analyzed': channel,
        'videos_analyzed': len(videos),
        'mentioned_channels': sorted_channels,
        'resolved_channels': resolved_channels,
        'analysis_date': str(datetime.now())
    }
    
    with open('golf_highlights_analysis.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print()
    print("📁 Results saved to golf_highlights_analysis.json")

if __name__ == "__main__":
    from datetime import datetime
    analyze_youtube_golf_highlights()