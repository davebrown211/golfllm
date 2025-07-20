"""
Trending Golf Content Detector
Identifies trending videos through multiple signals
"""

import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy import func, and_
from youtube_analyzer.app.database import SessionLocal
from youtube_analyzer.app.models import YouTubeVideo, VideoRanking
from youtube_analyzer.app.golf_directory import GolfDirectory

logger = logging.getLogger(__name__)


class TrendingDetector:
    def __init__(self):
        self.directory = GolfDirectory()
    
    def calculate_trending_scores(self):
        """Calculate trending scores based on multiple factors."""
        with SessionLocal() as session:
            # 1. View Velocity Score (views per hour for recent videos)
            logger.info("Calculating view velocity scores...")
            
            # Videos from last 48 hours
            cutoff_48h = datetime.now(timezone.utc) - timedelta(hours=48)
            recent_videos = session.query(YouTubeVideo).filter(
                YouTubeVideo.published_at >= cutoff_48h
            ).all()
            
            for video in recent_videos:
                hours_since_upload = (datetime.now(timezone.utc) - video.published_at).total_seconds() / 3600
                if hours_since_upload > 0:
                    hourly_velocity = video.view_count / hours_since_upload
                    
                    # Create velocity ranking
                    ranking = VideoRanking(
                        video_id=video.id,
                        ranking_type='hourly_velocity',
                        score=hourly_velocity,
                        rank=0  # Will be updated later
                    )
                    session.add(ranking)
            
            # 2. Engagement Spike Detection
            logger.info("Detecting engagement spikes...")
            
            # Find videos with unusually high engagement
            avg_engagement = session.query(func.avg(YouTubeVideo.engagement_rate)).scalar() or 3.0
            high_engagement_videos = session.query(YouTubeVideo).filter(
                and_(
                    YouTubeVideo.engagement_rate > avg_engagement * 1.5,
                    YouTubeVideo.view_count > 10000,
                    YouTubeVideo.published_at >= datetime.now(timezone.utc) - timedelta(days=7)
                )
            ).all()
            
            for video in high_engagement_videos:
                ranking = VideoRanking(
                    video_id=video.id,
                    ranking_type='engagement_spike',
                    score=video.engagement_rate,
                    rank=0
                )
                session.add(ranking)
            
            # 3. Viral Potential Score
            logger.info("Calculating viral potential...")
            
            # Videos growing faster than channel average
            channel_avg_views = session.query(
                YouTubeVideo.channel_id,
                func.avg(YouTubeVideo.view_count).label('avg_views')
            ).group_by(YouTubeVideo.channel_id).subquery()
            
            viral_candidates = session.query(YouTubeVideo).join(
                channel_avg_views,
                YouTubeVideo.channel_id == channel_avg_views.c.channel_id
            ).filter(
                and_(
                    YouTubeVideo.view_count > channel_avg_views.c.avg_views * 2,
                    YouTubeVideo.published_at >= datetime.now(timezone.utc) - timedelta(days=3)
                )
            ).all()
            
            for video in viral_candidates:
                ranking = VideoRanking(
                    video_id=video.id,
                    ranking_type='viral_potential',
                    score=video.view_count,
                    rank=0
                )
                session.add(ranking)
            
            session.commit()
            
            # Update ranks
            self._update_ranking_positions(session)
    
    def _update_ranking_positions(self, session):
        """Update rank positions for all ranking types."""
        ranking_types = ['hourly_velocity', 'engagement_spike', 'viral_potential']
        
        for ranking_type in ranking_types:
            # Get rankings ordered by score
            rankings = session.query(VideoRanking).filter_by(
                ranking_type=ranking_type
            ).order_by(VideoRanking.score.desc()).all()
            
            # Update ranks
            for i, ranking in enumerate(rankings, 1):
                ranking.rank = i
        
        session.commit()
    
    def get_trending_report(self):
        """Generate trending content report."""
        with SessionLocal() as session:
            report = {
                'timestamp': datetime.now().isoformat(),
                'trending_now': [],
                'rising_fast': [],
                'viral_potential': []
            }
            
            # Get top trending by velocity
            velocity_rankings = session.query(VideoRanking).filter_by(
                ranking_type='hourly_velocity'
            ).order_by(VideoRanking.rank).limit(10).all()
            
            for ranking in velocity_rankings:
                video = ranking.video
                report['trending_now'].append({
                    'title': video.title,
                    'channel': video.channel.title,
                    'views': video.view_count,
                    'hourly_velocity': ranking.score,
                    'published': video.published_at.isoformat(),
                    'url': f"https://youtube.com/watch?v={video.id}"
                })
            
            # Get engagement spikes
            engagement_rankings = session.query(VideoRanking).filter_by(
                ranking_type='engagement_spike'
            ).order_by(VideoRanking.rank).limit(10).all()
            
            for ranking in engagement_rankings:
                video = ranking.video
                report['rising_fast'].append({
                    'title': video.title,
                    'channel': video.channel.title,
                    'engagement_rate': ranking.score,
                    'views': video.view_count,
                    'url': f"https://youtube.com/watch?v={video.id}"
                })
            
            # Get viral potential
            viral_rankings = session.query(VideoRanking).filter_by(
                ranking_type='viral_potential'
            ).order_by(VideoRanking.rank).limit(10).all()
            
            for ranking in viral_rankings:
                video = ranking.video
                report['viral_potential'].append({
                    'title': video.title,
                    'channel': video.channel.title,
                    'views': video.view_count,
                    'published': video.published_at.isoformat(),
                    'url': f"https://youtube.com/watch?v={video.id}"
                })
            
            return report
    
    def monitor_real_time(self):
        """Check for trending content every hour."""
        logger.info("Checking for trending content...")
        
        # Get videos published in last 24 hours
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        
        trending_search_terms = [
            "golf viral today",
            "golf trending now",
            f"golf {datetime.now().strftime('%B %Y')}",
            "PGA tour today",
            "golf highlights today"
        ]
        
        for term in trending_search_terms:
            try:
                videos = self.directory.youtube_client.search_golf_videos(
                    query=term,
                    max_results=10,
                    order="viewCount",
                    published_after=cutoff
                )
                
                with SessionLocal() as session:
                    for video_data in videos:
                        try:
                            self.directory._upsert_video(session, video_data)
                            session.commit()
                        except Exception as e:
                            session.rollback()
                            
            except Exception as e:
                logger.error(f"Error searching for {term}: {e}")
        
        # Recalculate trending scores
        self.calculate_trending_scores()


def check_trending():
    """Run trending detection."""
    detector = TrendingDetector()
    detector.monitor_real_time()
    report = detector.get_trending_report()
    
    print("\n=== TRENDING GOLF CONTENT ===")
    print(f"Report generated: {report['timestamp']}\n")
    
    if report['trending_now']:
        print("🔥 TRENDING NOW (Highest view velocity):")
        for i, video in enumerate(report['trending_now'][:5], 1):
            print(f"{i}. {video['title']}")
            print(f"   {video['views']:,} views | {video['hourly_velocity']:.0f} views/hour")
            print(f"   {video['url']}\n")
    
    if report['rising_fast']:
        print("\n📈 HIGH ENGAGEMENT (Going viral):")
        for i, video in enumerate(report['rising_fast'][:5], 1):
            print(f"{i}. {video['title']}")
            print(f"   {video['engagement_rate']:.2f}% engagement | {video['views']:,} views")
            print(f"   {video['url']}\n")
    
    return report


if __name__ == "__main__":
    check_trending()