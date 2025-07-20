import os
from googleapiclient.discovery import build
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import json

class YouTubeMetadataClient:
    def __init__(self, api_key: str):
        self.youtube = build('youtube', 'v3', developerKey=api_key)
    
    def search_golf_videos(self, 
                          query: str = "golf", 
                          max_results: int = 50,
                          order: str = "viewCount",
                          published_after: Optional[datetime] = None) -> List[Dict]:
        """
        Search for golf videos with various sorting options.
        
        Args:
            query: Search query (default: "golf")
            max_results: Maximum number of results to return
            order: Sort order - "viewCount", "date", "rating", "relevance"
            published_after: Only return videos published after this date
        """
        search_params = {
            'part': 'snippet',
            'q': query,
            'type': 'video',
            'maxResults': max_results,
            'order': order,
            'videoCategoryId': '17',  # Sports category
        }
        
        if published_after:
            # Format date for YouTube API (RFC 3339)
            search_params['publishedAfter'] = published_after.strftime('%Y-%m-%dT%H:%M:%SZ')
        
        response = self.youtube.search().list(**search_params).execute()
        
        video_ids = [item['id']['videoId'] for item in response['items']]
        return self.get_video_details(video_ids)
    
    def get_video_details(self, video_ids: List[str]) -> List[Dict]:
        """
        Get detailed statistics and metadata for videos.
        """
        response = self.youtube.videos().list(
            part='snippet,statistics,contentDetails',
            id=','.join(video_ids)
        ).execute()
        
        videos = []
        for item in response['items']:
            video_data = {
                'id': item['id'],
                'title': item['snippet']['title'],
                'description': item['snippet']['description'],
                'channel_id': item['snippet']['channelId'],
                'channel_title': item['snippet']['channelTitle'],
                'published_at': item['snippet']['publishedAt'],
                'duration': item['contentDetails']['duration'],
                'view_count': int(item['statistics'].get('viewCount', 0)),
                'like_count': int(item['statistics'].get('likeCount', 0)),
                'comment_count': int(item['statistics'].get('commentCount', 0)),
                'thumbnail': item['snippet']['thumbnails']['high']['url']
            }
            
            # Calculate engagement rate
            if video_data['view_count'] > 0:
                video_data['engagement_rate'] = (
                    (video_data['like_count'] + video_data['comment_count']) / 
                    video_data['view_count'] * 100
                )
            else:
                video_data['engagement_rate'] = 0
                
            videos.append(video_data)
        
        return videos
    
    def get_channel_details(self, channel_ids: List[str]) -> Dict[str, Dict]:
        """
        Get channel statistics for golf content creators.
        """
        response = self.youtube.channels().list(
            part='snippet,statistics',
            id=','.join(channel_ids)
        ).execute()
        
        channels = {}
        for item in response['items']:
            channels[item['id']] = {
                'title': item['snippet']['title'],
                'description': item['snippet']['description'],
                'subscriber_count': int(item['statistics'].get('subscriberCount', 0)),
                'video_count': int(item['statistics'].get('videoCount', 0)),
                'view_count': int(item['statistics'].get('viewCount', 0)),
                'thumbnail': item['snippet']['thumbnails']['high']['url']
            }
        
        return channels
    
    def get_trending_golf_videos(self, days: int = 7) -> List[Dict]:
        """
        Get trending golf videos from the past N days.
        """
        published_after = datetime.now() - timedelta(days=days)
        return self.search_golf_videos(
            query="golf",
            order="viewCount",
            published_after=published_after
        )
    
    def search_by_golf_topic(self, topic: str, max_results: int = 25) -> List[Dict]:
        """
        Search for specific golf topics like "golf swing", "putting tips", etc.
        """
        topics = {
            'instruction': 'golf instruction tips lesson',
            'equipment': 'golf clubs equipment review',
            'tour': 'PGA tour golf tournament',
            'highlights': 'golf highlights best shots',
            'vlogs': 'golf vlog course review'
        }
        
        query = topics.get(topic, topic)
        return self.search_golf_videos(query=query, max_results=max_results)


def demo_youtube_api():
    """
    Demo function to show YouTube API capabilities.
    """
    api_key = os.getenv('YOUTUBE_API_KEY') or os.getenv('GOOGLE_API_KEY')
    if not api_key:
        print("Please set YOUTUBE_API_KEY or GOOGLE_API_KEY environment variable")
        return
    
    client = YouTubeMetadataClient(api_key)
    
    print("\n=== TOP GOLF VIDEOS BY VIEWS ===")
    top_videos = client.search_golf_videos(max_results=10)
    for i, video in enumerate(top_videos, 1):
        print(f"{i}. {video['title']}")
        print(f"   Views: {video['view_count']:,} | Likes: {video['like_count']:,}")
        print(f"   Channel: {video['channel_title']}")
        print(f"   Engagement: {video['engagement_rate']:.2f}%")
        print()
    
    print("\n=== TRENDING GOLF VIDEOS (LAST 7 DAYS) ===")
    trending = client.get_trending_golf_videos(days=7)
    for i, video in enumerate(trending[:5], 1):
        print(f"{i}. {video['title']}")
        print(f"   Views: {video['view_count']:,} | Published: {video['published_at']}")
        print()
    
    print("\n=== GOLF INSTRUCTION VIDEOS ===")
    instruction = client.search_by_golf_topic('instruction', max_results=5)
    for i, video in enumerate(instruction, 1):
        print(f"{i}. {video['title']}")
        print(f"   Views: {video['view_count']:,}")
        print()


if __name__ == "__main__":
    demo_youtube_api()