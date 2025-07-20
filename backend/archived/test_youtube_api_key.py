#!/usr/bin/env python3
"""
Test YouTube API key and diagnose issues.
"""

import os
from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

load_dotenv()

def test_api_key():
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        print("❌ No GOOGLE_API_KEY found in .env")
        return
    
    print(f"✓ API Key found: {api_key[:10]}...")
    
    try:
        youtube = build('youtube', 'v3', developerKey=api_key)
        
        # Test 1: Try to get a specific video (usually less restricted)
        print("\n1. Testing video details endpoint...")
        try:
            response = youtube.videos().list(
                part='snippet,statistics',
                id='dQw4w9WgXcQ'  # Well-known video ID
            ).execute()
            
            if response['items']:
                video = response['items'][0]
                print(f"✓ Video details work! Got: {video['snippet']['title']}")
                print(f"  Views: {video['statistics']['viewCount']}")
            else:
                print("❌ No video found")
                
        except HttpError as e:
            print(f"❌ Video details failed: {e}")
        
        # Test 2: Try search (more restricted)
        print("\n2. Testing search endpoint...")
        try:
            response = youtube.search().list(
                part='snippet',
                q='golf',
                type='video',
                maxResults=1
            ).execute()
            
            if response['items']:
                print(f"✓ Search works! Found: {response['items'][0]['snippet']['title']}")
            else:
                print("❌ No search results")
                
        except HttpError as e:
            print(f"❌ Search failed: {e}")
            if "forbidden" in str(e):
                print("\n⚠️  Search is blocked. This might be due to:")
                print("   1. API key restrictions (check Google Cloud Console)")
                print("   2. API not fully enabled yet")
                print("   3. Project billing not set up")
        
        # Test 3: Try channel list
        print("\n3. Testing channels endpoint...")
        try:
            response = youtube.channels().list(
                part='snippet,statistics',
                id='UCq-Rqdgna3OJxPg3aBt3c3Q'  # Rick Shiels Golf
            ).execute()
            
            if response['items']:
                channel = response['items'][0]
                print(f"✓ Channel details work! Got: {channel['snippet']['title']}")
                print(f"  Subscribers: {channel['statistics']['subscriberCount']}")
            else:
                print("❌ No channel found")
                
        except HttpError as e:
            print(f"❌ Channel details failed: {e}")
    
    except Exception as e:
        print(f"❌ Failed to create YouTube client: {e}")
    
    print("\n" + "="*60)
    print("DIAGNOSIS:")
    print("="*60)
    
    print("\nIf search is blocked but other endpoints work:")
    print("1. Go to: https://console.cloud.google.com/apis/credentials")
    print("2. Click on your API key")
    print("3. Check 'API restrictions' - should be 'Don't restrict key' or include YouTube Data API")
    print("4. Check 'Application restrictions' - try 'None' for testing")
    
    print("\nIf all endpoints fail:")
    print("1. Verify YouTube Data API v3 is enabled")
    print("2. Check if billing is enabled for the project")
    print("3. Try creating a new API key")
    
    print("\nAlternative approach:")
    print("Use only video IDs and channel IDs (no search) to avoid restrictions")


if __name__ == "__main__":
    test_api_key()