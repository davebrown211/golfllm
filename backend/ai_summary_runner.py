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

# Whitelist now handled via database JOINs - no imports needed

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
        
        logger.info("AI Summary Runner initialized with database-driven whitelist")
        
    def get_video_of_the_day_needing_ai(self):
        """Get current Video of the Day if it needs AI analysis"""
        try:
            # Load shared query 
            shared_query_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'shared', 'video-of-the-day-query.sql')
            with open(shared_query_path, 'r') as f:
                query = f.read().strip()
            
            with psycopg2.connect(self.database_url) as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                    cur.execute(query)
                    row = cur.fetchone()
                    
                    if not row:
                        logger.info("No Video of the Day found")
                        return []
                    
                    # Check if this video already has AI analysis
                    cur.execute("""
                        SELECT status FROM video_analyses 
                        WHERE youtube_url LIKE %s AND status = 'COMPLETED'
                    """, (f"%{row['video_id']}%",))
                    
                    existing = cur.fetchone()
                    if existing:
                        logger.info(f"Video of the Day already has completed AI analysis: {row['title']}")
                        return []
                    
                    # Return as list for compatibility with existing code
                    return [{
                        'video_id': row['video_id'],
                        'title': row['title'],
                        'channel': row['channel'],
                        'channel_id': None  # Not needed for AI processing
                    }]
                    
        except Exception as e:
            logger.error(f"Error getting Video of the Day: {e}", exc_info=True)
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
        """Run AI generation for Video of the Day if needed"""
        logger.info("Starting AI summary generation for Video of the Day...")
        
        videos = self.get_video_of_the_day_needing_ai()
        
        if not videos:
            logger.info("Video of the Day doesn't need AI analysis or no Video of the Day found")
            return 0
        
        logger.info(f"Video of the Day needs AI analysis: {videos[0]['title']}")
        
        successful = 0
        for video in videos:
            try:
                success = self.generate_ai_for_video(
                    video['video_id'],
                    video['title']
                )
                if success:
                    successful += 1
                
            except Exception as e:
                logger.error(f"Error processing Video of the Day {video['video_id']}: {e}")
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