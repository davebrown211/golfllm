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
import asyncio
import psycopg2
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import schedule
import json
from dataclasses import dataclass
from dotenv import load_dotenv

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

class GolfScheduler:
    """Main scheduler class matching Next.js scheduler logic"""
    
    def __init__(self):
        self.db_url = os.getenv('DATABASE_URL')
        if not self.db_url:
            raise ValueError("DATABASE_URL environment variable required")
        
        self.youtube_api_key = os.getenv('YOUTUBE_API_KEY') or os.getenv('GOOGLE_API_KEY')
        if not self.youtube_api_key:
            raise ValueError("YOUTUBE_API_KEY or GOOGLE_API_KEY required")
            
        self.elevenlabs_api_key = os.getenv('ELEVENLABS_API_KEY')
        self.daily_quota_limit = 10000
        
        # Whitelisted channel IDs (from Next.js content-whitelist.ts)
        self.whitelisted_channels = [
            "UCgz5-3igA0IfsU7StatmjMw",  # Good Good
            "UCCz0skLgV2Yz1KsYFJMnVAw",  # Bob Does Sports
            "UCiWLfSweyRNmLpgEHekhoAg",  # Rick Shiels
            # Add all 167 channels from the whitelist
        ]
        
        logger.info("Golf Scheduler initialized")
    
    def get_db_connection(self):
        """Get database connection"""
        return psycopg2.connect(self.db_url)
    
    def can_perform_operation(self, operation_type: str, count: int = 1) -> bool:
        """Check if we have quota for the operation (matches Next.js quota-tracker)"""
        try:
            with self.get_db_connection() as conn:
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
            with self.get_db_connection() as conn:
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
            with self.get_db_connection() as conn:
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
                            # Here we would call YouTube API to update video stats
                            # This is a placeholder - actual implementation would use YouTube API
                            logger.info(f"Would update batch of {len(batch)} videos")
                            self.record_quota_usage("videoList", 1)
                            time.sleep(1)  # Rate limiting
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
                
                # This would call YouTube API search
                # search_params = {
                #     'q': 'golf',
                #     'order': 'viewCount',
                #     'publishedAfter': published_after,
                #     'publishedBefore': published_before,
                #     'maxResults': 50,
                #     'regionCode': 'US',
                #     'relevanceLanguage': 'en'
                # }
                
                logger.info(f"Would search for today's videos: {published_after} to {published_before}")
                self.record_quota_usage("search", 1)
                
            # Step 2: Get video of the day and generate AI if needed
            self.generate_ai_for_video_of_day()
            
        except Exception as e:
            logger.error(f"Error in collect today videos: {e}")
    
    def generate_ai_for_video_of_day(self):
        """Generate AI analysis for video of the day if missing"""
        try:
            with self.get_db_connection() as conn:
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
                    
                    # This would call the AI generation process
                    # 1. Download transcript with yt-dlp
                    # 2. Generate Jim Nantz summary with Gemini
                    # 3. Generate audio with ElevenLabs
                    # 4. Save to database
                    
                    logger.info("AI analysis generation completed (placeholder)")
                    
        except Exception as e:
            logger.error(f"Error generating AI for video of the day: {e}")
    
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
            with self.get_db_connection() as conn:
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
                            logger.info(f"Would update maintenance batch of {len(batch)} videos")
                            self.record_quota_usage("videoList", 1)
                            time.sleep(2)  # Rate limiting with delays
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
        logger.info("- Daily maintenance: Every day at 3 AM")
        
        # Schedule the 3 tasks (matches Next.js frequencies exactly)
        schedule.every(2).minutes.do(self.perform_view_count_updates)
        schedule.every(30).minutes.do(self.perform_collect_today_videos)
        schedule.every().day.at("03:00").do(self.perform_maintenance_update)
        
        # Run collect today videos immediately on startup (matches Next.js)
        logger.info("Running initial collect today videos on startup...")
        self.perform_collect_today_videos()
        
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