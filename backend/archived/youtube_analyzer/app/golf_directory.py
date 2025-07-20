"""
Golf YouTube Directory - Proof of Concept
A metadata-driven approach to organizing golf content on YouTube
"""

import os
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional
from sqlalchemy import desc, func
from sqlalchemy.orm import Session
from youtube_analyzer.app.models import YouTubeVideo, YouTubeChannel, VideoRanking
from youtube_analyzer.app.database import engine, SessionLocal, Base
from youtube_analyzer.app.youtube_metadata import YouTubeMetadataClient
import isodate
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class GolfDirectory:
    def __init__(self):
        # Use existing PostgreSQL database
        Base.metadata.create_all(bind=engine)
        self.SessionLocal = SessionLocal
        
        api_key = os.getenv('YOUTUBE_API_KEY') or os.getenv('GOOGLE_API_KEY')
        self.youtube_client = YouTubeMetadataClient(api_key) if api_key else None
    
    def update_video_catalog(self, search_terms: List[str] = None):
        """
        Update the video catalog with latest golf videos.
        """
        if not self.youtube_client:
            print("No YouTube API key configured")
            return
        
        if search_terms is None:
            search_terms = [
                "golf",
                "PGA tour 2024",
                "golf instruction",
                "golf equipment review",
                "golf course vlog",
                "golf highlights",
                "golf swing tips"
            ]
        
        with self.SessionLocal() as session:
            for term in search_terms:
                print(f"Searching for: {term}")
                videos = self.youtube_client.search_golf_videos(query=term, max_results=25)
                
                for video_data in videos:
                    try:
                        self._upsert_video(session, video_data)
                        session.commit()
                    except Exception as e:
                        session.rollback()
                        print(f"Error saving video {video_data.get('id')}: {str(e)}")
    
    def _upsert_video(self, session: Session, video_data: Dict):
        """
        Insert or update video and channel data.
        """
        # Upsert channel
        channel = session.query(YouTubeChannel).filter_by(id=video_data['channel_id']).first()
        if not channel:
            channel = YouTubeChannel(
                id=video_data['channel_id'],
                title=video_data['channel_title']
            )
            session.add(channel)
            # Flush to avoid duplicate key errors in bulk operations
            try:
                session.flush()
            except:
                # Channel might have been added by another video in this batch
                session.rollback()
                channel = session.query(YouTubeChannel).filter_by(id=video_data['channel_id']).first()
        
        # Upsert video
        video = session.query(YouTubeVideo).filter_by(id=video_data['id']).first()
        if not video:
            video = YouTubeVideo(id=video_data['id'])
            session.add(video)
        
        # Update video data
        video.title = video_data['title']
        video.description = video_data['description'][:1000]  # Truncate long descriptions
        video.channel_id = video_data['channel_id']
        # Parse published date with timezone
        published_str = video_data['published_at'].replace('Z', '+00:00')
        video.published_at = datetime.fromisoformat(published_str)
        video.view_count = video_data['view_count']
        video.like_count = video_data['like_count']
        video.comment_count = video_data['comment_count']
        video.engagement_rate = video_data['engagement_rate']
        video.thumbnail_url = video_data['thumbnail']
        
        # Parse duration
        try:
            duration = isodate.parse_duration(video_data['duration'])
            video.duration_seconds = int(duration.total_seconds())
        except:
            video.duration_seconds = 0
        
        # Calculate view velocity (handle timezone-aware datetime)
        now = datetime.now(video.published_at.tzinfo) if video.published_at.tzinfo else datetime.now()
        days_since_upload = (now - video.published_at).days or 1
        video.view_velocity = video.view_count / days_since_upload
        
        # Categorize video based on title/description
        video.category = self._categorize_video(video.title, video.description)
    
    def _categorize_video(self, title: str, description: str) -> str:
        """
        Simple categorization based on keywords.
        """
        text = (title + " " + description).lower()
        
        categories = {
            'instruction': ['lesson', 'tip', 'how to', 'tutorial', 'teach', 'swing', 'putting', 'chipping'],
            'equipment': ['review', 'club', 'ball', 'gear', 'equipment', 'shaft', 'driver', 'iron'],
            'tour': ['pga', 'tour', 'tournament', 'round', 'leaderboard', 'championship'],
            'highlights': ['highlight', 'best', 'shot', 'hole in one', 'ace', 'eagle'],
            'vlog': ['vlog', 'course', 'round', 'playing', 'golf with'],
            'news': ['news', 'update', 'announcement', 'breaking']
        }
        
        for category, keywords in categories.items():
            if any(keyword in text for keyword in keywords):
                return category
        
        return 'general'
    
    def update_rankings(self):
        """
        Calculate and update video rankings.
        """
        with self.SessionLocal() as session:
            # Clear old rankings
            session.query(VideoRanking).filter(
                VideoRanking.date < datetime.now() - timedelta(days=7)
            ).delete()
            
            ranking_types = [
                ('daily_trending', 1),
                ('weekly_trending', 7),
                ('all_time_views', 9999),
                ('high_engagement', 9999)
            ]
            
            for ranking_type, days in ranking_types:
                self._calculate_ranking(session, ranking_type, days)
            
            session.commit()
    
    def _calculate_ranking(self, session: Session, ranking_type: str, days: int):
        """
        Calculate rankings based on different criteria.
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        if ranking_type == 'daily_trending':
            # Videos published in last day, sorted by views
            videos = session.query(YouTubeVideo).filter(
                YouTubeVideo.published_at >= cutoff_date
            ).order_by(desc(YouTubeVideo.view_count)).limit(100).all()
            
        elif ranking_type == 'weekly_trending':
            # Videos with highest view velocity
            videos = session.query(YouTubeVideo).filter(
                YouTubeVideo.published_at >= cutoff_date
            ).order_by(desc(YouTubeVideo.view_velocity)).limit(100).all()
            
        elif ranking_type == 'all_time_views':
            # All time most viewed
            videos = session.query(YouTubeVideo).order_by(
                desc(YouTubeVideo.view_count)
            ).limit(100).all()
            
        elif ranking_type == 'high_engagement':
            # Highest engagement rate
            videos = session.query(YouTubeVideo).filter(
                YouTubeVideo.view_count > 10000  # Min threshold
            ).order_by(desc(YouTubeVideo.engagement_rate)).limit(100).all()
        
        # Create rankings
        for rank, video in enumerate(videos, 1):
            ranking = VideoRanking(
                video_id=video.id,
                ranking_type=ranking_type,
                rank=rank,
                score=self._calculate_score(video, ranking_type),
                date=datetime.now()
            )
            session.add(ranking)
    
    def _calculate_score(self, video: YouTubeVideo, ranking_type: str) -> float:
        """
        Calculate a normalized score for ranking.
        """
        if ranking_type in ['daily_trending', 'all_time_views']:
            return float(video.view_count)
        elif ranking_type == 'weekly_trending':
            return video.view_velocity
        elif ranking_type == 'high_engagement':
            return video.engagement_rate
        return 0.0
    
    def get_rankings(self, ranking_type: str = 'daily_trending', limit: int = 20) -> List[Dict]:
        """
        Get current rankings for display.
        """
        with self.SessionLocal() as session:
            rankings = session.query(VideoRanking).filter_by(
                ranking_type=ranking_type
            ).order_by(VideoRanking.rank).limit(limit).all()
            
            results = []
            for ranking in rankings:
                video = ranking.video
                results.append({
                    'rank': ranking.rank,
                    'title': video.title,
                    'channel': video.channel.title,
                    'views': f"{video.view_count:,}",
                    'likes': f"{video.like_count:,}",
                    'engagement': f"{video.engagement_rate:.2f}%",
                    'published': video.published_at.strftime('%Y-%m-%d'),
                    'url': f"https://youtube.com/watch?v={video.id}",
                    'thumbnail': video.thumbnail_url
                })
            
            return results
    
    def get_top_channels(self, limit: int = 20) -> List[Dict]:
        """
        Get top golf channels by video performance.
        """
        with self.SessionLocal() as session:
            # Aggregate video stats by channel
            channel_stats = session.query(
                YouTubeChannel.id,
                YouTubeChannel.title,
                func.count(YouTubeVideo.id).label('video_count'),
                func.sum(YouTubeVideo.view_count).label('total_views'),
                func.avg(YouTubeVideo.engagement_rate).label('avg_engagement')
            ).join(
                YouTubeVideo
            ).group_by(
                YouTubeChannel.id
            ).order_by(
                desc('total_views')
            ).limit(limit).all()
            
            results = []
            for stats in channel_stats:
                results.append({
                    'channel': stats.title,
                    'videos_tracked': stats.video_count,
                    'total_views': f"{int(stats.total_views):,}",
                    'avg_engagement': f"{stats.avg_engagement:.2f}%",
                    'url': f"https://youtube.com/channel/{stats.id}"
                })
            
            return results
    
    def search_videos(self, query: str, category: Optional[str] = None) -> List[Dict]:
        """
        Search videos in the local database.
        """
        with self.SessionLocal() as session:
            search = session.query(YouTubeVideo)
            
            # Text search in title and description
            search = search.filter(
                (YouTubeVideo.title.contains(query)) |
                (YouTubeVideo.description.contains(query))
            )
            
            if category:
                search = search.filter(YouTubeVideo.category == category)
            
            videos = search.order_by(desc(YouTubeVideo.view_count)).limit(50).all()
            
            results = []
            for video in videos:
                results.append({
                    'title': video.title,
                    'channel': video.channel.title,
                    'views': f"{video.view_count:,}",
                    'category': video.category,
                    'published': video.published_at.strftime('%Y-%m-%d'),
                    'url': f"https://youtube.com/watch?v={video.id}"
                })
            
            return results


def demo_directory():
    """
    Demo the Golf Directory functionality.
    """
    directory = GolfDirectory()
    
    print("=== GOLF YOUTUBE DIRECTORY DEMO ===\n")
    
    # Update catalog (requires API key)
    if directory.youtube_client:
        print("Updating video catalog...")
        directory.update_video_catalog()
        directory.update_rankings()
        print("Catalog updated!\n")
    
    # Show rankings
    print("=== TODAY'S TRENDING GOLF VIDEOS ===")
    for video in directory.get_rankings('daily_trending', limit=10):
        print(f"{video['rank']}. {video['title']}")
        print(f"   Channel: {video['channel']} | Views: {video['views']} | Engagement: {video['engagement']}")
        print(f"   URL: {video['url']}\n")
    
    # Show top channels
    print("\n=== TOP GOLF CHANNELS ===")
    for channel in directory.get_top_channels(limit=10):
        print(f"• {channel['channel']}")
        print(f"  Videos: {channel['videos_tracked']} | Total Views: {channel['total_views']}")
        print(f"  Avg Engagement: {channel['avg_engagement']} | URL: {channel['url']}\n")


if __name__ == "__main__":
    demo_directory()