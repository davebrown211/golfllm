"""
YouTube Golf Data Collector
Automated system for collecting and updating golf video metadata
"""

import os
import time
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy import create_engine, text
from youtube_analyzer.app.golf_directory import GolfDirectory
from youtube_analyzer.app.models import Base
import schedule
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_collection.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class GolfDataCollector:
    def __init__(self):
        self.directory = GolfDirectory()  # Uses PostgreSQL
        self.api_quota_used = 0
        self.daily_quota_limit = 10000  # YouTube API daily quota
        
    def collect_trending_videos(self):
        """Collect currently trending golf videos."""
        logger.info("Starting trending video collection...")
        
        trending_queries = [
            "golf",  # General golf content
            "PGA tour " + datetime.now().strftime("%Y %B"),  # Current month tour content
            "golf viral",  # Viral golf content
            "golf course vlog",  # Popular vlog format
            "golf tips",  # Instructional content
        ]
        
        for query in trending_queries:
            if self.api_quota_used >= self.daily_quota_limit - 100:
                logger.warning("Approaching daily API quota limit, stopping collection")
                break
                
            try:
                # Search costs 100 quota units
                videos = self.directory.youtube_client.search_golf_videos(
                    query=query,
                    max_results=50,
                    order="viewCount",
                    published_after=datetime.now() - timedelta(days=7)
                )
                self.api_quota_used += 100
                
                logger.info(f"Found {len(videos)} videos for query: {query}")
                
                # Save to database
                with self.directory.SessionLocal() as session:
                    for video_data in videos:
                        self.directory._upsert_video(session, video_data)
                    session.commit()
                    
            except Exception as e:
                logger.error(f"Error collecting videos for {query}: {str(e)}")
                
        logger.info(f"Trending collection complete. Quota used: {self.api_quota_used}")
    
    def collect_channel_videos(self, channel_ids: List[str] = None):
        """Collect latest videos from top golf channels."""
        logger.info("Starting channel video collection...")
        
        if channel_ids is None:
            # Default top golf channels to track
            channel_ids = [
                "UCq-Rqdgna3OJxPg3aBt3c3Q",  # Rick Shiels Golf
                "UCfi6B7SX9R3mZPuEHTgmeow",  # Good Good
                "UC9ywmLLYtiWKC0nHPWA_53g",  # GM Golf
                "UCDnv_1DzQGaHCPz6Jc6cfjQ",  # TXG
                "UCVZMKsVxmgYpgtfcbkq1mZg",  # Peter Finch Golf
                "UCZelGnfKLXic4gDP8xfwXKg",  # Golf Sidekick
                "UCaioJ73g8HlZ8d3apaiCMxg",  # Micah Morris Golf
                "UC0QLmupAq9GktezSAk_oVCw",  # Bryan Bros Golf
                "UC3jFoA7_6BTV90hsRSVHoaw",  # Phil Mickelson and the HyFlyers
            ]
        
        for channel_id in channel_ids:
            if self.api_quota_used >= self.daily_quota_limit - 100:
                logger.warning("Approaching daily API quota limit, stopping collection")
                break
                
            try:
                # Get channel's latest videos
                search_params = {
                    'part': 'snippet',
                    'channelId': channel_id,
                    'type': 'video',
                    'maxResults': 10,
                    'order': 'date'
                }
                
                response = self.directory.youtube_client.youtube.search().list(**search_params).execute()
                self.api_quota_used += 100
                
                video_ids = [item['id']['videoId'] for item in response['items']]
                if video_ids:
                    videos = self.directory.youtube_client.get_video_details(video_ids)
                    self.api_quota_used += len(video_ids)  # 1 unit per video
                    
                    # Save to database
                    with self.directory.SessionLocal() as session:
                        for video_data in videos:
                            self.directory._upsert_video(session, video_data)
                        session.commit()
                    
                    logger.info(f"Collected {len(videos)} videos from channel {channel_id}")
                    
            except Exception as e:
                logger.error(f"Error collecting videos for channel {channel_id}: {str(e)}")
    
    def collect_by_category(self):
        """Collect videos for specific golf categories."""
        logger.info("Starting category-based collection...")
        
        category_queries = {
            'instruction': [
                'golf swing basics',
                'putting tips',
                'golf chipping technique',
                'how to hit driver',
                'golf course management'
            ],
            'equipment': [
                'golf club review 2024',
                'best golf balls',
                'golf rangefinder review',
                'new golf drivers'
            ],
            'tour': [
                'PGA tour highlights',
                'Masters tournament',
                'US Open golf',
                'British Open'
            ]
        }
        
        for category, queries in category_queries.items():
            for query in queries:
                if self.api_quota_used >= self.daily_quota_limit - 100:
                    logger.warning("Approaching daily API quota limit, stopping collection")
                    return
                    
                try:
                    videos = self.directory.youtube_client.search_golf_videos(
                        query=query,
                        max_results=25
                    )
                    self.api_quota_used += 100
                    
                    # Save with category
                    with self.directory.SessionLocal() as session:
                        for video_data in videos:
                            self.directory._upsert_video(session, video_data)
                        session.commit()
                    
                    logger.info(f"Collected {len(videos)} videos for {category}: {query}")
                    
                except Exception as e:
                    logger.error(f"Error collecting {category} videos: {str(e)}")
    
    def update_existing_videos(self):
        """Update statistics for existing videos in database."""
        logger.info("Updating existing video statistics...")
        
        with self.directory.SessionLocal() as session:
            # Get videos that haven't been updated in 24 hours
            cutoff = datetime.now() - timedelta(hours=24)
            stale_videos = session.execute(
                text("SELECT id FROM youtube_videos WHERE updated_at < :cutoff ORDER BY view_count DESC LIMIT 50"),
                {"cutoff": cutoff}
            ).fetchall()
            
            video_ids = [row[0] for row in stale_videos]
            
            if video_ids:
                # Batch update (max 50 videos per request)
                for i in range(0, len(video_ids), 50):
                    batch = video_ids[i:i+50]
                    try:
                        videos = self.directory.youtube_client.get_video_details(batch)
                        self.api_quota_used += len(batch)
                        
                        for video_data in videos:
                            self.directory._upsert_video(session, video_data)
                        
                        session.commit()
                        logger.info(f"Updated {len(videos)} existing videos")
                        
                    except Exception as e:
                        logger.error(f"Error updating videos: {str(e)}")
    
    def run_daily_collection(self):
        """Run a complete daily collection cycle."""
        logger.info("=== Starting daily collection cycle ===")
        self.api_quota_used = 0
        
        # 1. Collect trending videos
        self.collect_trending_videos()
        
        # 2. Update top channels
        self.collect_channel_videos()
        
        # 3. Collect by category
        self.collect_by_category()
        
        # 4. Update existing videos
        self.update_existing_videos()
        
        # 5. Update rankings
        logger.info("Updating rankings...")
        self.directory.update_rankings()
        
        # 6. Log statistics
        self.log_collection_stats()
        
        logger.info(f"=== Daily collection complete. Total quota used: {self.api_quota_used}/10000 ===")
    
    def log_collection_stats(self):
        """Log collection statistics."""
        with self.directory.SessionLocal() as session:
            stats = {
                'total_videos': session.execute(text("SELECT COUNT(*) FROM youtube_videos")).scalar(),
                'total_channels': session.execute(text("SELECT COUNT(*) FROM youtube_channels")).scalar(),
                'videos_today': session.execute(
                    text("SELECT COUNT(*) FROM youtube_videos WHERE DATE(discovered_at) = DATE('now')")
                ).scalar(),
                'api_quota_used': self.api_quota_used,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Collection stats: {json.dumps(stats, indent=2)}")
            
            # Save stats to file
            with open('collection_stats.json', 'w') as f:
                json.dump(stats, f, indent=2)


def setup_scheduled_collection():
    """Set up scheduled data collection jobs."""
    collector = GolfDataCollector()
    
    # Schedule daily collection at 2 AM
    schedule.every().day.at("02:00").do(collector.run_daily_collection)
    
    # Schedule trending updates every 6 hours
    schedule.every(6).hours.do(collector.collect_trending_videos)
    
    logger.info("Scheduled jobs set up. Running scheduler...")
    
    # Run once immediately
    collector.run_daily_collection()
    
    # Keep running scheduled jobs
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute


def run_initial_collection():
    """Run an initial data collection to populate the database."""
    collector = GolfDataCollector()
    
    print("=== INITIAL DATA COLLECTION ===")
    print("This will populate your database with golf video data.")
    print(f"API Key: {'✓ Found' if collector.directory.youtube_client else '✗ Not found'}")
    
    if not collector.directory.youtube_client:
        print("\nERROR: No API key found. Please set GOOGLE_API_KEY in .env file")
        return
    
    print("\nStarting collection...")
    collector.run_daily_collection()
    
    print("\n✓ Initial collection complete!")
    print("You can now:")
    print("1. Run the API: uvicorn youtube_analyzer.app.directory_api:app --reload")
    print("2. Schedule automatic updates: python -m youtube_analyzer.app.data_collector --schedule")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--schedule":
        setup_scheduled_collection()
    else:
        run_initial_collection()