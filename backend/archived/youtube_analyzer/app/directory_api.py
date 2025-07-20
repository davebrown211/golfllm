"""
FastAPI endpoints for the Golf YouTube Directory
"""

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from youtube_analyzer.app.golf_directory import GolfDirectory

app = FastAPI(title="Golf YouTube Directory API", version="2.0")

# Add CORS middleware to allow frontend connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

directory = GolfDirectory()


class VideoRanking(BaseModel):
    rank: int
    title: str
    channel: str
    views: str
    likes: str
    engagement: str
    published: str
    url: str
    thumbnail: str


class ChannelStats(BaseModel):
    channel: str
    videos_tracked: int
    total_views: str
    avg_engagement: str
    url: str


class SearchResult(BaseModel):
    title: str
    channel: str
    views: str
    category: str
    published: str
    url: str


@app.get("/")
def read_root():
    return {
        "name": "Golf YouTube Directory API",
        "version": "2.0",
        "description": "A metadata-driven golf content discovery platform",
        "endpoints": {
            "/rankings/{ranking_type}": "Get video rankings",
            "/channels/top": "Get top golf channels",
            "/search": "Search golf videos",
            "/update": "Update video catalog (requires API key)"
        }
    }


@app.get("/rankings/{ranking_type}", response_model=List[VideoRanking])
def get_rankings(
    ranking_type: str = "daily_trending",
    limit: int = Query(20, ge=1, le=100)
):
    """
    Get video rankings by type.
    
    Types:
    - daily_trending: Videos published today with most views
    - weekly_trending: Videos with highest view velocity this week
    - all_time_views: Most viewed golf videos of all time
    - high_engagement: Videos with highest like/comment ratio
    """
    valid_types = ['daily_trending', 'weekly_trending', 'all_time_views', 'high_engagement']
    if ranking_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"Invalid ranking type. Choose from: {valid_types}")
    
    return directory.get_rankings(ranking_type, limit)


@app.get("/channels/top", response_model=List[ChannelStats])
def get_top_channels(limit: int = Query(20, ge=1, le=100)):
    """
    Get top golf channels by total video views.
    """
    return directory.get_top_channels(limit)


@app.get("/search", response_model=List[SearchResult])
def search_videos(
    q: str = Query(..., description="Search query"),
    category: Optional[str] = Query(None, description="Filter by category")
):
    """
    Search for golf videos.
    
    Categories: instruction, equipment, tour, highlights, vlog, news, general
    """
    if len(q) < 2:
        raise HTTPException(status_code=400, detail="Query must be at least 2 characters")
    
    results = directory.search_videos(q, category)
    if not results:
        raise HTTPException(status_code=404, detail="No videos found")
    
    return results


@app.post("/update")
async def update_catalog(background_tasks: BackgroundTasks):
    """
    Update the video catalog with latest data from YouTube.
    Requires YOUTUBE_API_KEY or GOOGLE_API_KEY environment variable.
    """
    if not directory.youtube_client:
        raise HTTPException(
            status_code=503,
            detail="YouTube API key not configured. Set YOUTUBE_API_KEY or GOOGLE_API_KEY environment variable."
        )
    
    background_tasks.add_task(update_catalog_task)
    return {"message": "Catalog update started", "status": "processing"}


def update_catalog_task():
    """Background task to update catalog."""
    directory.update_video_catalog()
    directory.update_rankings()


@app.get("/stats")
def get_directory_stats():
    """
    Get statistics about the directory.
    """
    with directory.SessionLocal() as session:
        from youtube_analyzer.app.models_metadata import YouTubeVideo, YouTubeChannel
        
        video_count = session.query(YouTubeVideo).count()
        channel_count = session.query(YouTubeChannel).count()
        
        # Get category breakdown
        from sqlalchemy import func
        category_stats = session.query(
            YouTubeVideo.category,
            func.count(YouTubeVideo.id)
        ).group_by(YouTubeVideo.category).all()
        
        return {
            "total_videos": video_count,
            "total_channels": channel_count,
            "categories": {cat: count for cat, count in category_stats},
            "last_updated": datetime.now().isoformat()
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)