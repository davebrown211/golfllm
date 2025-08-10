#!/usr/bin/env python3
"""
AI Video of the Day Runner - Generate AI summary and audio for the current video of the day only
"""

import os
import sys
import logging
import psycopg2
import psycopg2.extras
from datetime import datetime
from dotenv import load_dotenv
from ai_processor import AIProcessor
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class AIVideoOfDayRunner:
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL')
        google_api_key = os.getenv('GOOGLE_API_KEY')
        elevenlabs_api_key = os.getenv('ELEVENLABS_API_KEY')
        
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable is required")
        
        self.ai_processor = AIProcessor(google_api_key, elevenlabs_api_key)
        
    def get_current_video_of_day(self):
        """Get the current video of the day using the exact same shared query as frontend"""
        try:
            # Import shared query to ensure identical logic as frontend
            import sys
            sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'shared'))
            from video_of_the_day_query import get_video_of_the_day_query
            
            conn = psycopg2.connect(self.database_url)
            cur = conn.cursor()
            
            # Use the exact same shared query as frontend - no parameters needed!
            query = get_video_of_the_day_query()
            cur.execute(query)
            
            # Get column names and row data
            colnames = [desc[0] for desc in cur.description]
            row = cur.fetchone()
            
            cur.close()
            conn.close()
            
            if not row:
                logger.info("No video of the day found using shared query")
                return None
            
            # Convert row to dict
            video = dict(zip(colnames, row))
            
            logger.info(f"Selected video using shared query: {video['title']} by {video['channel']}")
            
            # Return in format expected by rest of code
            return {
                'video_id': video['video_id'],
                'title': video['title'],
                'channel': video['channel'],
                'has_ai_analysis': bool(video['ai_analysis']),
                'analysis_status': video['analysis_status']
            }
                    
        except Exception as e:
            logger.error(f"Error getting video of the day: {e}", exc_info=True)
            return None
    
    def generate_ai_for_video(self, video_id, title):
        """Generate AI summary and audio for a single video"""
        try:
            logger.info(f"Generating AI for Video of the Day: {title} ({video_id})")
            
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
                                status = 'COMPLETED'
                            WHERE youtube_url LIKE %s
                        """, (ai_result['summary'], ai_result.get('audio_url'), f"%{video_id}%"))
                    else:
                        # Insert new
                        cur.execute("""
                            INSERT INTO video_analyses (video_id, youtube_url, result, audio_url, status)
                            VALUES (%s, %s, %s, %s, 'COMPLETED')
                        """, (video_id, f"https://youtube.com/watch?v={video_id}", ai_result['summary'], ai_result.get('audio_url')))
                    
                    conn.commit()
                    logger.info(f"Saved AI analysis for {video_id}")
                    
        except Exception as e:
            logger.error(f"Error saving AI result: {e}", exc_info=True)
    
    def run(self):
        """Run AI generation for the video of the day"""
        logger.info("Starting AI generation for Video of the Day...")
        
        # Get current video of the day
        video = self.get_current_video_of_day()
        
        if not video:
            logger.info("No video of the day found for today")
            return False
        
        logger.info(f"Found Video of the Day: {video['title']} ({video['video_id']})")
        
        # Check if AI already exists
        if video['analysis_status'] == 'COMPLETED' and video.get('audio_url'):
            logger.info("Video of the Day already has completed AI analysis with audio")
            return True
        
        # Generate AI
        success = self.generate_ai_for_video(video['video_id'], video['title'])
        
        if success:
            logger.info("AI generation completed successfully for Video of the Day")
        else:
            logger.error("Failed to generate AI for Video of the Day")
        
        return success

if __name__ == "__main__":
    runner = AIVideoOfDayRunner()
    runner.run()