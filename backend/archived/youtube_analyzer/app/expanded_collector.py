"""
Expanded YouTube Golf Data Collector
- Collects historical data from top channels
- Finds trending content through multiple methods
- Discovers new channels automatically
"""

import os
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict
from youtube_analyzer.app.golf_directory import GolfDirectory
from youtube_analyzer.app.database import SessionLocal
from youtube_analyzer.app.models import YouTubeChannel, YouTubeVideo
from sqlalchemy import func
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ExpandedGolfCollector:
    def __init__(self):
        self.directory = GolfDirectory()
        self.api_quota_used = 0
        
    def collect_historical_channel_data(self, channel_id: str, max_videos: int = 50):
        """Collect historical videos from a specific channel."""
        logger.info(f"Collecting historical data for channel: {channel_id}")
        
        try:
            # Get channel's uploads playlist
            channel_response = self.directory.youtube_client.youtube.channels().list(
                part='contentDetails,snippet',
                id=channel_id
            ).execute()
            
            if not channel_response['items']:
                return
            
            channel_info = channel_response['items'][0]
            uploads_playlist_id = channel_info['contentDetails']['relatedPlaylists']['uploads']
            
            # Get videos from uploads playlist
            videos_collected = 0
            next_page_token = None
            
            while videos_collected < max_videos:
                playlist_response = self.directory.youtube_client.youtube.playlistItems().list(
                    part='contentDetails',
                    playlistId=uploads_playlist_id,
                    maxResults=min(50, max_videos - videos_collected),
                    pageToken=next_page_token
                ).execute()
                
                video_ids = [item['contentDetails']['videoId'] for item in playlist_response['items']]
                
                if video_ids:
                    videos = self.directory.youtube_client.get_video_details(video_ids)
                    
                    with SessionLocal() as session:
                        for video_data in videos:
                            try:
                                self.directory._upsert_video(session, video_data)
                                session.commit()
                                videos_collected += 1
                            except Exception as e:
                                session.rollback()
                                logger.error(f"Error saving video: {e}")
                
                next_page_token = playlist_response.get('nextPageToken')
                if not next_page_token:
                    break
                    
            logger.info(f"Collected {videos_collected} videos from {channel_info['snippet']['title']}")
            
        except Exception as e:
            logger.error(f"Error collecting channel {channel_id}: {e}")
    
    def discover_channels_from_videos(self):
        """Find new channels from featured/recommended videos."""
        logger.info("Discovering new channels from existing videos...")
        
        with SessionLocal() as session:
            # Get channels with most views that we haven't fully explored
            top_channels = session.query(
                YouTubeChannel.id,
                YouTubeChannel.title,
                func.sum(YouTubeVideo.view_count).label('total_views'),
                func.count(YouTubeVideo.id).label('video_count')
            ).join(
                YouTubeVideo
            ).group_by(
                YouTubeChannel.id, YouTubeChannel.title
            ).having(
                func.count(YouTubeVideo.id) < 10  # Channels with few videos collected
            ).order_by(
                func.sum(YouTubeVideo.view_count).desc()
            ).limit(10).all()
            
            for channel in top_channels:
                if channel.video_count < 10:
                    logger.info(f"Expanding collection for {channel.title}")
                    self.collect_historical_channel_data(channel.id, max_videos=25)
    
    def find_trending_by_velocity(self):
        """Find videos with high view velocity (views per day)."""
        logger.info("Finding trending videos by velocity...")
        
        # Search for recent videos with time filters
        time_ranges = [
            (1, "golf highlights today"),
            (7, "golf this week"),
            (30, "golf viral recent")
        ]
        
        for days, query in time_ranges:
            published_after = datetime.now(timezone.utc) - timedelta(days=days)
            videos = self.directory.youtube_client.search_golf_videos(
                query=query,
                max_results=25,
                order="viewCount",
                published_after=published_after
            )
            
            with SessionLocal() as session:
                for video_data in videos:
                    try:
                        self.directory._upsert_video(session, video_data)
                        session.commit()
                    except Exception as e:
                        session.rollback()
    
    def collect_tournament_content(self):
        """Collect content from major tournaments."""
        logger.info("Collecting tournament content...")
        
        # Current year tournaments
        year = datetime.now().year
        tournaments = [
            f"Masters {year}",
            f"US Open golf {year}",
            f"British Open {year}",
            f"PGA Championship {year}",
            f"Ryder Cup",
            "LIV Golf highlights",
            "PGA Tour highlights this week"
        ]
        
        for tournament in tournaments:
            videos = self.directory.youtube_client.search_golf_videos(
                query=tournament,
                max_results=20,
                order="viewCount"
            )
            
            with SessionLocal() as session:
                for video_data in videos:
                    try:
                        self.directory._upsert_video(session, video_data)
                        session.commit()
                    except Exception as e:
                        session.rollback()
    
    def expand_channel_list(self):
        """Expanded list of golf channels to track."""
        channels = {
            # Major Golf YouTubers
            "UCq-Rqdgna3OJxPg3aBt3c3Q": "Rick Shiels Golf",
            "UCfi-mPMOmche6WI-jkvnGXw": "Good Good",
            "UC9ywmLLYtiWKC0nHPWA_53g": "GM Golf",
            "UCDnv_1DzQGaHCPz6Jc6cfjQ": "TXG - Tour Experience Golf",
            "UCVZMKsVxmgYpgtfcbkq1mZg": "Peter Finch Golf",
            "UCZelGnfKLXic4gDP8xfwXKg": "Golf Sidekick",
            "UCaioJ73g8HlZ8d3apaiCMxg": "Micah Morris Golf",
            "UC0QLmupAq9GktezSAk_oVCw": "Bryan Bros Golf",
            "UCgUueMmSpcl-aCTt5CuCKQw": "Grant Horvat Golf",
            "UCl4Z0A7wt0aw-gHPcPXBxKA": "Luke Kwon Golf",
            
            # Instruction Focused
            "UCXPXrE2M8jmr1kUGQ0vuPEw": "Danny Maude",
            "UCQd_qgUk2olgFhH3RXvYmhg": "Me and My Golf",
            "UCbQQKqbwJp3N_m7LwmJzYrw": "Clay Ballard - Top Speed Golf",
            "UC9FgOZOz1vRGJCaReNQXKmA": "Athletic Motion Golf",
            "UCAE0t7yWXUgXyKC3w5VeHKw": "Chris Ryan Golf",
            
            # Tour/Professional
            "UCKwGZZMrhNYKzucCtTPY2Nw": "PGA TOUR",
            "UCRBxbDlh5-1-9mXz1Dd7UCA": "DP World Tour",
            "UCxu1btBKsH-iGJmqN3hf1Gw": "USGA",
            "UC7TqDvBSuz9e_dKOaNGauJQ": "The Open",
            
            # Entertainment/Vlog Style
            "UCaS8PbJ4skMeqsNJN7xAQmg": "Foreplay Golf",
            "UCHmAKsNPQ1FdJ0hQ4WhZMPQ": "No Laying Up",
            "UC2Xqy5e1NjdGNwTjmXTLkuA": "Random Golf Club",
            "UCW21y7vjvMOJEGQzTK3MXQA": "Golf Life TV",
            
            # Rising/Newer Channels
            "UC79Zncey_Jlk": "George Bryan",
            "UCCHuiIcQ24gAyqJJa4fcJFA": "Divot Dudes",
            "UCUOqlmPAo8h4pVQ4cuRECUg": "Big Wedge Golf",
        }
        
        for channel_id, name in channels.items():
            logger.info(f"Collecting from {name}")
            self.collect_historical_channel_data(channel_id, max_videos=30)
    
    def run_expanded_collection(self):
        """Run comprehensive data collection."""
        logger.info("=== Starting Expanded Collection ===")
        
        # 1. Collect from expanded channel list
        self.expand_channel_list()
        
        # 2. Find trending content
        self.find_trending_by_velocity()
        
        # 3. Collect tournament content
        self.collect_tournament_content()
        
        # 4. Discover new channels
        self.discover_channels_from_videos()
        
        # 5. Update rankings
        self.directory.update_rankings()
        
        logger.info("=== Expanded Collection Complete ===")


def collect_all_historical():
    """One-time historical collection."""
    collector = ExpandedGolfCollector()
    collector.run_expanded_collection()


if __name__ == "__main__":
    collect_all_historical()