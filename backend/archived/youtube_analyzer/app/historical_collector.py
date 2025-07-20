"""
Comprehensive Historical Data Collection
Systematically collect more videos from high-performing channels
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict
from youtube_analyzer.app.golf_directory import GolfDirectory
from youtube_analyzer.app.database import SessionLocal
from youtube_analyzer.app.models import YouTubeChannel, YouTubeVideo
from sqlalchemy import func
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HistoricalCollector:
    def __init__(self):
        self.directory = GolfDirectory()
        self.api_quota_used = 0
        self.daily_quota_limit = 9000  # Leave some buffer
        
    def get_collection_priority_list(self):
        """Generate prioritized list of channels to collect from."""
        
        with SessionLocal() as session:
            # Get channels with their current video counts and performance
            channels = session.query(YouTubeChannel).all()
            
            priority_channels = []
            
            for channel in channels:
                videos = session.query(YouTubeVideo).filter_by(channel_id=channel.id).all()
                
                if videos:
                    total_views = sum(v.view_count for v in videos)
                    avg_views = total_views / len(videos)
                    avg_engagement = sum(v.engagement_rate for v in videos) / len(videos)
                    
                    # Calculate priority score
                    # High views + high engagement + few videos collected = high priority
                    completeness_penalty = max(0, (50 - len(videos)) / 50)  # More penalty for fewer videos
                    quality_score = (avg_views / 1000000) + (avg_engagement / 5.0)  # Normalize metrics
                    
                    priority_score = quality_score * (1 + completeness_penalty)
                    
                    priority_channels.append({
                        'channel_id': channel.id,
                        'title': channel.title,
                        'current_videos': len(videos),
                        'avg_views': avg_views,
                        'avg_engagement': avg_engagement,
                        'total_views': total_views,
                        'priority_score': priority_score
                    })
            
            # Sort by priority score
            return sorted(priority_channels, key=lambda x: x['priority_score'], reverse=True)
    
    def collect_channel_deep_dive(self, channel_id: str, target_videos: int = 100):
        """Collect comprehensive history from a specific channel."""
        logger.info(f"Deep diving channel: {channel_id}")
        
        if self.api_quota_used >= self.daily_quota_limit:
            logger.warning("Approaching quota limit")
            return 0
        
        collected = 0
        try:
            # Get channel info first
            channel_response = self.directory.youtube_client.youtube.channels().list(
                part='contentDetails,snippet,statistics',
                id=channel_id
            ).execute()
            
            self.api_quota_used += 1
            
            if not channel_response['items']:
                logger.error(f"Channel {channel_id} not found")
                return 0
            
            channel_info = channel_response['items'][0]
            uploads_playlist = channel_info['contentDetails']['relatedPlaylists']['uploads']
            
            logger.info(f"Collecting from: {channel_info['snippet']['title']}")
            
            # Update channel info in database
            with SessionLocal() as session:
                channel = session.query(YouTubeChannel).filter_by(id=channel_id).first()
                if channel:
                    stats = channel_info.get('statistics', {})
                    channel.subscriber_count = int(stats.get('subscriberCount', 0))
                    channel.video_count = int(stats.get('videoCount', 0))
                    channel.view_count = int(stats.get('viewCount', 0))
                    session.commit()
            
            # Collect videos from uploads playlist
            next_page_token = None
            
            while collected < target_videos and self.api_quota_used < self.daily_quota_limit:
                # Get playlist items
                playlist_response = self.directory.youtube_client.youtube.playlistItems().list(
                    part='contentDetails',
                    playlistId=uploads_playlist,
                    maxResults=50,
                    pageToken=next_page_token
                ).execute()
                
                self.api_quota_used += 1
                
                video_ids = [item['contentDetails']['videoId'] for item in playlist_response['items']]
                
                if not video_ids:
                    break
                
                # Get video details in batches
                for i in range(0, len(video_ids), 50):
                    batch_ids = video_ids[i:i+50]
                    
                    try:
                        videos = self.directory.youtube_client.get_video_details(batch_ids)
                        self.api_quota_used += len(batch_ids)
                        
                        # Save to database
                        with SessionLocal() as session:
                            for video_data in videos:
                                try:
                                    self.directory._upsert_video(session, video_data)
                                    session.commit()
                                    collected += 1
                                except Exception as e:
                                    session.rollback()
                                    logger.error(f"Error saving video: {e}")
                        
                        logger.info(f"Collected {collected} videos so far...")
                        
                    except Exception as e:
                        logger.error(f"Error getting video details: {e}")
                
                next_page_token = playlist_response.get('nextPageToken')
                if not next_page_token:
                    break
            
            logger.info(f"Completed collection: {collected} videos from {channel_info['snippet']['title']}")
            
        except Exception as e:
            logger.error(f"Error collecting from channel {channel_id}: {e}")
        
        return collected
    
    def discover_and_collect_similar_channels(self):
        """Find and collect from channels similar to our high performers."""
        logger.info("Discovering similar channels...")
        
        # Search terms based on our successful channels
        discovery_searches = [
            "golf course vlog 2024",
            "amateur golf journey",
            "golf improvement channel",
            "golf challenge videos",
            "breaking 80 golf",
            "golf with tour pro",
            "public golf course",
            "golf equipment testing",
            "golf trick shots",
            "golf course review",
            "golf lessons youtube",
            "mini golf course",
            "disc golf channel",
            "women golf youtuber",
            "junior golf channel",
            "golf fitness youtube"
        ]
        
        discovered_channels = set()
        
        for search_term in discovery_searches:
            if self.api_quota_used >= self.daily_quota_limit - 100:
                break
                
            try:
                logger.info(f"Searching: {search_term}")
                videos = self.directory.youtube_client.search_golf_videos(
                    query=search_term,
                    max_results=20,
                    order="relevance"
                )
                
                self.api_quota_used += 100
                
                # Track unique channels
                for video in videos:
                    discovered_channels.add((video['channel_id'], video['channel_title']))
                
                # Save videos
                with SessionLocal() as session:
                    for video_data in videos:
                        try:
                            self.directory._upsert_video(session, video_data)
                            session.commit()
                        except Exception as e:
                            session.rollback()
                            
            except Exception as e:
                logger.error(f"Error in discovery search '{search_term}': {e}")
        
        logger.info(f"Discovered {len(discovered_channels)} unique channels")
        return list(discovered_channels)
    
    def run_comprehensive_collection(self):
        """Run the full historical collection process."""
        logger.info("=== STARTING COMPREHENSIVE HISTORICAL COLLECTION ===")
        
        # 1. Get priority list of existing channels
        priority_list = self.get_collection_priority_list()
        
        logger.info(f"Priority collection targets:")
        for i, channel in enumerate(priority_list[:10], 1):
            logger.info(f"{i}. {channel['title']} - {channel['current_videos']} videos, "
                       f"{channel['avg_views']:,.0f} avg views")
        
        total_collected = 0
        
        # 2. Deep dive into top priority channels
        for channel_data in priority_list[:15]:  # Top 15 channels
            if self.api_quota_used >= self.daily_quota_limit - 500:
                logger.warning("Approaching quota limit, stopping collection")
                break
            
            # Calculate target videos based on priority
            if channel_data['current_videos'] < 10:
                target = 50  # Get more videos from undersampled high-quality channels
            elif channel_data['current_videos'] < 25:
                target = 30  # Moderate expansion
            else:
                target = 15  # Just fill in recent gaps
            
            collected = self.collect_channel_deep_dive(
                channel_data['channel_id'], 
                target_videos=target
            )
            total_collected += collected
            
            logger.info(f"Channel total: {collected} videos, Running total: {total_collected}")
        
        # 3. Discovery phase
        if self.api_quota_used < self.daily_quota_limit - 1000:
            logger.info("Starting discovery phase...")
            discovered = self.discover_and_collect_similar_channels()
            
            # Quick sampling from discovered channels
            for channel_id, channel_title in discovered[:10]:
                if self.api_quota_used >= self.daily_quota_limit - 200:
                    break
                    
                logger.info(f"Sampling new channel: {channel_title}")
                collected = self.collect_channel_deep_dive(channel_id, target_videos=10)
                total_collected += collected
        
        # 4. Update rankings
        logger.info("Updating rankings...")
        self.directory.update_rankings()
        
        logger.info(f"=== COLLECTION COMPLETE ===")
        logger.info(f"Total videos collected: {total_collected}")
        logger.info(f"API quota used: {self.api_quota_used}/{self.daily_quota_limit}")
        
        return total_collected


def run_historical_collection():
    """Main entry point for historical collection."""
    collector = HistoricalCollector()
    return collector.run_comprehensive_collection()


if __name__ == "__main__":
    run_historical_collection()