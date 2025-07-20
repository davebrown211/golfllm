#!/usr/bin/env python3
"""
Add YouTube metadata tables to existing PostgreSQL database.
"""

from youtube_analyzer.app.database import engine, Base
from youtube_analyzer.app.models import (
    VideoAnalysis, Character, CharacterAppearance,
    YouTubeChannel, YouTubeVideo, VideoRanking, SearchQuery
)
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_database():
    """Add new YouTube metadata tables to existing database."""
    
    logger.info("Starting database migration...")
    
    try:
        # Create all tables (will skip existing ones)
        Base.metadata.create_all(bind=engine)
        logger.info("✓ YouTube metadata tables created successfully")
        
        # Check what tables exist
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        logger.info("\nTables in database:")
        for table in sorted(tables):
            logger.info(f"  • {table}")
        
        # Verify new tables
        required_tables = ['youtube_channels', 'youtube_videos', 'video_rankings', 'search_queries']
        missing = [t for t in required_tables if t not in tables]
        
        if missing:
            logger.error(f"Missing tables: {missing}")
        else:
            logger.info("\n✓ All YouTube metadata tables verified!")
            logger.info("\nYou can now start collecting YouTube metadata:")
            logger.info("  python -m youtube_analyzer.app.data_collector")
            
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        raise


if __name__ == "__main__":
    migrate_database()