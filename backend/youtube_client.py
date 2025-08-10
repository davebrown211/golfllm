"""
YouTube API Client - Python Implementation
Matches the refined Next.js youtube-client.ts logic exactly
"""

import os
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import googleapiclient.discovery
from googleapiclient.errors import HttpError
import re
# Whitelist handling moved to database level - no longer needed here

logger = logging.getLogger(__name__)

class YouTubeClient:
    """YouTube API client matching Next.js functionality"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.youtube = googleapiclient.discovery.build(
            'youtube', 'v3', developerKey=api_key
        )
        
        # Whitelist filtering now handled at database query level
    
    def parse_duration(self, duration: str) -> int:
        """Parse ISO 8601 duration to seconds (matches Next.js logic)"""
        if not duration:
            return 0
            
        # Parse PT4M13S format
        pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
        match = re.match(pattern, duration)
        
        if not match:
            return 0
            
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0) 
        seconds = int(match.group(3) or 0)
        
        return hours * 3600 + minutes * 60 + seconds
    
    def search_golf_videos(self, 
                          query: str = "golf",
                          published_after: Optional[str] = None,
                          published_before: Optional[str] = None,
                          max_results: int = 50) -> List[Dict[str, Any]]:
        """
        Search for golf videos (matches Next.js searchGolfVideos)
        """
        try:
            search_params = {
                'part': 'snippet',
                'q': query,
                'type': 'video',
                'order': 'viewCount',
                'maxResults': max_results,
                'regionCode': 'US',
                'relevanceLanguage': 'en'
            }
            
            if published_after:
                search_params['publishedAfter'] = published_after
            if published_before:
                search_params['publishedBefore'] = published_before
                
            response = self.youtube.search().list(**search_params).execute()
            
            videos = []
            for item in response.get('items', []):
                video_data = {
                    'id': item['id']['videoId'],
                    'title': item['snippet']['title'],
                    'description': item['snippet']['description'],
                    'channel_id': item['snippet']['channelId'],
                    'channel_title': item['snippet']['channelTitle'],
                    'published_at': item['snippet']['publishedAt'],
                    'thumbnail_url': self._get_best_thumbnail(item['snippet']['thumbnails'])
                }
                
                # Content filtering (matches Next.js logic)
                if self._is_valid_content(video_data):
                    videos.append(video_data)
            
            logger.info(f"Found {len(videos)} valid golf videos")
            return videos
            
        except HttpError as e:
            logger.error(f"YouTube API error: {e}")
            return []
    
    def get_channel_recent_videos(self, channel_id: str, max_results: int = 10, days_back: int = 7) -> List[Dict[str, Any]]:
        """
        Get recent videos from a specific channel
        """
        try:
            # First get the channel's uploads playlist ID
            channel_response = self.youtube.channels().list(
                part='contentDetails',
                id=channel_id
            ).execute()
            
            if not channel_response.get('items'):
                return []
            
            uploads_playlist_id = channel_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
            
            # Get recent videos from the uploads playlist
            playlist_response = self.youtube.playlistItems().list(
                part='snippet',
                playlistId=uploads_playlist_id,
                maxResults=max_results * 2  # Get more to filter by date
            ).execute()
            
            # Filter by date
            recent_videos = []
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)
            
            for item in playlist_response.get('items', []):
                published_at = datetime.strptime(
                    item['snippet']['publishedAt'], 
                    '%Y-%m-%dT%H:%M:%SZ'
                )
                
                if published_at >= cutoff_date:
                    recent_videos.append({
                        'id': item['snippet']['resourceId']['videoId'],
                        'title': item['snippet']['title'],
                        'published_at': item['snippet']['publishedAt']
                    })
                
                if len(recent_videos) >= max_results:
                    break
            
            return recent_videos
            
        except HttpError as e:
            logger.error(f"Error getting channel videos: {e}")
            return []
    
    def update_video_stats(self, video_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Update video statistics in batches of 50 (matches Next.js updateVideoStats)
        """
        if not video_ids:
            return []
            
        try:
            # Process in batches of 50 (YouTube API limit)
            all_videos = []
            batch_size = 50
            
            for i in range(0, len(video_ids), batch_size):
                batch = video_ids[i:i + batch_size]
                
                response = self.youtube.videos().list(
                    part='snippet,statistics,contentDetails',
                    id=','.join(batch)
                ).execute()
                
                for item in response.get('items', []):
                    video_data = self._parse_video_item(item)
                    all_videos.append(video_data)
                    
            logger.info(f"Updated stats for {len(all_videos)} videos")
            return all_videos
            
        except HttpError as e:
            logger.error(f"Error updating video stats: {e}")
            return []
    
    def _parse_video_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Parse YouTube API video item (matches Next.js parsing logic)"""
        snippet = item['snippet']
        statistics = item.get('statistics', {})
        content_details = item.get('contentDetails', {})
        
        # Parse statistics
        view_count = int(statistics.get('viewCount', 0))
        like_count = int(statistics.get('likeCount', 0))
        comment_count = int(statistics.get('commentCount', 0))
        
        # Calculate engagement rate (matches Next.js formula)
        engagement_rate = 0
        if view_count > 0:
            engagement_rate = ((like_count + comment_count) / view_count) * 100
        
        # Parse duration
        duration_seconds = self.parse_duration(content_details.get('duration', ''))
        
        return {
            'id': item['id'],
            'title': snippet['title'],
            'description': snippet.get('description', ''),
            'channel_id': snippet['channelId'],
            'channel_title': snippet['channelTitle'],
            'published_at': snippet['publishedAt'],
            'thumbnail_url': self._get_best_thumbnail(snippet['thumbnails']),
            'view_count': view_count,
            'like_count': like_count,
            'comment_count': comment_count,
            'engagement_rate': engagement_rate,
            'duration_seconds': duration_seconds,
            'updated_at': datetime.utcnow().isoformat()
        }
    
    def _get_best_thumbnail(self, thumbnails: Dict[str, Any]) -> str:
        """Get highest quality thumbnail (matches Next.js logic)"""
        quality_order = ['maxres', 'high', 'medium', 'default']
        
        for quality in quality_order:
            if quality in thumbnails:
                return thumbnails[quality]['url']
        
        return ''
    
    def _is_valid_content(self, video_data: Dict[str, Any]) -> bool:
        """
        Content validation (matches Next.js filtering)
        Note: Content rejection was removed in Next.js, so this just does basic filtering
        """
        title = video_data.get('title', '').lower()
        
        # Basic language filtering (matches Next.js patterns)
        if not re.search(r'[a-zA-Z]', title):
            return False
            
        # Exclude non-English content patterns
        excluded_patterns = [
            r'[あ-ん]',      # Japanese hiragana
            r'[ア-ン]',      # Japanese katakana  
            r'[一-龯]',      # Chinese/Japanese kanji
            r'[À-ÿ]'         # Accented characters
        ]
        
        for pattern in excluded_patterns:
            if re.search(pattern, title):
                return False
        
        return True
    
    def normalize_channel_identifier(self, identifier: str) -> str:
        """Convert handle to channel ID if needed, otherwise return as-is"""
        if identifier.startswith('@'):
            # It's a handle, convert to ID
            channel_info = self.get_channel_by_handle(identifier)
            if channel_info:
                return channel_info['id']
            else:
                logger.warning(f"Could not resolve handle {identifier} to channel ID")
                return identifier  # Return as-is if we can't resolve
        else:
            # It's already a channel ID
            return identifier
    
    def normalize_channel_list(self, identifiers: List[str]) -> List[str]:
        """Convert a list of mixed handles/IDs to all channel IDs"""
        normalized = []
        for identifier in identifiers:
            normalized_id = self.normalize_channel_identifier(identifier)
            normalized.append(normalized_id)
        return normalized
    
    def get_channel_by_handle(self, handle: str) -> Optional[Dict[str, Any]]:
        """Get channel info by handle (e.g., @youtubegolfhighlights)"""
        try:
            # Remove @ if present
            clean_handle = handle.lstrip('@')
            
            response = self.youtube.channels().list(
                part='snippet,statistics,contentDetails',
                forHandle=clean_handle
            ).execute()
            
            if response.get('items'):
                channel = response['items'][0]
                return {
                    'id': channel['id'],
                    'title': channel['snippet']['title'],
                    'description': channel['snippet']['description'],
                    'handle': f"@{clean_handle}",
                    'subscriber_count': int(channel['statistics'].get('subscriberCount', 0)),
                    'video_count': int(channel['statistics'].get('videoCount', 0)),
                    'view_count': int(channel['statistics'].get('viewCount', 0)),
                    'thumbnail_url': channel['snippet']['thumbnails'].get('high', {}).get('url'),
                    'uploads_playlist_id': channel['contentDetails']['relatedPlaylists']['uploads']
                }
            return None
            
        except HttpError as e:
            logger.error(f"Error getting channel by handle {handle}: {e}")
            return None
    
    def get_channel_info(self, channel_ids: List[str]) -> List[Dict[str, Any]]:
        """Get channel information"""
        try:
            batch_size = 50
            all_channels = []
            
            for i in range(0, len(channel_ids), batch_size):
                batch = channel_ids[i:i + batch_size]
                
                response = self.youtube.channels().list(
                    part='snippet,statistics',
                    id=','.join(batch)
                ).execute()
                
                for item in response.get('items', []):
                    channel_data = {
                        'id': item['id'],
                        'title': item['snippet']['title'],
                        'description': item['snippet'].get('description', ''),
                        'subscriber_count': int(item['statistics'].get('subscriberCount', 0)),
                        'video_count': int(item['statistics'].get('videoCount', 0)),
                        'view_count': int(item['statistics'].get('viewCount', 0)),
                        'thumbnail_url': self._get_best_thumbnail(item['snippet']['thumbnails']),
                        'updated_at': datetime.utcnow().isoformat()
                    }
                    all_channels.append(channel_data)
            
            return all_channels
            
        except HttpError as e:
            logger.error(f"Error getting channel info: {e}")
            return []