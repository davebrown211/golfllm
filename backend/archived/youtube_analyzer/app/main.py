from dotenv import load_dotenv
load_dotenv()

import logging
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, HttpUrl
from sqlalchemy.orm import Session
from .worker import process_video, process_video_direct
from .database import engine, Base, get_db
from .models import VideoAnalysis

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="YouTube Golf Performance Analyzer",
    description="An API to analyze YouTube golf videos using Gemini.",
    version="1.0.0",
)


class VideoSubmissionRequest(BaseModel):
    youtube_url: HttpUrl

class TaskResponse(BaseModel):
    task_id: str


@app.get("/")
async def root():
    return {"message": "Welcome to the YouTube Golf Performance Analyzer API."}


@app.post("/analyze-video/", response_model=TaskResponse)
async def submit_video_for_analysis(
    request: VideoSubmissionRequest,
    force: bool = False,
    persist_files: bool = False,
    db: Session = Depends(get_db)
):
    """
    Accepts a YouTube URL, checks if it has been analyzed,
    adds it to the processing queue if not, and returns a task ID.
    A `force=true` query parameter can be used to re-run analysis.
    A `persist_files=true` query parameter saves files for re-analysis.
    """
    logger.info(f"Received request for URL: {request.youtube_url}, force={force}, persist_files={persist_files}")
    video_url_str = str(request.youtube_url)
    analysis = db.query(VideoAnalysis).filter(VideoAnalysis.youtube_url == video_url_str).first()

    if analysis and not force:
        logger.warning(f"Duplicate request for URL: {video_url_str}. Current status: {analysis.status}. Use force=true to re-run.")
        return {"task_id": analysis.task_id, "status": f"DUPLICATE - Current status is {analysis.status}"}

    # If the analysis doesn't exist, create it
    if not analysis:
        logger.info(f"No existing record found for {video_url_str}. Creating new record.")
        analysis = VideoAnalysis(youtube_url=video_url_str)
        db.add(analysis)
        db.commit()
        db.refresh(analysis)

    # At this point, we have an `analysis` object, either new or pre-existing (with force=true)
    # We can now queue the task and update the record.
    analysis.status = "QUEUED"
    db.commit()

    logger.info(f"Dispatching direct video analysis task to Celery for analysis ID: {analysis.id}...")
    task = process_video_direct.delay(
        analysis_id=analysis.id,
        youtube_url=video_url_str,
        persist_files=persist_files
    )
    
    analysis.task_id = task.id
    db.commit()
    logger.info(f"Direct analysis task dispatched with ID: {task.id}")

    return {"task_id": task.id, "status": "QUEUED"} 