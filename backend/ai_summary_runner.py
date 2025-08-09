#!/usr/bin/env python3
"""
AI Summary Runner - Standalone script to generate AI summaries for videos
Runs independently from the main scheduler to ensure AI generation happens reliably
"""

import os
import sys
import logging
import psycopg2
import psycopg2.extras
from datetime import datetime, timedelta
from dotenv import load_dotenv
from ai_processor import AIProcessor
import time

# Import the whitelist
from golf_whitelist import WHITELISTED_CHANNELS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class AISummaryRunner:
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL')
        google_api_key = os.getenv('GOOGLE_API_KEY')
        elevenlabs_api_key = os.getenv('ELEVENLABS_API_KEY')
        
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable is required")
        
        self.ai_processor = AIProcessor(google_api_key, elevenlabs_api_key)
        
        # Load whitelisted channel IDs (filter out handles)
        self.whitelisted_channel_ids = set()
        
        for channel in WHITELISTED_CHANNELS:
            if isinstance(channel, str) and not channel.startswith('@'):
                self.whitelisted_channel_ids.add(channel)
        
        logger.info(f"Loaded {len(self.whitelisted_channel_ids)} whitelisted channel IDs")
        
    def get_videos_needing_ai(self, limit=10):
        """Get videos that need AI summaries generated"""
        try:
            with psycopg2.connect(self.database_url) as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                    query = """
                    SELECT 
                        yv.id as video_id,
                        yv.title,
                        yc.title as channel,
                        yv.channel_id
                    FROM youtube_videos yv
                    JOIN youtube_channels yc ON yv.channel_id = yc.id
                    LEFT JOIN video_analyses va ON va.youtube_url LIKE '%%' || yv.id || '%%'
                    WHERE yv.published_at >= NOW() - INTERVAL '7 days'  -- Recent videos
                        AND yv.view_count > 1000  -- Some engagement
                        AND (yv.duration_seconds IS NULL OR yv.duration_seconds >= 120)  -- Not shorts
                        AND yv.thumbnail_url IS NOT NULL
                        AND (va.id IS NULL OR va.status != 'COMPLETED')  -- No completed analysis
                    ORDER BY yv.view_count DESC
                    LIMIT %s
                    """
                    
                    cur.execute(query, (limit * 3,))  # Get more to filter by whitelist
                    videos = cur.fetchall()
                    
                    # Filter by whitelist
                    whitelisted_videos = []
                    for video in videos:
                        if video['channel_id'] in self.whitelisted_channel_ids:
                            whitelisted_videos.append(video)
                            if len(whitelisted_videos) >= limit:
                                break
                    
                    return whitelisted_videos
                    
        except Exception as e:
            logger.error(f"Error getting videos needing AI: {e}", exc_info=True)
            return []
    
    def generate_ai_for_video(self, video_id, title):
        """Generate AI summary and audio for a single video"""
        try:
            logger.info(f"Generating AI for: {title} ({video_id})")
            
            # Generate transcript summary and audio
            ai_result = self.ai_processor.generate_transcript_summary(video_id, title)
            
            if ai_result.get('summary'):
                logger.info(f"Successfully generated AI summary for {video_id}")
                logger.info(f"Summary preview: {ai_result['summary'][:100]}...")
                if ai_result.get('audio_url'):
                    logger.info(f"Audio generated: {ai_result['audio_url']}")
                
                # Save to database
                self.save_ai_result(video_id, ai_result)
                return True
            else:
                logger.warning(f"Failed to generate AI summary for {video_id}: {ai_result.get('error')}")
                return False
                
        except Exception as e:
            logger.error(f"Error generating AI for video {video_id}: {e}", exc_info=True)
            return False
    
    def save_ai_result(self, video_id, ai_result):
        """Save AI analysis result to database"""
        try:
            with psycopg2.connect(self.database_url) as conn:
                with conn.cursor() as cur:
                    # Check if analysis exists
                    cur.execute("""
                        SELECT id FROM video_analyses 
                        WHERE youtube_url LIKE %s
                    """, (f"%{video_id}%",))
                    
                    existing = cur.fetchone()
                    
                    if existing:
                        # Update existing
                        cur.execute("""
                            UPDATE video_analyses
                            SET result = %s,
                                audio_url = %s,
                                status = 'COMPLETED',
                                updated_at = NOW()
                            WHERE youtube_url LIKE %s
                        """, (ai_result['summary'], ai_result.get('audio_url'), f"%{video_id}%"))
                    else:
                        # Insert new
                        cur.execute("""
                            INSERT INTO video_analyses (youtube_url, result, audio_url, status, created_at, updated_at)
                            VALUES (%s, %s, %s, 'COMPLETED', NOW(), NOW())
                        """, (f"https://youtube.com/watch?v={video_id}", ai_result['summary'], ai_result.get('audio_url')))
                    
                    conn.commit()
                    logger.info(f"Saved AI analysis for {video_id}")
                    
        except Exception as e:
            logger.error(f"Error saving AI result: {e}", exc_info=True)
    
    def run_once(self, max_videos=5):
        """Run AI generation for a batch of videos"""
        logger.info(f"Starting AI summary generation for up to {max_videos} videos...")
        
        videos = self.get_videos_needing_ai(max_videos)
        
        if not videos:
            logger.info("No videos found needing AI summaries")
            return 0
        
        logger.info(f"Found {len(videos)} videos needing AI summaries")
        
        successful = 0
        for video in videos:
            try:
                success = self.generate_ai_for_video(
                    video['video_id'],
                    video['title']
                )
                if success:
                    successful += 1
                
                # Small delay to avoid rate limiting
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Error processing video {video['video_id']}: {e}")
                continue
        
        logger.info(f"AI summary generation completed. Successfully processed {successful}/{len(videos)} videos")
        return successful
    
    def run_continuous(self, interval_minutes=30, max_videos_per_run=5):
        """Run continuously with specified interval"""
        logger.info(f"Starting continuous AI summary generation (every {interval_minutes} minutes)")
        
        while True:
            try:
                self.run_once(max_videos_per_run)
                
                # Wait for next run
                logger.info(f"Waiting {interval_minutes} minutes until next run...")
                time.sleep(interval_minutes * 60)
                
            except KeyboardInterrupt:
                logger.info("Stopping AI summary runner...")
                break
            except Exception as e:
                logger.error(f"Error in continuous run: {e}", exc_info=True)
                time.sleep(60)  # Wait a minute before retrying

if __name__ == "__main__":
    runner = AISummaryRunner()
    
    # Check command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        # Run once
        max_videos = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        runner.run_once(max_videos)
    else:
        # Run continuously (default)
        runner.run_continuous(interval_minutes=30, max_videos_per_run=5)