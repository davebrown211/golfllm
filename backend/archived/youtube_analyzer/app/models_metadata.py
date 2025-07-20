from sqlalchemy import Column, Integer, String, DateTime, Float, BigInteger, Boolean, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class YouTubeChannel(Base):
    __tablename__ = 'youtube_channels'
    
    id = Column(String, primary_key=True)  # YouTube channel ID
    title = Column(String, nullable=False)
    description = Column(String)
    subscriber_count = Column(BigInteger, default=0)
    video_count = Column(Integer, default=0)
    view_count = Column(BigInteger, default=0)
    thumbnail_url = Column(String)
    
    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    videos = relationship("YouTubeVideo", back_populates="channel")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_channel_subscribers', 'subscriber_count'),
        Index('idx_channel_updated', 'updated_at'),
    )


class YouTubeVideo(Base):
    __tablename__ = 'youtube_videos'
    
    id = Column(String, primary_key=True)  # YouTube video ID
    title = Column(String, nullable=False)
    description = Column(String)
    channel_id = Column(String, ForeignKey('youtube_channels.id'))
    
    # Timestamps
    published_at = Column(DateTime, nullable=False)
    discovered_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Statistics
    view_count = Column(BigInteger, default=0)
    like_count = Column(BigInteger, default=0)
    comment_count = Column(BigInteger, default=0)
    
    # Calculated metrics
    engagement_rate = Column(Float, default=0.0)  # (likes + comments) / views * 100
    view_velocity = Column(Float, default=0.0)  # views per day since upload
    
    # Video details
    duration_seconds = Column(Integer)  # Parsed from ISO 8601 duration
    thumbnail_url = Column(String)
    tags = Column(JSON)  # Store as JSON array
    
    # Categories
    category = Column(String)  # 'instruction', 'equipment', 'tour', etc.
    is_hd = Column(Boolean, default=False)
    
    # Relationships
    channel = relationship("YouTubeChannel", back_populates="videos")
    rankings = relationship("VideoRanking", back_populates="video")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_video_views', 'view_count'),
        Index('idx_video_published', 'published_at'),
        Index('idx_video_engagement', 'engagement_rate'),
        Index('idx_video_velocity', 'view_velocity'),
        Index('idx_video_category', 'category'),
        Index('idx_video_channel', 'channel_id'),
    )


class VideoRanking(Base):
    __tablename__ = 'video_rankings'
    
    id = Column(Integer, primary_key=True)
    video_id = Column(String, ForeignKey('youtube_videos.id'))
    ranking_type = Column(String)  # 'daily_views', 'weekly_trending', 'all_time_best', etc.
    rank = Column(Integer)
    score = Column(Float)  # Ranking score based on algorithm
    date = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    video = relationship("YouTubeVideo", back_populates="rankings")
    
    # Indexes
    __table_args__ = (
        Index('idx_ranking_type_date', 'ranking_type', 'date'),
        Index('idx_ranking_video', 'video_id'),
    )


class SearchQuery(Base):
    __tablename__ = 'search_queries'
    
    id = Column(Integer, primary_key=True)
    query = Column(String, nullable=False)
    category = Column(String)
    result_count = Column(Integer)
    executed_at = Column(DateTime, default=datetime.utcnow)
    
    # Track popular searches
    __table_args__ = (
        Index('idx_search_query', 'query'),
        Index('idx_search_executed', 'executed_at'),
    )