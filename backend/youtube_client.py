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

logger = logging.getLogger(__name__)

class YouTubeClient:
    """YouTube API client matching Next.js functionality"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.youtube = googleapiclient.discovery.build(
            'youtube', 'v3', developerKey=api_key
        )
        
        # Whitelisted channel IDs (matches Next.js content-whitelist.ts)
        self.whitelisted_channels = [
            # VALIDATED CHANNELS IN DATABASE
            "UCfi-mPMOmche6WI-jkvnGXw",  # Good Good (main)
            "UCbY_v56iMzSGvXK79X6f4dw",  # Good Good Extra
            "UCqr4sONkmFEOPc3rfoVLEvg",  # Bob Does Sports
            "UCgUueMmSpcl-aCTt5CuCKQw",  # Grant Horvat Golf
            "UCJcc1x6emfrQquiV8Oe_pug",  # Luke Kwon Golf
            "UCsazhBmAVDUL_WYcARQEFQA",  # The Lads
            "UC3jFoA7_6BTV90hsRSVHoaw",  # Phil Mickelson and the HyFlyers
            "UCfdYeBYjouhibG64ep_m4Vw",  # Micah Morris
            "UCjchle1bmH0acutqK15_XSA",  # Brad Dalke
            "UCdCxaD8rWfAj12rloIYS6jQ",  # Bryan Bros Golf
            "UCB0NRdlQ6fBYQX8W8bQyoDA",  # MyTPI
            "UCyy8ULLDGSm16_EkXdIt4Gw",  # Titleist
            "UClJO9jvaU5mvNuP-XTbhHGw",  # TaylorMade Golf
            # POPULAR GOLF CREATORS
            "UCFHZHhZaH7Rc_FOMIzUziJA",  # Rick Shiels Golf
            "UCFoez1Xjc90CsHvCzqKnLcw",  # Peter Finch Golf
            "UCCxF55adGXOscJ3L8qdKnrQ",  # Bryson DeChambeau
            "UCZelGnfKLXic4gDP63dIRxw",  # Mark Crossfield
            "UCaeGjmOiTxekbGUDPKhoU-A",  # Golf Sidekick
            "UCtNpbO2MtsVY4qW23WfnxGg",  # James Robinson Golf
            "UCUOqlmPAo8h4pVQ4cuRECUg",  # Big Wedge Golf
            "UClljAz6ZKy0XeViKsohdjqA",  # GM Golf
            "UCSwdmDQhAi_-ICkAvNBLEBw",  # Danny Maude
            "UCJolpQHWLAW6cCUYGgean8w",  # Padraig Harrington
            "UCuXIBwKQeH9cnLOv7w66cJg",  # MrShortGame Golf
            "UCXvDkP2X3aE9yrPavNMJv0A",  # JnA Golf
            "UCamOYT0c_pSrSCu9c8CyEcg",  # Bryan Bros TV
            "UCrgGz4gZxWu77Nw5RXcxlRg",  # Josh Mayer
            "UCCry5X3Phfmz0UzqRNm0BPA",  # Golf Girl Games
            "UCwMgdK0S57nEdN_RGaajwOQ",  # GOLF LIFE
        ]
    
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