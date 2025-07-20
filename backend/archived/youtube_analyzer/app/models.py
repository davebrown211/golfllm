from sqlalchemy import Column, Integer, String, DateTime, Text, UniqueConstraint, Boolean, Float, ForeignKey, BigInteger, JSON, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base

class VideoAnalysis(Base):
    __tablename__ = "video_analyses"

    id = Column(Integer, primary_key=True, index=True)
    youtube_url = Column(String, unique=True, index=True, nullable=False)
    task_id = Column(String, index=True, nullable=True)
    status = Column(String, default="PENDING", nullable=False)
    result = Column(Text, nullable=True)
    captions_found = Column(Boolean, default=False, nullable=False)
    captions_preview = Column(Text, nullable=True)  # Store first 1000 chars of captions
    transcript_source = Column(String, nullable=True)  # 'captions', 'audio', or 'none'
    character_analysis = Column(Text, nullable=True)  # JSON string of character trait analysis
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (UniqueConstraint('youtube_url', name='_youtube_url_uc'),)

class Character(Base):
    __tablename__ = "characters"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    channel_name = Column(String, nullable=True)  # YouTube channel if known
    overall_notes = Column(Text, nullable=True)  # General notes about this person
    confirmed_identity = Column(Boolean, default=False)  # Manual verification this is correct person
    
    # Meta information
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    character_appearances = relationship("CharacterAppearance", back_populates="character")

class CharacterAppearance(Base):
    __tablename__ = "character_appearances"
    
    id = Column(Integer, primary_key=True, index=True)
    character_id = Column(Integer, ForeignKey("characters.id"), nullable=False)
    video_analysis_id = Column(Integer, ForeignKey("video_analyses.id"), nullable=False)
    
    # Personality traits (scale 1-10) - FROM AI ANALYSIS PER VIDEO
    confidence_level = Column(Float, nullable=True)
    humor_level = Column(Float, nullable=True)
    competitiveness = Column(Float, nullable=True)
    trash_talk_frequency = Column(Float, nullable=True)
    celebration_style = Column(String, nullable=True)  # "subdued", "animated", "excessive"
    
    # Speaking patterns - FROM THIS VIDEO
    catchphrases = Column(Text, nullable=True)  # JSON array of phrases from this video
    speaking_style = Column(String, nullable=True)  # "casual", "technical", "dramatic"
    notable_quotes = Column(Text, nullable=True)  # JSON array of specific quotes from this video
    profanity_usage = Column(Float, nullable=True)  # 1-10 scale
    accent_description = Column(String, nullable=True)
    
    # Golf-specific traits - FROM THIS VIDEO
    skill_level = Column(String, nullable=True)  # "amateur", "semi-pro", "pro"
    playing_style = Column(String, nullable=True)  # "aggressive", "conservative", "unpredictable"
    reaction_to_bad_shots = Column(String, nullable=True)  # "calm", "frustrated", "explosive"
    reaction_to_good_shots = Column(String, nullable=True)  # "humble", "confident", "showboat"
    
    # Physical/Visual traits - FROM THIS VIDEO
    appearance_description = Column(Text, nullable=True)  # Overall appearance in this video
    clothing_style = Column(Text, nullable=True)
    physical_build = Column(String, nullable=True)
    hair_facial_features = Column(Text, nullable=True)
    accessories = Column(Text, nullable=True)
    equipment_style = Column(Text, nullable=True)
    body_language = Column(Text, nullable=True)
    
    # Video-specific context
    performance_notes = Column(Text, nullable=True)  # How they played in this specific video
    team_dynamics = Column(Text, nullable=True)  # How they interacted with partners in this video
    signature_moments = Column(Text, nullable=True)  # JSON array of notable moments from this video
    comedy_potential = Column(Text, nullable=True)  # Parody angles from this video
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    character = relationship("Character", back_populates="character_appearances")
    video_analysis = relationship("VideoAnalysis")


# YouTube Metadata Tables
class YouTubeChannel(Base):
    __tablename__ = 'youtube_channels'
    
    id = Column(String, primary_key=True)  # YouTube channel ID
    title = Column(String, nullable=False)
    description = Column(Text)
    subscriber_count = Column(BigInteger, default=0)
    video_count = Column(Integer, default=0)
    view_count = Column(BigInteger, default=0)
    thumbnail_url = Column(String)
    
    # Tracking
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
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
    description = Column(Text)
    channel_id = Column(String, ForeignKey('youtube_channels.id'))
    
    # Link to existing video analysis if available
    video_analysis_id = Column(Integer, ForeignKey('video_analyses.id'), nullable=True)
    
    # Timestamps
    published_at = Column(DateTime(timezone=True), nullable=False)
    discovered_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
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
    video_analysis = relationship("VideoAnalysis", backref="youtube_metadata")
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
    date = Column(DateTime(timezone=True), server_default=func.now())
    
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
    executed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Track popular searches
    __table_args__ = (
        Index('idx_search_query', 'query'),
        Index('idx_search_executed', 'executed_at'),
    ) 