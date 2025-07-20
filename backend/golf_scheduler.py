#!/usr/bin/env python3
"""
Golf Directory Scheduler - Python Implementation
Matches the refined Next.js scheduler logic exactly

Three main tasks:
1. View count updates (every 2 minutes) - Smart user-facing video selection
2. Today collection + AI (every 30 minutes) - Today's videos + AI analysis
3. Daily maintenance (3 AM) - Older popular video updates
"""

import os
import sys
import time
import logging
import psycopg2
import psycopg2.extras
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import schedule
import json
from dataclasses import dataclass
from dotenv import load_dotenv

# Local imports
from youtube_client import YouTubeClient
from ai_processor import AIProcessor

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('golf_scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class QuotaUsage:
    """Track YouTube API quota usage"""
    date: str
    search_operations: int = 0
    video_list_operations: int = 0
    channel_list_operations: int = 0
    
    @property
    def total_units(self) -> int:
        return (self.search_operations * 100 + 
                self.video_list_operations * 1 + 
                self.channel_list_operations * 1)

class DatabaseManager:
    """Database operations manager"""
    
    def __init__(self, db_url: str):
        self.db_url = db_url
    
    def get_connection(self):
        """Get database connection"""
        return psycopg2.connect(self.db_url)
    
    def upsert_video(self, conn, video_data: Dict[str, Any]):
        """Upsert video data (matches Next.js video-service logic)"""
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO youtube_videos (
                    id, title, description, channel_id, published_at, 
                    view_count, like_count, comment_count, engagement_rate,
                    duration_seconds, thumbnail_url, updated_at
                ) VALUES (
                    %(id)s, %(title)s, %(description)s, %(channel_id)s, %(published_at)s,
                    %(view_count)s, %(like_count)s, %(comment_count)s, %(engagement_rate)s,
                    %(duration_seconds)s, %(thumbnail_url)s, NOW()
                )
                ON CONFLICT (id) DO UPDATE SET
                    view_count = EXCLUDED.view_count,
                    like_count = EXCLUDED.like_count,
                    comment_count = EXCLUDED.comment_count,
                    engagement_rate = EXCLUDED.engagement_rate,
                    updated_at = NOW()
            """, video_data)
    
    def upsert_channel(self, conn, channel_data: Dict[str, Any]):
        """Upsert channel data"""
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO youtube_channels (
                    id, title, description, subscriber_count, 
                    video_count, view_count, thumbnail_url, updated_at
                ) VALUES (
                    %(id)s, %(title)s, %(description)s, %(subscriber_count)s,
                    %(video_count)s, %(view_count)s, %(thumbnail_url)s, NOW()
                )
                ON CONFLICT (id) DO UPDATE SET
                    subscriber_count = EXCLUDED.subscriber_count,
                    video_count = EXCLUDED.video_count,
                    view_count = EXCLUDED.view_count,
                    updated_at = NOW()
            """, channel_data)
    
    def save_video_analysis(self, conn, video_id: str, summary: str, audio_url: Optional[str] = None):
        """Save AI analysis results"""
        with conn.cursor() as cur:
            youtube_url = f"https://youtube.com/watch?v={video_id}"
            # Format result as JSON object that frontend expects
            result_json = json.dumps({
                "summary": summary,
                "source": "transcript_analysis", 
                "generated_at": datetime.utcnow().isoformat()
            })
            cur.execute("""
                INSERT INTO video_analyses (video_id, youtube_url, summary, audio_url, status, result, created_at)
                VALUES (%s, %s, %s, %s, 'COMPLETED', %s, NOW())
                ON CONFLICT (video_id) DO UPDATE SET
                    youtube_url = EXCLUDED.youtube_url,
                    summary = EXCLUDED.summary,
                    audio_url = EXCLUDED.audio_url,
                    status = 'COMPLETED',
                    result = EXCLUDED.result,
                    created_at = NOW()
            """, (video_id, youtube_url, summary, audio_url, result_json))

class GolfScheduler:
    """Main scheduler class matching Next.js scheduler logic"""
    
    def __init__(self):
        self.db_url = os.getenv('DATABASE_URL')
        if not self.db_url:
            raise ValueError("DATABASE_URL environment variable required")
        
        youtube_api_key = os.getenv('YOUTUBE_API_KEY') or os.getenv('GOOGLE_API_KEY')
        if not youtube_api_key:
            raise ValueError("YOUTUBE_API_KEY or GOOGLE_API_KEY required")
        
        google_api_key = os.getenv('GOOGLE_API_KEY')
        elevenlabs_api_key = os.getenv('ELEVENLABS_API_KEY')
        
        # Initialize components
        self.youtube_client = YouTubeClient(youtube_api_key)
        self.ai_processor = AIProcessor(google_api_key, elevenlabs_api_key)
        self.db_manager = DatabaseManager(self.db_url)
        self.daily_quota_limit = 10000
        
        # Whitelisted channel IDs (from Next.js content-whitelist.ts)
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
        
        logger.info("Golf Scheduler initialized")
    
    def can_perform_operation(self, operation_type: str, count: int = 1) -> bool:
        """Check if we have quota for the operation (matches Next.js quota-tracker)"""
        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    today = datetime.now().strftime('%Y-%m-%d')
                    
                    # Get today's quota usage
                    cur.execute("""
                        SELECT search_operations, video_list_operations, channel_list_operations
                        FROM api_quota_usage 
                        WHERE date = %s
                    """, (today,))
                    
                    row = cur.fetchone()
                    if not row:
                        return True  # No usage today, can proceed
                    
                    search_ops, video_ops, channel_ops = row
                    current_total = search_ops * 100 + video_ops * 1 + channel_ops * 1
                    
                    # Calculate cost of this operation
                    costs = {"search": 100, "videoList": 1, "channelList": 1}
                    operation_cost = costs.get(operation_type, 1) * count
                    
                    return (current_total + operation_cost) <= self.daily_quota_limit
                    
        except Exception as e:
            logger.error(f"Error checking quota: {e}")
            return False
    
    def record_quota_usage(self, operation_type: str, count: int = 1):
        """Record quota usage (matches Next.js quota-tracker)"""
        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    today = datetime.now().strftime('%Y-%m-%d')
                    
                    # Upsert quota usage
                    if operation_type == "search":
                        cur.execute("""
                            INSERT INTO api_quota_usage (date, search_operations)
                            VALUES (%s, %s)
                            ON CONFLICT (date)
                            DO UPDATE SET search_operations = api_quota_usage.search_operations + %s
                        """, (today, count, count))
                    elif operation_type == "videoList":
                        cur.execute("""
                            INSERT INTO api_quota_usage (date, video_list_operations)
                            VALUES (%s, %s)
                            ON CONFLICT (date)
                            DO UPDATE SET video_list_operations = api_quota_usage.video_list_operations + %s
                        """, (today, count, count))
                    elif operation_type == "channelList":
                        cur.execute("""
                            INSERT INTO api_quota_usage (date, channel_list_operations)
                            VALUES (%s, %s)
                            ON CONFLICT (date)
                            DO UPDATE SET channel_list_operations = api_quota_usage.channel_list_operations + %s
                        """, (today, count, count))
                    
                    conn.commit()
                    
        except Exception as e:
            logger.error(f"Error recording quota usage: {e}")
    
    def perform_view_count_updates(self):
        """
        View count updates (every 2 minutes)
        Matches Next.js scheduler performViewCountUpdates() exactly
        """
        logger.info("Starting view count updates...")
        
        # Check quota first
        if not self.can_perform_operation("videoList", 2):  # Estimate 2 batches
            logger.warning("Insufficient quota for view count updates")
            return
        
        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    # Exact SQL from Next.js scheduler (matches user-facing video selection)
                    query = """
                    WITH user_facing_videos AS (
                        -- Curated videos (priority 1)
                        (SELECT yv.id, yv.updated_at, yv.published_at, yv.view_count, 1 as priority
                         FROM youtube_videos yv 
                         JOIN youtube_channels yc ON yv.channel_id = yc.id
                         WHERE yv.channel_id = ANY(%s::text[])
                           AND yv.published_at >= NOW() - INTERVAL '90 days'
                           AND yv.view_count > 100
                           AND yv.duration_seconds >= 180
                         ORDER BY yv.published_at DESC LIMIT 50)
                        
                        UNION ALL
                        
                        -- Video of day candidates (priority 2)  
                        (SELECT yv.id, yv.updated_at, yv.published_at, yv.view_count, 2 as priority
                         FROM youtube_videos yv
                         JOIN youtube_channels yc ON yv.channel_id = yc.id
                         WHERE yv.published_at >= NOW() - INTERVAL '14 days'
                           AND yv.view_count > 100
                           AND yv.channel_id = ANY(%s::text[])
                           AND yv.duration_seconds >= 60
                           AND yv.thumbnail_url IS NOT NULL
                         ORDER BY 
                           CASE 
                             WHEN yv.published_at >= NOW() - INTERVAL '1 day' THEN yv.view_count * 1000
                             WHEN yv.published_at >= NOW() - INTERVAL '2 days' THEN yv.view_count * 100  
                             WHEN yv.published_at >= NOW() - INTERVAL '3 days' THEN yv.view_count * 10
                             ELSE yv.view_count
                           END DESC
                         LIMIT 20)
                    )
                    SELECT id FROM user_facing_videos
                    WHERE updated_at <= NOW() - INTERVAL '10 minutes'
                       OR published_at >= NOW() - INTERVAL '12 hours'
                    ORDER BY priority, view_count DESC 
                    LIMIT 70
                    """
                    
                    cur.execute(query, (self.whitelisted_channels, self.whitelisted_channels))
                    video_ids = [row[0] for row in cur.fetchall()]
                    
                    if not video_ids:
                        logger.info("No videos need view count updates")
                        return
                    
                    logger.info(f"Updating view counts for {len(video_ids)} user-facing videos")
                    
                    # Update videos in batches of 50 (matches Next.js)
                    batch_size = 50
                    batches = [video_ids[i:i + batch_size] for i in range(0, len(video_ids), batch_size)]
                    
                    for batch in batches:
                        if self.can_perform_operation("videoList", 1):
                            # Get updated video stats from YouTube API
                            updated_videos = self.youtube_client.update_video_stats(batch)
                            
                            # Update database
                            for video_data in updated_videos:
                                self.db_manager.upsert_video(conn, video_data)
                            
                            conn.commit()
                            self.record_quota_usage("videoList", 1)
                            time.sleep(1)  # Rate limiting
                            
                            logger.info(f"Updated batch of {len(updated_videos)} videos")
                        else:
                            logger.warning("Quota exhausted, stopping view updates")
                            break
                    
                    logger.info("View count updates completed")
                    
        except Exception as e:
            logger.error(f"Error in view count updates: {e}")
    
    def perform_collect_today_videos(self):
        """
        Collect today videos + AI (every 30 minutes)
        Matches Next.js scheduler performCollectTodayVideos() exactly
        """
        logger.info("Starting collect today videos...")
        
        try:
            # Step 1: Collect today's videos (matches /api/collect-today-videos)
            if self.can_perform_operation("search", 1):
                logger.info("Collecting today's golf videos...")
                
                # Today's date range (UTC)
                today = datetime.utcnow().date()
                published_after = today.isoformat() + "T00:00:00Z"
                published_before = (today + timedelta(days=1)).isoformat() + "T00:00:00Z"
                
                # Search for today's golf videos
                videos = self.youtube_client.search_golf_videos(
                    query="golf",
                    published_after=published_after,
                    published_before=published_before,
                    max_results=50
                )
                
                if videos:
                    # Get video details for engagement rates
                    video_ids = [v['id'] for v in videos]
                    detailed_videos = self.youtube_client.update_video_stats(video_ids)
                    
                    # Get channel info
                    channel_ids = list(set([v['channel_id'] for v in detailed_videos]))
                    channels = self.youtube_client.get_channel_info(channel_ids)
                    
                    # Update database
                    with self.db_manager.get_connection() as conn:
                        # Upsert channels
                        for channel_data in channels:
                            self.db_manager.upsert_channel(conn, channel_data)
                        
                        # Upsert videos
                        for video_data in detailed_videos:
                            self.db_manager.upsert_video(conn, video_data)
                        
                        conn.commit()
                    
                    logger.info(f"Collected {len(detailed_videos)} today's videos")
                    self.record_quota_usage("search", 1)
                    self.record_quota_usage("videoList", len(video_ids) // 50 + 1)
                    self.record_quota_usage("channelList", len(channel_ids) // 50 + 1)
                
            # Step 2: Always check video of the day and generate AI if needed
            # This runs every 30 minutes to ensure we have AI summaries
            self.generate_ai_for_video_of_day()
            
        except Exception as e:
            logger.error(f"Error in collect today videos: {e}")
    
    def generate_ai_for_video_of_day(self):
        """Generate AI analysis for video of the day if missing"""
        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    # Get video of the day (matches momentum scoring from Next.js)
                    query = """
                    SELECT yv.id, yv.title
                    FROM youtube_videos yv
                    JOIN youtube_channels yc ON yv.channel_id = yc.id
                    WHERE yv.channel_id = ANY(%s::text[])
                      AND yv.view_count > 100
                      AND yv.duration_seconds >= 60
                      AND yv.thumbnail_url IS NOT NULL
                      AND yv.published_at >= NOW() - INTERVAL '14 days'
                    ORDER BY 
                      CASE 
                        WHEN yv.published_at >= NOW() - INTERVAL '1 day' THEN yv.view_count * 1000
                        WHEN yv.published_at >= NOW() - INTERVAL '2 days' THEN yv.view_count * 100
                        WHEN yv.published_at >= NOW() - INTERVAL '3 days' THEN yv.view_count * 10
                        ELSE yv.view_count
                      END DESC
                    LIMIT 1
                    """
                    
                    cur.execute(query, (self.whitelisted_channels,))
                    video_row = cur.fetchone()
                    
                    if not video_row:
                        logger.info("No video of the day candidate found")
                        return
                    
                    video_id, title = video_row
                    
                    # Check if AI analysis exists
                    cur.execute("""
                        SELECT id FROM video_analyses 
                        WHERE video_id = %s AND summary IS NOT NULL
                    """, (video_id,))
                    
                    if cur.fetchone():
                        logger.info("Video of the day already has AI analysis")
                        return
                    
                    logger.info(f"Generating AI analysis for video of the day: {title} ({video_id})")
                    
                    # Generate AI analysis
                    ai_result = self.ai_processor.generate_transcript_summary(video_id, title)
                    
                    if ai_result['summary']:
                        # Save to database (audio_url is just the filename)
                        self.db_manager.save_video_analysis(
                            conn, video_id, ai_result['summary'], ai_result.get('audio_url')
                        )
                        conn.commit()
                        logger.info("AI analysis saved successfully")
                    else:
                        logger.warning(f"AI analysis failed: {ai_result.get('error', 'Unknown error')}")
                    
        except Exception as e:
            logger.error(f"Error generating AI for video of the day: {e}")
    
    def perform_collect_whitelisted_videos(self):
        """
        Collect recent videos from whitelisted channels (every hour)
        Similar to Next.js /api/collect-whitelisted-videos
        """
        logger.info("Starting whitelisted channel collection...")
        
        try:
            if self.can_perform_operation("channelList", 2):
                # Get recent videos from whitelisted channels
                collected_count = 0
                days_back = 7  # Look for videos from past week
                max_videos_per_channel = 5
                
                for channel_id in self.whitelisted_channels:
                    try:
                        # Get channel's upload playlist
                        channel_videos = self.youtube_client.get_channel_recent_videos(
                            channel_id=channel_id,
                            max_results=max_videos_per_channel,
                            days_back=days_back
                        )
                        
                        if channel_videos:
                            # Get detailed stats for videos
                            video_ids = [v['id'] for v in channel_videos]
                            detailed_videos = self.youtube_client.update_video_stats(video_ids)
                            
                            # Upsert videos to database
                            with self.db_manager.get_connection() as conn:
                                for video in detailed_videos:
                                    self.db_manager.upsert_video(conn, video)
                                    collected_count += 1
                            
                            logger.info(f"Collected {len(detailed_videos)} videos from channel {channel_id}")
                    
                    except Exception as e:
                        logger.error(f"Error collecting from channel {channel_id}: {e}")
                        continue
                
                logger.info(f"Whitelisted collection completed: {collected_count} videos collected")
                
            else:
                logger.warning("Insufficient quota for whitelisted channel collection")
                
        except Exception as e:
            logger.error(f"Error in whitelisted collection: {e}")
    
    def perform_maintenance_update(self):
        """
        Daily maintenance (3 AM)
        Matches Next.js scheduler performMaintenanceUpdate() exactly
        """
        logger.info("Starting daily maintenance update...")
        
        if not self.can_perform_operation("videoList", 2):  # Estimate 2 batches
            logger.warning("Insufficient quota for maintenance update")
            return
        
        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    # Exact SQL from Next.js scheduler
                    query = """
                    SELECT yv.id FROM youtube_videos yv
                    JOIN youtube_channels yc ON yv.channel_id = yc.id  
                    WHERE yv.channel_id = ANY(%s::text[])
                      AND yv.published_at < NOW() - INTERVAL '90 days'
                      AND yv.view_count > 500000
                      AND yv.updated_at < NOW() - INTERVAL '7 days'
                    ORDER BY yv.view_count DESC 
                    LIMIT 100
                    """
                    
                    cur.execute(query, (self.whitelisted_channels,))
                    video_ids = [row[0] for row in cur.fetchall()]
                    
                    if not video_ids:
                        logger.info("No videos need maintenance updates")
                        return
                    
                    logger.info(f"Maintenance update for {len(video_ids)} older popular videos")
                    
                    # Process in batches of 50 (matches Next.js)
                    batch_size = 50
                    batches = [video_ids[i:i + batch_size] for i in range(0, len(video_ids), batch_size)]
                    
                    for batch in batches:
                        if self.can_perform_operation("videoList", 1):
                            # Get updated video stats
                            updated_videos = self.youtube_client.update_video_stats(batch)
                            
                            # Update database
                            for video_data in updated_videos:
                                self.db_manager.upsert_video(conn, video_data)
                            
                            conn.commit()
                            self.record_quota_usage("videoList", 1)
                            time.sleep(2)  # Rate limiting with delays
                            
                            logger.info(f"Updated maintenance batch of {len(updated_videos)} videos")
                        else:
                            logger.warning("Quota exhausted, stopping maintenance")
                            break
                    
                    logger.info("Daily maintenance completed")
                    
        except Exception as e:
            logger.error(f"Error in maintenance update: {e}")
    
    def start_scheduler(self):
        """Start the scheduler with the 3 refined tasks"""
        logger.info("Starting Golf Directory Python Scheduler")
        logger.info("Tasks:")
        logger.info("- View count updates: Every 2 minutes")
        logger.info("- Collect today videos + AI: Every 30 minutes")
        logger.info("- Collect whitelisted channels: Every 30 minutes")
        logger.info("- Daily maintenance: Every day at 3 AM")
        
        # Schedule the 4 tasks (matches Next.js frequencies exactly)
        schedule.every(2).minutes.do(self.perform_view_count_updates)
        schedule.every(30).minutes.do(self.perform_collect_today_videos)
        schedule.every(30).minutes.do(self.perform_collect_whitelisted_videos)  # Every 30 minutes
        schedule.every().day.at("03:00").do(self.perform_maintenance_update)
        
        # Run initial collections on startup
        logger.info("Running initial collections on startup...")
        self.perform_collect_today_videos()
        self.perform_collect_whitelisted_videos()
        
        # Main scheduler loop
        logger.info("Scheduler started. Press Ctrl+C to stop.")
        try:
            while True:
                schedule.run_pending()
                time.sleep(10)  # Check every 10 seconds
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")

if __name__ == "__main__":
    try:
        scheduler = GolfScheduler()
        scheduler.start_scheduler()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)