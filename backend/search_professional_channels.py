#!/usr/bin/env python3
"""Search for professional golf YouTube channels to get accurate IDs and handles"""

from youtube_client import YouTubeClient
import os
from dotenv import load_dotenv

load_dotenv()

client = YouTubeClient(os.getenv('YOUTUBE_API_KEY'))

# List of channels to search for
channels_to_find = [
    "PGA TOUR",
    "Golf Channel",
    "DP World Tour",
    "LPGA",
    "Korn Ferry Tour",
    "LIV Golf",
    "PGA of America",
    "USGA",
    "The R&A",
    "The Open Championship",
    "European Tour",
    "Ladies European Tour"
]

print("Searching for professional golf YouTube channels...")
print("=" * 60)

for channel_name in channels_to_find:
    try:
        # Search for the channel
        results = client.youtube.search().list(
            q=channel_name,
            type='channel',
            part='snippet',
            maxResults=3
        ).execute()
        
        print(f"\n{channel_name}:")
        for item in results.get('items', []):
            title = item['snippet']['title']
            channel_id = item['id']['channelId']
            description = item['snippet']['description'][:100] + "..." if len(item['snippet']['description']) > 100 else item['snippet']['description']
            
            # Highlight likely official channels
            official_marker = " ✓ LIKELY OFFICIAL" if any(word in title.lower() for word in ['official', 'tour', 'pga', 'lpga', 'usga']) else ""
            
            print(f"  - {title}{official_marker}")
            print(f"    ID: {channel_id}")
            print(f"    Description: {description}")
            
    except Exception as e:
        print(f"  Error searching for {channel_name}: {e}")

print("\n" + "=" * 60)
print("Search complete!")