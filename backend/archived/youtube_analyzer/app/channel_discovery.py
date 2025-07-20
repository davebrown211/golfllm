"""
Channel Discovery System
Find lesser-known golf channels with high potential
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Set
from youtube_analyzer.app.golf_directory import GolfDirectory
from youtube_analyzer.app.database import SessionLocal
from youtube_analyzer.app.models import YouTubeVideo, YouTubeChannel
from sqlalchemy import func, and_, or_
import re
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChannelDiscovery:
    def __init__(self):
        self.directory = GolfDirectory()
        self.discovered_channels = set()
    
    def find_mentioned_channels(self):
        """Find channels mentioned in video titles and descriptions."""
        logger.info("Searching for mentioned channels in existing content...")
        
        with SessionLocal() as session:
            videos = session.query(YouTubeVideo).all()
            
            # Patterns to find channel mentions
            patterns = [
                r'@([A-Za-z0-9_\-]+)',  # @username mentions
                r'ft\.\s*([A-Za-z0-9_\-\s]+)',  # ft. mentions
                r'feat\.\s*([A-Za-z0-9_\-\s]+)',  # feat. mentions
                r'with\s+([A-Z][A-Za-z0-9_\-\s]+)',  # "with ChannelName"
                r'vs\.?\s*([A-Z][A-Za-z0-9_\-\s]+)',  # vs battles
            ]
            
            mentioned_names = set()
            for video in videos:
                text = f"{video.title} {video.description or ''}"
                for pattern in patterns:
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    mentioned_names.update(m.strip() for m in matches if len(m.strip()) > 3)
            
            # Filter out common words and our existing channels
            existing_names = {ch.title.lower() for ch in session.query(YouTubeChannel).all()}
            
            potential_channels = []
            for name in mentioned_names:
                if name.lower() not in existing_names and len(name) > 3:
                    # Search for this potential channel
                    try:
                        search_results = self.directory.youtube_client.search_golf_videos(
                            query=f"{name} golf channel",
                            max_results=3
                        )
                        if search_results:
                            potential_channels.append({
                                'mentioned_name': name,
                                'found_channels': [(v['channel_title'], v['channel_id']) 
                                                 for v in search_results]
                            })
                    except Exception as e:
                        logger.error(f"Error searching for {name}: {e}")
            
            return potential_channels
    
    def find_rising_channels(self):
        """Find channels with high engagement but low subscriber count."""
        logger.info("Finding rising golf channels...")
        
        # Search for golf content with specific characteristics
        rising_queries = [
            "golf channel under 100k subscribers",
            "new golf youtuber 2024",
            "underrated golf channel",
            "small golf youtuber",
            "golf content creator",
            "golf vlog beginner",
            "amateur golf channel"
        ]
        
        discovered = []
        for query in rising_queries:
            try:
                videos = self.directory.youtube_client.search_golf_videos(
                    query=query,
                    max_results=10,
                    order="relevance"
                )
                
                # Group by channel
                channels_found = {}
                for video in videos:
                    channel_id = video['channel_id']
                    if channel_id not in channels_found:
                        channels_found[channel_id] = {
                            'channel_title': video['channel_title'],
                            'videos': [],
                            'total_views': 0,
                            'avg_engagement': 0
                        }
                    channels_found[channel_id]['videos'].append(video)
                    channels_found[channel_id]['total_views'] += video['view_count']
                    channels_found[channel_id]['avg_engagement'] += video['engagement_rate']
                
                # Calculate averages and filter
                for channel_id, data in channels_found.items():
                    video_count = len(data['videos'])
                    data['avg_engagement'] /= video_count
                    data['avg_views'] = data['total_views'] / video_count
                    
                    # High engagement + decent views = rising channel
                    if data['avg_engagement'] > 5.0 and data['avg_views'] > 1000:
                        discovered.append({
                            'channel_id': channel_id,
                            'channel_title': data['channel_title'],
                            'metrics': {
                                'videos_found': video_count,
                                'avg_views': data['avg_views'],
                                'avg_engagement': data['avg_engagement']
                            }
                        })
                
            except Exception as e:
                logger.error(f"Error in rising channel search: {e}")
        
        return discovered
    
    def find_niche_content(self):
        """Find channels focusing on specific golf niches."""
        logger.info("Discovering niche golf content...")
        
        niche_searches = {
            'women_golf': ['ladies golf channel', 'women golf instruction', 'lpga youtube'],
            'senior_golf': ['senior golf tips', 'golf over 50', 'senior golf channel'],
            'junior_golf': ['junior golf channel', 'kids golf instruction', 'youth golf'],
            'golf_fitness': ['golf fitness youtube', 'golf workout channel', 'golf flexibility'],
            'course_vlogs': ['public golf course vlog', 'municipal golf', 'local golf course'],
            'golf_tech': ['golf technology channel', 'golf gadgets', 'golf apps review'],
            'international': ['uk golf channel', 'australian golf youtube', 'canadian golf'],
            'budget_golf': ['budget golf channel', 'affordable golf', 'cheap golf equipment'],
            'golf_travel': ['golf travel vlog', 'golf destinations', 'golf course reviews'],
            'trick_shots': ['golf trick shots channel', 'golf skills challenge', 'mini golf tricks']
        }
        
        niche_channels = {}
        
        for niche, queries in niche_searches.items():
            niche_channels[niche] = []
            
            for query in queries:
                try:
                    videos = self.directory.youtube_client.search_golf_videos(
                        query=query,
                        max_results=5,
                        order="relevance"
                    )
                    
                    # Track unique channels
                    seen_channels = set()
                    for video in videos:
                        if video['channel_id'] not in seen_channels:
                            seen_channels.add(video['channel_id'])
                            niche_channels[niche].append({
                                'channel_id': video['channel_id'],
                                'channel_title': video['channel_title'],
                                'sample_video': video['title'],
                                'views': video['view_count']
                            })
                    
                except Exception as e:
                    logger.error(f"Error searching niche {niche}: {e}")
        
        return niche_channels
    
    def analyze_channel_networks(self):
        """Find channels that frequently collaborate."""
        logger.info("Analyzing collaboration networks...")
        
        with SessionLocal() as session:
            # Find videos with multiple channel mentions
            collaboration_videos = session.query(YouTubeVideo).filter(
                or_(
                    YouTubeVideo.title.contains(' vs '),
                    YouTubeVideo.title.contains(' with '),
                    YouTubeVideo.title.contains(' ft. '),
                    YouTubeVideo.title.contains(' feat. '),
                    YouTubeVideo.title.contains(' & ')
                )
            ).all()
            
            # Build collaboration graph
            collaborations = {}
            for video in collaboration_videos:
                # Extract potential collaborators
                title_lower = video.title.lower()
                if any(word in title_lower for word in ['vs', 'with', 'ft.', 'feat.', '&']):
                    if video.channel_id not in collaborations:
                        collaborations[video.channel_id] = {
                            'channel': video.channel.title,
                            'collaborators': set(),
                            'collab_count': 0
                        }
                    collaborations[video.channel_id]['collab_count'] += 1
            
            return collaborations
    
    def get_discovery_report(self):
        """Generate a comprehensive discovery report."""
        report = {
            'timestamp': datetime.now().isoformat(),
            'mentioned_channels': self.find_mentioned_channels(),
            'rising_channels': self.find_rising_channels(),
            'niche_content': self.find_niche_content(),
            'collaboration_networks': self.analyze_channel_networks()
        }
        
        return report
    
    def auto_collect_discoveries(self, max_channels=10):
        """Automatically collect content from discovered channels."""
        logger.info("Auto-collecting from discovered channels...")
        
        # Get rising channels
        rising = self.find_rising_channels()
        
        collected_count = 0
        for channel_data in rising[:max_channels]:
            try:
                logger.info(f"Collecting from {channel_data['channel_title']}")
                
                # Get more videos from this channel
                search_params = {
                    'part': 'snippet',
                    'channelId': channel_data['channel_id'],
                    'type': 'video',
                    'maxResults': 10,
                    'order': 'date'
                }
                
                response = self.directory.youtube_client.youtube.search().list(**search_params).execute()
                video_ids = [item['id']['videoId'] for item in response['items']]
                
                if video_ids:
                    videos = self.directory.youtube_client.get_video_details(video_ids)
                    
                    with SessionLocal() as session:
                        for video_data in videos:
                            try:
                                self.directory._upsert_video(session, video_data)
                                session.commit()
                            except Exception as e:
                                session.rollback()
                    
                    collected_count += 1
                    
            except Exception as e:
                logger.error(f"Error collecting from {channel_data['channel_title']}: {e}")
        
        logger.info(f"Collected content from {collected_count} new channels")


def discover_new_channels():
    """Run channel discovery process."""
    discovery = ChannelDiscovery()
    report = discovery.get_discovery_report()
    
    print("\n=== GOLF CHANNEL DISCOVERY REPORT ===")
    print(f"Generated: {report['timestamp']}\n")
    
    # Show mentioned channels
    if report['mentioned_channels']:
        print("📢 CHANNELS MENTIONED IN VIDEOS:")
        for mention in report['mentioned_channels'][:10]:
            print(f"\nMentioned: '{mention['mentioned_name']}'")
            for channel_name, channel_id in mention['found_channels'][:2]:
                print(f"  → Found: {channel_name}")
    
    # Show rising channels
    if report['rising_channels']:
        print("\n\n🚀 RISING CHANNELS (High Engagement):")
        for channel in report['rising_channels'][:10]:
            metrics = channel['metrics']
            print(f"\n{channel['channel_title']}")
            print(f"  Engagement: {metrics['avg_engagement']:.1f}%")
            print(f"  Avg Views: {metrics['avg_views']:,.0f}")
            print(f"  Videos Found: {metrics['videos_found']}")
    
    # Show niche content
    if report['niche_content']:
        print("\n\n🎯 NICHE CONTENT DISCOVERED:")
        for niche, channels in report['niche_content'].items():
            if channels:
                print(f"\n{niche.upper().replace('_', ' ')}:")
                for ch in channels[:3]:
                    print(f"  • {ch['channel_title']} ({ch['views']:,} views)")
    
    return report


if __name__ == "__main__":
    discover_new_channels()