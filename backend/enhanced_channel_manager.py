#!/usr/bin/env python3
"""
Enhanced YouTube Channel Whitelist Manager for Golf Directory

Production-ready script for managing golf instruction channel whitelists with:
- Robust YouTube API integration with retry logic
- Database compatibility for multiple table schemas  
- Advanced channel filtering and validation
- Comprehensive error handling and logging
- Safe duplicate prevention and production deployment features

Usage:
    python enhanced_channel_manager.py [--config-file channels.txt] [--channel-type instructional]
    python enhanced_channel_manager.py --live-run  # For production execution
    python enhanced_channel_manager.py --validate-existing  # Audit existing channels
"""

import os
import sys
import json
import logging
import argparse
import time
import re
from typing import List, Dict, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError, Error
import backoff

# Enhanced logging configuration for production
def setup_logging(log_level: str = 'INFO', log_file: str = 'channel_manager.log') -> logging.Logger:
    """Set up comprehensive logging for production use"""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    
    # Create logger
    logger = logging.getLogger('channel_manager')
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers to prevent duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # File handler with rotation capability
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(log_format)
    file_handler.setFormatter(file_formatter)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

logger = setup_logging()

@dataclass
class ChannelSearchResult:
    """Enhanced data class for channel search and analysis results"""
    search_name: str
    channel_id: Optional[str] = None
    channel_title: Optional[str] = None
    channel_handle: Optional[str] = None
    subscriber_count: Optional[int] = None
    video_count: Optional[int] = None
    view_count: Optional[int] = None
    description: Optional[str] = None
    country: Optional[str] = None
    created_date: Optional[str] = None
    
    # Whitelist status
    is_whitelisted: bool = False
    whitelist_name: Optional[str] = None
    whitelist_channel_type: Optional[str] = None
    whitelist_table: Optional[str] = None
    
    # Analysis results
    golf_relevance_score: Optional[float] = None
    is_instructional: Optional[bool] = None
    is_golf_related: Optional[bool] = None
    confidence_level: str = "unknown"
    
    # Error handling
    error_message: Optional[str] = None
    warning_messages: List[str] = None
    multiple_results: Optional[List[Dict]] = None
    api_retries: int = 0
    
    def __post_init__(self):
        if self.warning_messages is None:
            self.warning_messages = []

class ProductionChannelManager:
    """Enhanced production-ready YouTube channel manager"""
    
    # Golf-related keywords for relevance scoring
    GOLF_KEYWORDS = {
        'high_relevance': ['golf', 'swing', 'putting', 'driver', 'iron', 'wedge', 'course', 'handicap', 'pga', 'tour'],
        'medium_relevance': ['sport', 'game', 'practice', 'tips', 'lesson', 'instruction', 'coach', 'pro'],
        'instruction_keywords': ['lesson', 'instruction', 'tips', 'tutorial', 'how to', 'improve', 'academy', 'coach', 'teaching']
    }
    
    def __init__(self, database_url: str, youtube_api_key: str, dry_run: bool = False, 
                 max_retries: int = 3, rate_limit_delay: float = 1.2):
        self.database_url = database_url
        self.youtube_api_key = youtube_api_key
        self.dry_run = dry_run
        self.max_retries = max_retries
        self.rate_limit_delay = rate_limit_delay
        self.youtube = None
        self.conn = None
        self.db_schema_info = {}
        
        if not dry_run:
            self._initialize_services()
        else:
            logger.info("🔄 Running in DRY-RUN mode - no actual API calls or database modifications")
    
    def _initialize_services(self):
        """Initialize YouTube API and database connections with error handling"""
        try:
            # Initialize YouTube API client
            self.youtube = build('youtube', 'v3', developerKey=self.youtube_api_key)
            logger.info("✅ YouTube API client initialized successfully")
            
            # Initialize database connection
            self.conn = psycopg2.connect(self.database_url)
            self.conn.set_session(autocommit=False)
            logger.info("✅ Database connection established")
            
            # Analyze database schema
            self._analyze_database_schema()
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize services: {e}")
            raise
    
    def _analyze_database_schema(self):
        """Analyze database schema to determine available tables and columns"""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Check for whitelisted_channels table
                cur.execute("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'whitelisted_channels' 
                    ORDER BY ordinal_position
                """)
                whitelist_cols = cur.fetchall()
                
                # Check for monitored_channels table  
                cur.execute("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'monitored_channels' 
                    ORDER BY ordinal_position
                """)
                monitored_cols = cur.fetchall()
                
                self.db_schema_info = {
                    'has_whitelisted_channels': len(whitelist_cols) > 0,
                    'has_monitored_channels': len(monitored_cols) > 0,
                    'whitelisted_columns': [col['column_name'] for col in whitelist_cols],
                    'monitored_columns': [col['column_name'] for col in monitored_cols]
                }
                
                if self.db_schema_info['has_whitelisted_channels']:
                    logger.info(f"📋 Found whitelisted_channels table with columns: {self.db_schema_info['whitelisted_columns']}")
                
                if self.db_schema_info['has_monitored_channels']:
                    logger.info(f"📋 Found monitored_channels table with columns: {self.db_schema_info['monitored_columns']}")
                
                if not (self.db_schema_info['has_whitelisted_channels'] or self.db_schema_info['has_monitored_channels']):
                    logger.warning("⚠️ No recognized whitelist tables found in database")
                    
        except Exception as e:
            logger.error(f"❌ Failed to analyze database schema: {e}")
            self.db_schema_info = {'has_whitelisted_channels': False, 'has_monitored_channels': False}
    
    @backoff.on_exception(
        backoff.expo,
        (HttpError, ConnectionError, TimeoutError),
        max_tries=3,
        factor=2
    )
    def _make_youtube_api_call(self, api_call_func, *args, **kwargs):
        """Make YouTube API call with exponential backoff retry logic"""
        try:
            return api_call_func(*args, **kwargs).execute()
        except HttpError as e:
            if e.resp.status == 403:
                logger.error("❌ YouTube API quota exceeded or permissions denied")
                raise
            elif e.resp.status == 429:
                logger.warning("⚠️ Rate limit exceeded, backing off...")
                raise
            else:
                logger.warning(f"⚠️ YouTube API error {e.resp.status}: {e.content.decode()}")
                raise
    
    def calculate_golf_relevance(self, channel_title: str, description: str = "") -> Tuple[float, bool, bool]:
        """
        Calculate golf relevance score and categorization for a channel
        
        Returns:
            Tuple of (relevance_score, is_golf_related, is_instructional)
        """
        text_to_analyze = f"{channel_title} {description}".lower()
        
        high_score = sum(2 for keyword in self.GOLF_KEYWORDS['high_relevance'] if keyword in text_to_analyze)
        medium_score = sum(1 for keyword in self.GOLF_KEYWORDS['medium_relevance'] if keyword in text_to_analyze)
        instruction_score = sum(1 for keyword in self.GOLF_KEYWORDS['instruction_keywords'] if keyword in text_to_analyze)
        
        total_score = high_score + medium_score * 0.5
        max_possible = len(self.GOLF_KEYWORDS['high_relevance']) * 2 + len(self.GOLF_KEYWORDS['medium_relevance']) * 0.5
        
        relevance_score = min(total_score / max_possible * 100, 100) if max_possible > 0 else 0
        is_golf_related = relevance_score >= 25 or any(keyword in text_to_analyze for keyword in ['golf'])
        is_instructional = instruction_score >= 2 or any(keyword in text_to_analyze for keyword in ['instruction', 'lesson', 'academy'])
        
        return relevance_score, is_golf_related, is_instructional
    
    def search_channel_enhanced(self, channel_name: str) -> ChannelSearchResult:
        """
        Enhanced channel search with golf-specific filtering and validation
        """
        result = ChannelSearchResult(search_name=channel_name)
        
        if self.dry_run:
            return self._generate_mock_result(channel_name)
        
        try:
            # Search for channels
            search_response = self._make_youtube_api_call(
                self.youtube.search().list,
                q=f"{channel_name} golf",
                part='snippet',
                type='channel',
                maxResults=10,
                order='relevance'
            )
            
            channels = search_response.get('items', [])
            if not channels:
                # Try without 'golf' keyword
                search_response = self._make_youtube_api_call(
                    self.youtube.search().list,
                    q=channel_name,
                    part='snippet',
                    type='channel',
                    maxResults=10,
                    order='relevance'
                )
                channels = search_response.get('items', [])
            
            if not channels:
                result.error_message = "No channels found"
                return result
            
            # Analyze and score all results for golf relevance
            scored_channels = []
            for channel in channels:
                title = channel['snippet']['title']
                description = channel['snippet'].get('description', '')
                
                relevance_score, is_golf_related, is_instructional = self.calculate_golf_relevance(title, description)
                
                scored_channels.append({
                    'channel_data': channel,
                    'relevance_score': relevance_score,
                    'is_golf_related': is_golf_related,
                    'is_instructional': is_instructional,
                    'title_match_score': self._calculate_title_similarity(channel_name, title)
                })
            
            # Sort by combination of relevance and title match
            scored_channels.sort(
                key=lambda x: (x['is_golf_related'], x['relevance_score'], x['title_match_score']), 
                reverse=True
            )
            
            # Store multiple results for review if needed
            if len(scored_channels) > 1:
                result.multiple_results = [
                    {
                        'channel_id': ch['channel_data']['snippet']['channelId'],
                        'title': ch['channel_data']['snippet']['title'],
                        'description': (ch['channel_data']['snippet'].get('description', '')[:200] + '...') if len(ch['channel_data']['snippet'].get('description', '')) > 200 else ch['channel_data']['snippet'].get('description', ''),
                        'relevance_score': ch['relevance_score'],
                        'is_golf_related': ch['is_golf_related']
                    }
                    for ch in scored_channels
                ]
                logger.info(f"🔍 Found {len(scored_channels)} channels for '{channel_name}', using most relevant")
            
            # Use the highest-scoring result
            best_match = scored_channels[0]
            channel_data = best_match['channel_data']
            channel_id = channel_data['snippet']['channelId']
            
            # Get detailed channel information
            channel_response = self._make_youtube_api_call(
                self.youtube.channels().list,
                id=channel_id,
                part='snippet,statistics,brandingSettings'
            )
            
            if channel_response['items']:
                detailed_data = channel_response['items'][0]
                result.channel_id = channel_id
                result.channel_title = detailed_data['snippet']['title']
                result.description = detailed_data['snippet'].get('description', '')
                result.country = detailed_data['snippet'].get('country', '')
                result.created_date = detailed_data['snippet'].get('publishedAt', '')
                
                # Handle optional statistics (some channels hide subscriber counts)
                stats = detailed_data.get('statistics', {})
                result.subscriber_count = int(stats.get('subscriberCount', 0)) if stats.get('subscriberCount') else None
                result.video_count = int(stats.get('videoCount', 0)) if stats.get('videoCount') else None
                result.view_count = int(stats.get('viewCount', 0)) if stats.get('viewCount') else None
                
                # Get custom URL / handle if available
                branding = detailed_data.get('brandingSettings', {})
                channel_settings = branding.get('channel', {})
                result.channel_handle = channel_settings.get('customUrl', '')
                
                # Calculate relevance scores
                result.golf_relevance_score, result.is_golf_related, result.is_instructional = \
                    self.calculate_golf_relevance(result.channel_title, result.description)
                
                # Set confidence level
                if result.golf_relevance_score >= 70:
                    result.confidence_level = "high"
                elif result.golf_relevance_score >= 40:
                    result.confidence_level = "medium"
                else:
                    result.confidence_level = "low"
                
                # Add warnings for low-confidence matches
                if result.confidence_level == "low":
                    result.warning_messages.append("Low golf relevance score - manual review recommended")
                
                if not result.is_golf_related:
                    result.warning_messages.append("Channel may not be golf-related")
                
                logger.info(f"✅ Found: {result.channel_title} (ID: {channel_id}, Golf Score: {result.golf_relevance_score:.1f}%)")
                
            else:
                result.error_message = "Channel details not available"
                
        except Exception as e:
            result.error_message = f"Search error: {str(e)}"
            logger.error(f"❌ Error searching for '{channel_name}': {e}")
        
        # Add small delay for rate limiting
        time.sleep(self.rate_limit_delay)
        
        return result
    
    def _calculate_title_similarity(self, search_name: str, channel_title: str) -> float:
        """Calculate similarity score between search name and channel title"""
        search_words = set(search_name.lower().split())
        title_words = set(channel_title.lower().split())
        
        if not search_words:
            return 0
        
        intersection = search_words.intersection(title_words)
        return len(intersection) / len(search_words) * 100
    
    def _generate_mock_result(self, channel_name: str) -> ChannelSearchResult:
        """Generate mock result for dry-run mode"""
        hash_suffix = str(abs(hash(channel_name)))[-18:]
        mock_channel_id = f"UC{hash_suffix}"
        
        result = ChannelSearchResult(search_name=channel_name)
        result.channel_id = mock_channel_id
        result.channel_title = f"{channel_name}"
        result.subscriber_count = 150000 + (hash(channel_name) % 100000)
        result.video_count = 300 + (hash(channel_name) % 500)
        result.view_count = 15000000 + (hash(channel_name) % 10000000)
        result.golf_relevance_score = 85.0
        result.is_golf_related = True
        result.is_instructional = True
        result.confidence_level = "high"
        
        logger.info(f"🔄 [DRY-RUN] Mock result: {result.channel_title} ({mock_channel_id})")
        return result
    
    def check_whitelist_status_enhanced(self, result: ChannelSearchResult) -> ChannelSearchResult:
        """
        Enhanced whitelist checking with support for multiple table schemas
        """
        if not result.channel_id or self.dry_run:
            if self.dry_run:
                # Mock some channels as already whitelisted for demo
                if "Danny Maude" in result.search_name or "Rick Shiels" in result.search_name:
                    result.is_whitelisted = True
                    result.whitelist_name = result.channel_title
                    result.whitelist_channel_type = "instructional"
                    result.whitelist_table = "whitelisted_channels"
                    logger.info(f"🔄 [DRY-RUN] '{result.channel_title}' simulated as whitelisted")
                else:
                    logger.info(f"🔄 [DRY-RUN] '{result.channel_title}' simulated as NOT whitelisted")
            return result
        
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Check whitelisted_channels table first
                if self.db_schema_info.get('has_whitelisted_channels'):
                    cur.execute("""
                        SELECT name, channel_type, active, 'whitelisted_channels' as source_table
                        FROM whitelisted_channels 
                        WHERE channel_id = %s
                    """, (result.channel_id,))
                    
                    row = cur.fetchone()
                    if row:
                        result.is_whitelisted = True
                        result.whitelist_name = row['name']
                        result.whitelist_channel_type = row['channel_type']
                        result.whitelist_table = row['source_table']
                        
                        if not row.get('active', True):
                            result.warning_messages.append("Channel is whitelisted but marked as inactive")
                        return result
                
                # Check monitored_channels table as fallback
                if self.db_schema_info.get('has_monitored_channels'):
                    cur.execute("""
                        SELECT channel_name as name, 'monitored' as channel_type, 
                               is_whitelisted as active, 'monitored_channels' as source_table
                        FROM monitored_channels 
                        WHERE channel_id = %s
                    """, (result.channel_id,))
                    
                    row = cur.fetchone()
                    if row:
                        result.is_whitelisted = row['active']
                        result.whitelist_name = row['name']
                        result.whitelist_channel_type = row['channel_type']
                        result.whitelist_table = row['source_table']
                        
                        if not row['active']:
                            result.warning_messages.append("Channel found in monitored_channels but not whitelisted")
                        return result
                
                # Not found in any table
                result.is_whitelisted = False
                
        except Exception as e:
            logger.error(f"❌ Database error checking whitelist status: {e}")
            result.error_message = f"Database error: {str(e)}"
        
        return result
    
    def process_channel_list(self, channel_names: List[str]) -> List[ChannelSearchResult]:
        """Process list of channel names with enhanced error handling"""
        results = []
        
        logger.info(f"🚀 Starting processing of {len(channel_names)} channels")
        
        for i, channel_name in enumerate(channel_names, 1):
            logger.info(f"🔄 Processing {i}/{len(channel_names)}: {channel_name}")
            
            try:
                # Search for channel with enhanced features
                result = self.search_channel_enhanced(channel_name)
                
                # Check whitelist status if channel was found
                if result.channel_id:
                    result = self.check_whitelist_status_enhanced(result)
                
                results.append(result)
                
                # Log immediate status
                if result.error_message:
                    logger.warning(f"⚠️ {channel_name}: {result.error_message}")
                elif result.channel_id:
                    status_icon = "✅" if result.is_whitelisted else "🆕"
                    logger.info(f"{status_icon} {channel_name} -> {result.channel_title}")
                
            except KeyboardInterrupt:
                logger.info("⏹️ Processing interrupted by user")
                break
            except Exception as e:
                error_result = ChannelSearchResult(
                    search_name=channel_name,
                    error_message=f"Processing error: {str(e)}"
                )
                results.append(error_result)
                logger.error(f"❌ Failed to process '{channel_name}': {e}")
        
        logger.info(f"✅ Completed processing {len(results)} channels")
        return results
    
    def generate_sql_statements(self, results: List[ChannelSearchResult], 
                               channel_type: str = 'instructional') -> str:
        """Generate SQL INSERT statements for new channels with enhanced safety"""
        new_channels = [
            r for r in results 
            if r.channel_id and not r.is_whitelisted and not r.error_message
        ]
        
        if not new_channels:
            return "-- No new channels to add to whitelist"
        
        # Determine which table to use
        target_table = None
        if self.db_schema_info.get('has_whitelisted_channels'):
            target_table = 'whitelisted_channels'
        elif self.db_schema_info.get('has_monitored_channels'):
            target_table = 'monitored_channels'
        
        if not target_table:
            return "-- ERROR: No compatible database table found for inserting channels"
        
        sql_statements = []
        header_comments = [
            f"-- Enhanced Channel Whitelist Manager - Generated {datetime.now().isoformat()}",
            f"-- Target table: {target_table}",
            f"-- Channel type: {channel_type}",
            f"-- New channels to add: {len(new_channels)}",
            f"-- Safe to run: Uses INSERT ... ON CONFLICT DO NOTHING for duplicate prevention",
            ""
        ]
        
        for result in new_channels:
            # Escape single quotes in names
            safe_name = result.channel_title.replace("'", "''")
            
            if target_table == 'whitelisted_channels':
                sql_statements.append(
                    f"INSERT INTO whitelisted_channels (channel_id, name, channel_type, active, created_at) "
                    f"VALUES ('{result.channel_id}', '{safe_name}', '{channel_type}', true, NOW()) "
                    f"ON CONFLICT (channel_id) DO NOTHING;"
                )
            else:  # monitored_channels
                sql_statements.append(
                    f"INSERT INTO monitored_channels (channel_id, channel_name, is_whitelisted, priority, created_at) "
                    f"VALUES ('{result.channel_id}', '{safe_name}', true, 1, NOW()) "
                    f"ON CONFLICT (channel_id) DO NOTHING;"
                )
            
            # Add comment with channel details
            sql_statements.append(
                f"-- {safe_name}: {result.subscriber_count or 'Unknown'} subscribers, "
                f"Golf relevance: {result.golf_relevance_score or 'Unknown'}%"
            )
        
        return '\n'.join(header_comments) + '\n'.join(sql_statements)
    
    def print_comprehensive_report(self, results: List[ChannelSearchResult]):
        """Generate comprehensive analysis report"""
        print("\n" + "="*100)
        print("🏌️ ENHANCED GOLF CHANNEL WHITELIST ANALYSIS REPORT")
        print("="*100)
        
        # Statistics
        total = len(results)
        found = len([r for r in results if r.channel_id])
        whitelisted = len([r for r in results if r.is_whitelisted])
        needs_adding = len([r for r in results if r.channel_id and not r.is_whitelisted and not r.error_message])
        errors = len([r for r in results if r.error_message])
        warnings = len([r for r in results if r.warning_messages])
        
        print(f"\n📊 SUMMARY STATISTICS:")
        print(f"   Total channels searched: {total}")
        print(f"   ✅ Channels found: {found}")
        print(f"   ✅ Already whitelisted: {whitelisted}")
        print(f"   🆕 Need to be added: {needs_adding}")
        print(f"   ❌ Errors encountered: {errors}")
        print(f"   ⚠️ Warnings generated: {warnings}")
        
        if found > 0:
            golf_related = len([r for r in results if r.is_golf_related])
            instructional = len([r for r in results if r.is_instructional])
            high_confidence = len([r for r in results if r.confidence_level == "high"])
            
            print(f"   🏌️ Golf-related channels: {golf_related}")
            print(f"   📚 Instructional channels: {instructional}")
            print(f"   🎯 High-confidence matches: {high_confidence}")
        
        # Detailed channel analysis
        print(f"\n🔍 DETAILED CHANNEL ANALYSIS:")
        print("-" * 100)
        
        for result in results:
            print(f"\n🏷️ Channel: {result.search_name}")
            
            if result.error_message:
                print(f"   ❌ Error: {result.error_message}")
                continue
            
            if not result.channel_id:
                print(f"   ❌ Channel not found")
                continue
            
            # Channel information
            print(f"   ✅ Found: {result.channel_title}")
            print(f"   🆔 Channel ID: {result.channel_id}")
            
            if result.subscriber_count:
                print(f"   👥 Subscribers: {result.subscriber_count:,}")
            if result.video_count:
                print(f"   📹 Videos: {result.video_count:,}")
            if result.view_count:
                print(f"   👀 Total views: {result.view_count:,}")
            
            # Golf relevance analysis
            if result.golf_relevance_score is not None:
                confidence_icon = {"high": "🎯", "medium": "⚖️", "low": "⚠️"}.get(result.confidence_level, "❓")
                print(f"   {confidence_icon} Golf relevance: {result.golf_relevance_score:.1f}% ({result.confidence_level} confidence)")
                print(f"   🏌️ Golf-related: {'Yes' if result.is_golf_related else 'No'}")
                print(f"   📚 Instructional: {'Yes' if result.is_instructional else 'No'}")
            
            # Whitelist status
            if result.is_whitelisted:
                print(f"   ✅ Already whitelisted: {result.whitelist_name} ({result.whitelist_channel_type})")
                print(f"   📋 Source table: {result.whitelist_table}")
            else:
                print(f"   🆕 Not whitelisted - NEEDS TO BE ADDED")
            
            # Warnings
            if result.warning_messages:
                for warning in result.warning_messages:
                    print(f"   ⚠️ Warning: {warning}")
            
            # Multiple results info
            if result.multiple_results and len(result.multiple_results) > 1:
                print(f"   🔍 Found {len(result.multiple_results)} similar channels (used most relevant):")
                for i, alt in enumerate(result.multiple_results[1:4], 2):  # Show top 3 alternatives
                    relevance = alt.get('relevance_score', 0)
                    golf_related = "🏌️" if alt.get('is_golf_related', False) else "❌"
                    print(f"      #{i}: {alt['title']} ({alt['channel_id']}) {golf_related} {relevance:.1f}%")
        
        # SQL generation
        if needs_adding > 0:
            print(f"\n" + "="*100)
            print("📝 SQL STATEMENTS TO ADD NEW CHANNELS")
            print("="*100)
            sql_statements = self.generate_sql_statements(results)
            print(sql_statements)
        
        # Recommendations
        print(f"\n" + "="*100)
        print("💡 RECOMMENDATIONS")
        print("="*100)
        
        low_confidence = [r for r in results if r.confidence_level == "low" and r.channel_id]
        if low_confidence:
            print(f"⚠️ Manual review recommended for {len(low_confidence)} low-confidence channels:")
            for r in low_confidence:
                print(f"   - {r.channel_title}: {r.golf_relevance_score:.1f}% golf relevance")
        
        non_golf = [r for r in results if r.channel_id and not r.is_golf_related]
        if non_golf:
            print(f"🚫 Consider excluding {len(non_golf)} non-golf channels:")
            for r in non_golf:
                print(f"   - {r.channel_title}")
        
        if not (low_confidence or non_golf):
            print("✅ All found channels appear to be good matches for golf instruction content")
    
    def save_detailed_results(self, results: List[ChannelSearchResult], 
                             filename: str = None) -> str:
        """Save detailed results to JSON with enhanced metadata"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"channel_analysis_{timestamp}.json"
        
        # Convert results to dict format with metadata
        output_data = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'script_version': 'enhanced_channel_manager_v2.0',
                'dry_run_mode': self.dry_run,
                'total_channels': len(results),
                'database_schema': self.db_schema_info
            },
            'summary_stats': {
                'found': len([r for r in results if r.channel_id]),
                'whitelisted': len([r for r in results if r.is_whitelisted]),
                'needs_adding': len([r for r in results if r.channel_id and not r.is_whitelisted and not r.error_message]),
                'errors': len([r for r in results if r.error_message]),
                'golf_related': len([r for r in results if r.is_golf_related]),
                'instructional': len([r for r in results if r.is_instructional])
            },
            'channel_results': [asdict(result) for result in results]
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"💾 Detailed results saved to {filename}")
        return filename
    
    def validate_existing_channels(self) -> List[Dict]:
        """Validate existing whitelisted channels for golf relevance"""
        if self.dry_run:
            logger.info("🔄 [DRY-RUN] Skipping existing channel validation")
            return []
        
        existing_channels = []
        
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Get existing whitelisted channels
                if self.db_schema_info.get('has_whitelisted_channels'):
                    cur.execute("""
                        SELECT channel_id, name, channel_type, active 
                        FROM whitelisted_channels 
                        WHERE active = true
                    """)
                    rows = cur.fetchall()
                    
                    for row in rows:
                        channel_info = {
                            'channel_id': row['channel_id'],
                            'name': row['name'],
                            'channel_type': row['channel_type'],
                            'table_source': 'whitelisted_channels'
                        }
                        
                        # Validate with YouTube API
                        try:
                            channel_response = self._make_youtube_api_call(
                                self.youtube.channels().list,
                                id=row['channel_id'],
                                part='snippet,statistics'
                            )
                            
                            if channel_response['items']:
                                channel_data = channel_response['items'][0]
                                title = channel_data['snippet']['title']
                                description = channel_data['snippet'].get('description', '')
                                
                                relevance_score, is_golf_related, is_instructional = \
                                    self.calculate_golf_relevance(title, description)
                                
                                channel_info.update({
                                    'current_title': title,
                                    'subscriber_count': channel_data['statistics'].get('subscriberCount'),
                                    'golf_relevance_score': relevance_score,
                                    'is_golf_related': is_golf_related,
                                    'is_instructional': is_instructional,
                                    'validation_status': 'valid'
                                })
                            else:
                                channel_info.update({
                                    'validation_status': 'channel_not_found',
                                    'error': 'Channel no longer exists on YouTube'
                                })
                        
                        except Exception as e:
                            channel_info.update({
                                'validation_status': 'api_error',
                                'error': str(e)
                            })
                        
                        existing_channels.append(channel_info)
                        time.sleep(self.rate_limit_delay)
        
        except Exception as e:
            logger.error(f"❌ Error validating existing channels: {e}")
        
        return existing_channels
    
    def close(self):
        """Clean up connections"""
        if self.conn:
            self.conn.close()
            logger.info("🔌 Database connection closed")

def load_channels_from_file(filename: str) -> List[str]:
    """Load channel names from text file with enhanced parsing"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            channels = []
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                
                # Support comma-separated values on a single line
                if ',' in line:
                    channels.extend([name.strip() for name in line.split(',') if name.strip()])
                else:
                    channels.append(line)
        
        logger.info(f"📂 Loaded {len(channels)} channels from {filename}")
        return channels
        
    except FileNotFoundError:
        logger.error(f"❌ Channel file not found: {filename}")
        return []
    except Exception as e:
        logger.error(f"❌ Error loading channel file: {e}")
        return []

def main():
    """Enhanced main function with comprehensive argument handling"""
    parser = argparse.ArgumentParser(
        description='Enhanced YouTube Channel Whitelist Manager for Golf Directory',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python enhanced_channel_manager.py --dry-run                    # Safe test run
  python enhanced_channel_manager.py --live-run                   # Production execution  
  python enhanced_channel_manager.py -f channels.txt -t coaching  # Custom channel list
  python enhanced_channel_manager.py --validate-existing          # Audit existing channels
        """
    )
    
    parser.add_argument('--config-file', '-f', 
                       help='Text file with channel names (one per line or comma-separated)')
    parser.add_argument('--channel-type', '-t', default='instructional',
                       help='Channel type for new channels (default: instructional)')
    parser.add_argument('--output-json', '-o',
                       help='Save detailed results to JSON file')
    parser.add_argument('--dry-run', action='store_true', default=True,
                       help='Run in safe dry-run mode (default behavior)')
    parser.add_argument('--live-run', action='store_true',
                       help='Execute with actual API calls and database operations')
    parser.add_argument('--validate-existing', action='store_true',
                       help='Validate existing whitelisted channels for golf relevance')
    parser.add_argument('--log-level', default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='Set logging level')
    parser.add_argument('--max-retries', type=int, default=3,
                       help='Maximum API retry attempts (default: 3)')
    
    args = parser.parse_args()
    
    # Setup logging with specified level
    global logger
    logger = setup_logging(args.log_level)
    
    # Determine run mode
    dry_run = not args.live_run  # Default to dry-run unless explicitly overridden
    
    if dry_run and not args.live_run:
        logger.info("🔄 Running in DRY-RUN mode (use --live-run for production execution)")
    elif args.live_run:
        logger.info("⚡ Running in LIVE mode - will make actual API calls and database changes")
    
    # Default channel list matching your requirements
    default_channels = [
        'Danny Maude', 'Lower My Handicap', 'Sonic Titan Golf', 'WorldClassGolf',
        'Scratch Golf Academy', 'Short Game Chef', 'Kerrod Gray Golf', 'Harry Shaw',
        'Eric Cogorno', 'Bausek Golf', 'Ashley Knoll', 'Jerome Rufin', 'Steve Pratt'
    ]
    
    # Load channels
    if args.config_file:
        channels = load_channels_from_file(args.config_file)
        if not channels:
            logger.warning("⚠️ No channels loaded from file, using default list")
            channels = default_channels
    else:
        channels = default_channels
        logger.info(f"📋 Using default channel list ({len(channels)} channels)")
    
    # Environment variables
    database_url = os.getenv('DATABASE_URL')
    youtube_api_key = os.getenv('YOUTUBE_API_KEY', 'AIzaSyCHslhwhJz15xOm5U04Xf6vJXB5NpBK6c8')
    
    if not dry_run:
        if not database_url:
            logger.error("❌ DATABASE_URL environment variable required for live mode")
            sys.exit(1)
        if not youtube_api_key:
            logger.error("❌ YOUTUBE_API_KEY environment variable required for live mode")
            sys.exit(1)
    else:
        # Use dummy values for dry-run
        database_url = database_url or "postgresql://dummy:dummy@localhost/dummy"
        # API key already set above with default
    
    # Initialize manager
    manager = None
    try:
        logger.info(f"🚀 Initializing Enhanced Channel Manager")
        manager = ProductionChannelManager(
            database_url=database_url,
            youtube_api_key=youtube_api_key,
            dry_run=dry_run,
            max_retries=args.max_retries
        )
        
        if args.validate_existing:
            logger.info("🔍 Validating existing whitelisted channels...")
            existing_validation = manager.validate_existing_channels()
            
            if existing_validation:
                validation_file = f"existing_channel_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(validation_file, 'w') as f:
                    json.dump(existing_validation, f, indent=2, default=str)
                logger.info(f"💾 Existing channel validation saved to {validation_file}")
            
            return
        
        # Process channel list
        logger.info(f"🎯 Processing {len(channels)} golf instruction channels")
        results = manager.process_channel_list(channels)
        
        # Generate comprehensive report
        manager.print_comprehensive_report(results)
        
        # Save detailed results if requested
        if args.output_json:
            manager.save_detailed_results(results, args.output_json)
        else:
            saved_file = manager.save_detailed_results(results)
            logger.info(f"📄 Automatic detailed report saved: {saved_file}")
        
        # Final summary
        successful_results = len([r for r in results if r.channel_id and not r.error_message])
        logger.info(f"✅ Analysis completed successfully: {successful_results}/{len(channels)} channels processed")
        
    except KeyboardInterrupt:
        logger.info("⏹️ Analysis interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)
    finally:
        if manager:
            manager.close()

if __name__ == '__main__':
    main()