"""
YouTube Channel Resolver - Smart algorithm to find channel IDs from names/handles
"""

import os
import json
import time
from typing import Optional, Dict, List, Tuple
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

class ChannelResolver:
    def __init__(self, youtube_api_key: str):
        self.youtube = build('youtube', 'v3', developerKey=youtube_api_key)
        
    def resolve_channel(self, name: str, handle_hint: str = None) -> Optional[Dict]:
        """
        Smart algorithm to resolve a channel name to ID using multiple strategies:
        
        1. Try exact handle match (if provided)
        2. Try common handle variations 
        3. Search by channel name
        4. Search by name + "golf" keyword
        5. Manual verification prompts
        
        Returns channel info dict or None if not found
        """
        
        print(f"\n🔍 Resolving: '{name}' (hint: {handle_hint})")
        
        # Strategy 1: Try exact handle if provided
        if handle_hint:
            result = self._try_handle(handle_hint)
            if result and self._is_golf_related(result, name):
                print(f"✅ Found via exact handle: @{handle_hint}")
                return result
                
        # Strategy 2: Try common handle variations
        handle_variations = self._generate_handle_variations(name)
        for handle in handle_variations:
            result = self._try_handle(handle)
            if result and self._is_golf_related(result, name):
                print(f"✅ Found via handle variation: @{handle}")
                return result
                
        # Strategy 3: Search by channel name
        search_results = self._search_channels(name)
        for result in search_results:
            if self._is_good_match(result, name):
                print(f"✅ Found via name search: {result['title']}")
                return result
                
        # Strategy 4: Search with "golf" keyword
        golf_search_results = self._search_channels(f"{name} golf")
        for result in golf_search_results:
            if self._is_good_match(result, name):
                print(f"✅ Found via golf search: {result['title']}")
                return result
                
        print(f"❌ Could not resolve: {name}")
        return None
        
    def _try_handle(self, handle: str) -> Optional[Dict]:
        """Try to get channel by handle"""
        try:
            clean_handle = handle.lstrip('@').lower()
            response = self.youtube.channels().list(
                part='snippet,statistics',
                forHandle=clean_handle
            ).execute()
            
            if response.get('items'):
                channel = response['items'][0]
                return {
                    'id': channel['id'],
                    'title': channel['snippet']['title'],
                    'description': channel['snippet']['description'],
                    'subscriber_count': int(channel['statistics'].get('subscriberCount', 0)),
                    'handle': f"@{clean_handle}"
                }
        except Exception:
            pass
        return None
        
    def _search_channels(self, query: str) -> List[Dict]:
        """Search for channels by name"""
        try:
            response = self.youtube.search().list(
                part='snippet',
                q=query,
                type='channel',
                maxResults=10
            ).execute()
            
            results = []
            for item in response.get('items', []):
                # Get detailed channel info
                channel_response = self.youtube.channels().list(
                    part='snippet,statistics',
                    id=item['snippet']['channelId']
                ).execute()
                
                if channel_response.get('items'):
                    channel = channel_response['items'][0]
                    results.append({
                        'id': channel['id'],
                        'title': channel['snippet']['title'],
                        'description': channel['snippet']['description'],
                        'subscriber_count': int(channel['statistics'].get('subscriberCount', 0))
                    })
                    
            return results
        except Exception as e:
            print(f"Search error: {e}")
            return []
            
    def _generate_handle_variations(self, name: str) -> List[str]:
        """Generate common handle variations from a name"""
        variations = []
        clean_name = name.lower().replace(' ', '').replace('-', '').replace('_', '')
        
        # Basic variations
        variations.extend([
            clean_name,
            clean_name + 'golf',
            clean_name + 'official',
            name.lower().replace(' ', ''),
            name.lower().replace(' ', '').replace('golf', ''),
        ])
        
        # For names with spaces, try different combinations
        if ' ' in name:
            parts = name.lower().split()
            variations.extend([
                ''.join(parts),
                ''.join(parts) + 'golf',
                parts[0] + parts[-1],  # first + last name
                parts[0] + parts[-1] + 'golf',
            ])
            
        # Remove duplicates and return
        return list(set(variations))
        
    def _is_golf_related(self, channel: Dict, expected_name: str) -> bool:
        """Check if channel is golf-related and matches expected name"""
        title = channel['title'].lower()
        description = channel['description'].lower()
        expected = expected_name.lower()
        
        # Must have reasonable subscriber count (avoid fake/inactive channels)
        if channel.get('subscriber_count', 0) < 1000:
            return False
            
        # Check if name matches
        name_match = any(word in title for word in expected.split())
        
        # Check if golf-related
        golf_keywords = ['golf', 'pga', 'tour', 'swing', 'course', 'tee', 'fairway', 'green']
        golf_related = any(keyword in title + ' ' + description for keyword in golf_keywords)
        
        return name_match and golf_related
        
    def _is_good_match(self, channel: Dict, expected_name: str) -> bool:
        """Check if channel is a good match for expected name"""
        title = channel['title'].lower()
        expected = expected_name.lower()
        
        # Must have reasonable subscriber count
        if channel.get('subscriber_count', 0) < 1000:
            return False
            
        # Check for exact or close name match
        title_words = set(title.split())
        expected_words = set(expected.split())
        
        # At least 50% word overlap
        overlap = len(title_words.intersection(expected_words))
        return overlap >= len(expected_words) * 0.5
        
    def resolve_batch(self, channels: List[Dict]) -> List[Dict]:
        """Resolve multiple channels with rate limiting"""
        results = []
        
        for i, channel in enumerate(channels):
            print(f"\n--- Processing {i+1}/{len(channels)} ---")
            
            result = self.resolve_channel(
                name=channel['name'],
                handle_hint=channel.get('handle', '').lstrip('@')
            )
            
            if result:
                # Update the channel entry with resolved info
                channel['id'] = result['id']
                channel['name'] = result['title']  # Use official name
                channel['handle'] = result.get('handle', channel.get('handle', ''))
                channel['subscriber_count'] = result['subscriber_count']
                
            results.append(channel)
            
            # Rate limiting
            time.sleep(1)
            
        return results

def main():
    """Test the resolver"""
    youtube_api_key = os.getenv('YOUTUBE_API_KEY')
    resolver = ChannelResolver(youtube_api_key)
    
    # Test with some unresolved channels
    test_channels = [
        {"name": "Phil Mickelson HyFlyers", "handle": "@philmickelsonhyflyers"},
        {"name": "Brad Dalke", "handle": "@braddalke"},
        {"name": "Joey Cold Cuts", "handle": "@joeycoldcuts"},
        {"name": "Fat Perez", "handle": "@fatperez"},
    ]
    
    results = resolver.resolve_batch(test_channels)
    
    print("\n" + "="*50)
    print("RESOLUTION RESULTS:")
    print("="*50)
    
    for channel in results:
        status = "✅ RESOLVED" if channel.get('id') else "❌ FAILED"
        subs = f" ({channel.get('subscriber_count', 0):,} subs)" if channel.get('subscriber_count') else ""
        print(f"{status} {channel['name']}{subs}")
        if channel.get('id'):
            print(f"   ID: {channel['id']}")
            print(f"   Handle: {channel.get('handle', 'N/A')}")

if __name__ == "__main__":
    main()