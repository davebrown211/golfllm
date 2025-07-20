from dotenv import load_dotenv
load_dotenv()

import logging
import os
import subprocess
import tempfile
import yt_dlp
import json
import re
from celery import Celery, group, chord
from urllib.parse import urlparse, parse_qs

from .database import SessionLocal
from .models import VideoAnalysis
from .ai_processing import analyze_frame, transcribe_audio, synthesize_results, extract_character_traits, analyze_golf_video_direct
from .vtt_parser import parse_vtt_file
from .character_processing_v2 import process_character_analysis

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

celery_app = Celery(
    "youtube_analyzer.app.worker",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

celery_app.conf.update(
    task_track_started=True,
    imports=('youtube_analyzer.app.worker',),
    task_default_queue='celery',
)

@celery_app.task(name='app.worker.analyze_frame_task')
def analyze_frame_task(frame_path: str):
    """A new Celery task to analyze a single frame."""
    logger.info(f"Analyzing frame: {frame_path}")
    prompt = """
You are an expert data extractor for sports broadcasts.
Analyze the provided image from a golf video. Your task is to determine if it contains an on-screen graphic (like a scoreboard, leaderboard, or player statistics).

If a graphic is present, return a JSON object with `has_graphic` as `true` and use Optical Character Recognition (OCR) to extract ALL text from the graphic into the `extracted_text` field.

If no graphic is present, return a JSON object with `has_graphic` as `false`.

Example for a frame with a graphic:
{
  "has_graphic": true,
  "extracted_text": "LEADERBOARD\n1. T. Woods -12\n2. R. McIlroy -10\n3. J. Spieth -9"
}

Example for a frame without a graphic:
{
  "has_graphic": false
}
"""
    
    try:
        raw_analysis_result = analyze_frame(frame_path, prompt)
        logger.debug(f"Raw AI response for {frame_path}: {raw_analysis_result}")
        
        # Clean up potential markdown formatting
        match = re.search(r"```(json)?\n(.*)```", raw_analysis_result, re.DOTALL)
        if match:
            json_str = match.group(2).strip()
        else:
            json_str = raw_analysis_result.strip()

        try:
            analysis_json = json.loads(json_str)
            if analysis_json.get("has_graphic"):
                extracted_text = analysis_json.get("extracted_text")
                logger.info(f"Frame {frame_path} contained graphic with text: {extracted_text[:100]}...")
                return extracted_text
            else:
                logger.debug(f"Frame {frame_path} determined to have no graphic")
                return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON for frame {frame_path}. Raw response: {raw_analysis_result[:500]}...")
            logger.error(f"JSON parse error: {e}")
            # Try to extract text anyway if the response looks like it contains relevant content
            if any(keyword in raw_analysis_result.lower() for keyword in ['hole', 'par', 'team', 'score', 'yd']):
                logger.warning(f"JSON failed but content looks relevant, returning raw text for {frame_path}")
                return raw_analysis_result
            return None
            
    except Exception as e:
        logger.error(f"Error analyzing frame {frame_path}: {e}", exc_info=True)
        return None

@celery_app.task(name='app.worker.analyze_appearance_task')  
def analyze_appearance_task(frame_path: str):
    """Analyze a frame specifically for character appearance details."""
    logger.info(f"Analyzing appearance in frame: {frame_path}")
    prompt = """
You are a character appearance analyst for video content.
Analyze this golf video frame to identify and describe any people visible in detail.

Focus on extracting visual characteristics that would be useful for character design:

PHYSICAL APPEARANCE:
- Hair color, style, length
- Facial hair (beard, mustache, etc.)
- Build/physique (tall, short, athletic, etc.)
- Distinctive facial features

CLOTHING & STYLE:
- Shirt/polo colors and brands visible
- Pants/shorts style and color
- Hat/visor style, color, brand logos
- Golf shoes style and color
- Any distinctive clothing patterns or logos

ACCESSORIES:
- Sunglasses style
- Watches, jewelry
- Golf gloves color/style
- Any other distinctive accessories

EQUIPMENT:
- Golf club brands visible
- Golf bag color/style
- Any distinctive equipment

BODY LANGUAGE:
- Posture (upright, relaxed, tense)
- Distinctive gestures or mannerisms visible
- General demeanor

Return JSON format:
{
  "people_found": true/false,
  "character_descriptions": [
    {
      "position_description": "left side of frame",
      "clothing": "detailed clothing description",
      "physical_traits": "hair, build, distinctive features",
      "accessories": "glasses, watch, etc.",
      "equipment": "golf equipment visible",
      "body_language": "posture and mannerisms"
    }
  ]
}

If no people are clearly visible, return {"people_found": false}
"""
    
    try:
        raw_analysis_result = analyze_frame(frame_path, prompt)
        logger.debug(f"Raw appearance analysis for {frame_path}: {raw_analysis_result}")
        
        # Clean up potential markdown formatting
        match = re.search(r"```(json)?\\n(.*)```", raw_analysis_result, re.DOTALL)
        if match:
            json_str = match.group(2).strip()
        else:
            json_str = raw_analysis_result.strip()

        try:
            analysis_json = json.loads(json_str)
            if analysis_json.get("people_found"):
                descriptions = analysis_json.get("character_descriptions", [])
                logger.info(f"Frame {frame_path} found {len(descriptions)} people with appearance details")
                return descriptions
            else:
                logger.debug(f"Frame {frame_path} - no people found")
                return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse appearance JSON for frame {frame_path}: {e}")
            return None
            
    except Exception as e:
        logger.error(f"Error analyzing appearance in frame {frame_path}: {e}", exc_info=True)
        return None

@celery_app.task(name='app.worker.synthesize_and_save_task')
def synthesize_and_save_task(ocr_results: list[str], transcript: str, analysis_id: int, caption_info: dict = None):
    """
    Callback task to synthesize results and update the database.
    Receives results from all frame analysis tasks.
    """
    logger.info(f"[{analysis_id}] All frames analyzed. Starting synthesis.")
    db = SessionLocal()
    try:
        analysis = db.query(VideoAnalysis).filter(VideoAnalysis.id == analysis_id).first()
        if not analysis:
            logger.error(f"[{analysis_id}] Analysis not found in synthesis task.")
            return

        successful_extractions = [text for text in ocr_results if text]
        logger.info(f"[{analysis_id}] Synthesizing text from {len(successful_extractions)} frames and transcript.")

        # Extract golf scoring data
        final_summary = synthesize_results(transcript, successful_extractions)
        logger.info(f"[{analysis_id}] Final Synthesized Analysis:\n{final_summary}")
        
        # Extract character personality traits for parody creation
        logger.info(f"[{analysis_id}] Extracting character traits...")
        character_traits = extract_character_traits(transcript, successful_extractions)
        logger.info(f"[{analysis_id}] Character Traits Analysis:\n{character_traits}")
        
        analysis.result = final_summary
        analysis.character_analysis = character_traits
        
        # Process character data and update/create character records
        logger.info(f"[{analysis_id}] Processing character data into database...")
        process_character_analysis(analysis_id, character_traits)
        
        analysis.status = "COMPLETE"
        
        # Store caption information if provided
        if caption_info:
            analysis.captions_found = caption_info.get('found', False)
            analysis.captions_preview = caption_info.get('preview', None)
            analysis.transcript_source = caption_info.get('source', 'none')
            logger.info(f"[{analysis_id}] Caption info: found={analysis.captions_found}, source={analysis.transcript_source}")
        
        db.commit()
        logger.info(f"[{analysis_id}] Analysis complete and saved to DB.")

    except Exception as e:
        logger.error(f"[{analysis_id}] Error in synthesis task: {e}", exc_info=True)
        if 'analysis' in locals() and analysis:
            analysis.status = "FAILED"
            db.commit()
    finally:
        db.close()

def get_video_duration(video_path: str) -> float:
    """Gets the duration of a video file in seconds using ffprobe."""
    command = [
        'ffprobe',
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        video_path
    ]
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True, timeout=1800)
        duration = float(result.stdout.strip())
        logger.info(f"Video duration determined to be: {duration} seconds.")
        return duration
    except (subprocess.CalledProcessError, ValueError) as e:
        logger.error(f"Failed to get video duration for {video_path}: {e}")
        if isinstance(e, subprocess.CalledProcessError):
             logger.error(f"ffprobe stdout: {e.stdout}")
             logger.error(f"ffprobe stderr: {e.stderr}")
        return 0.0

def get_video_id(url):
    """A simple function to extract the video ID from a YouTube URL."""
    if 'youtu.be' in url:
        return url.split('/')[-1]
    query = urlparse(url).query
    return parse_qs(query).get('v', [None])[0]

def extract_audio(video_path: str, output_dir: str, video_id: str) -> str:
    """Extracts audio from a video file using FFmpeg."""
    audio_filename = f"{video_id}.mp3"
    audio_path = os.path.join(output_dir, audio_filename)
    logger.info(f"Starting audio extraction for {video_path}")
    command = ['ffmpeg', '-y', '-i', video_path, '-q:a', '0', '-map', 'a', audio_path]
    try:
        logger.info(f"Running ffmpeg (audio) command: {' '.join(command)}")
        # Using a long timeout to handle large files
        result = subprocess.run(command, check=True, capture_output=True, text=True, timeout=3600)
        logger.info("ffmpeg (audio) completed successfully.")
        logger.debug(f"ffmpeg (audio) stdout:\n{result.stdout}")
        logger.debug(f"ffmpeg (audio) stderr:\n{result.stderr}")
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg (audio) failed with exit code {e.returncode}")
        logger.error(f"ffmpeg (audio) stdout:\n{e.stdout}")
        logger.error(f"ffmpeg (audio) stderr:\n{e.stderr}")
        raise
    
    logger.info(f"Audio extracted to: {audio_path}")
    return audio_path

def extract_frames(video_path: str, output_dir: str) -> str:
    """Extracts frames from a video file using FFmpeg."""
    frames_dir = os.path.join(output_dir, "frames")
    os.makedirs(frames_dir, exist_ok=True)

    logger.info(f"Starting frame extraction for {video_path}")
    # Extract 1 frame every 30 seconds (since we have captions, we need fewer frames for OCR)
    # For long videos, this prevents excessive processing while still capturing scoreboards
    command = [
        'ffmpeg', '-y', 
        '-hwaccel', 'videotoolbox',  # Use hardware acceleration if available
        '-i', video_path, 
        '-vf', 'scale=1280:720,fps=1/30',  # Lower resolution, much fewer frames
        '-q:v', '8',  # Good quality but faster processing
        os.path.join(frames_dir, 'frame_%04d.jpg')
    ]
    try:
        logger.info(f"Running ffmpeg (frames) command: {' '.join(command)}")
        # Using a long timeout to handle large files
        result = subprocess.run(command, check=True, capture_output=True, text=True, timeout=3600)
        logger.info("ffmpeg (frames) completed successfully.")
        logger.debug(f"ffmpeg (frames) stdout:\n{result.stdout}")
        logger.debug(f"ffmpeg (frames) stderr:\n{result.stderr}")
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg (frames) failed with exit code {e.returncode}")
        logger.error(f"ffmpeg (frames) stdout:\n{e.stdout}")
        logger.error(f"ffmpeg (frames) stderr:\n{e.stderr}")
        raise

    logger.info(f"Frames extracted to: {frames_dir}")
    return frames_dir

def _download_and_process_video(youtube_url: str, target_dir: str) -> (str, str, str, str | None):
    """Downloads and processes a video, saving assets to the target directory."""
    try:
        logger.info(f"Downloading video to directory: {target_dir}")
        video_id = get_video_id(youtube_url)
        if not video_id:
            raise ValueError("Could not extract video ID.")

        video_path = os.path.join(target_dir, f"{video_id}.mp4")
        
        # Always try to download captions first, then decide on video format
        logger.info("Attempting to download captions...")
        captions_available = False
        
        # Try to download captions first
        caption_opts = {
            'skip_download': True,
            'writeautomaticsub': True,
            'writesubtitles': True,
            'subtitleslangs': ['en', 'en-US', 'en-GB'],
            'subtitlesformat': 'vtt',
            'outtmpl': video_path,
            'quiet': False,
        }
        
        try:
            with yt_dlp.YoutubeDL(caption_opts) as ydl:
                info = ydl.extract_info(youtube_url, download=True)
                
                # Check if any caption files were downloaded
                caption_variants = [
                    f"{video_id}.en.vtt",
                    f"{video_id}.en-US.vtt", 
                    f"{video_id}.en-GB.vtt"
                ]
                
                for variant in caption_variants:
                    full_path = os.path.join(target_dir, variant)
                    if os.path.exists(full_path) and os.path.getsize(full_path) > 100:  # Must be substantial
                        captions_available = True
                        logger.info(f"Captions successfully downloaded: {variant} ({os.path.getsize(full_path)} bytes)")
                        break
                        
                if not captions_available:
                    logger.error("No caption files found after download attempt")
                    
        except Exception as e:
            logger.error(f"Caption download failed: {e}")
        
        # Error out if no captions are available
        if not captions_available:
            raise ValueError(f"No captions available for video {youtube_url}. Captions are required for accurate golf analysis.")
        
        # Download video only (no audio needed since we have captions)
        logger.info("Captions confirmed - downloading video only")
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]/best[ext=mp4]',
            'outtmpl': video_path,
            'quiet': False,
            'ignoreconfig': True,
            'nocheckcertificate': True,
            'no_cachedir': True,
            'progress': True,
        }
        
        logger.info(f"yt-dlp options: {json.dumps(ydl_opts, indent=2)}")

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([youtube_url])
        
        logger.info(f"Video download reported as complete. Verifying file at: {video_path}")
        if not os.path.exists(video_path):
             raise FileNotFoundError(f"yt-dlp claims success, but file does not exist: {video_path}")

        duration = get_video_duration(video_path)
        if duration == 0.0:
            raise ValueError("Could not determine video duration, processing cannot continue.")

        # --- FFmpeg processing steps ---
        # Skip audio extraction since captions are required
        logger.info("Skipping audio extraction - using captions only")
        audio_path = None
        frames_dir = extract_frames(video_path, target_dir)
        
        # Check for the downloaded caption files (try multiple variants)
        caption_variants = [
            f"{video_id}.en.vtt",
            f"{video_id}.en-US.vtt", 
            f"{video_id}.en-GB.vtt",
            f"{video_id}.live_chat.json"  # Sometimes live chat is available
        ]
        
        caption_path = None
        for variant in caption_variants:
            full_path = os.path.join(target_dir, variant)
            if os.path.exists(full_path):
                caption_path = full_path
                logger.info(f"Found caption file: {variant}")
                break
        
        if not caption_path:
            logger.info("No caption files found for this video.")
            # List all files in directory for debugging
            all_files = os.listdir(target_dir)
            vtt_files = [f for f in all_files if f.endswith('.vtt')]
            logger.info(f"All files in target directory: {all_files}")
            logger.info(f"VTT files found: {vtt_files}")

        return video_id, audio_path, frames_dir, caption_path
    except Exception as e:
        logger.error(f"An error occurred in _download_and_process_video: {e}", exc_info=True)
        raise

def _perform_ai_analysis(analysis_id: int, video_id: str, audio_path: str, frames_dir: str, caption_path: str | None):
    """Sets up and launches the asynchronous analysis pipeline."""
    logger.info(f"[{analysis_id}] Starting AI analysis pipeline for video_id: {video_id}")
    
    # 1. Prioritize captions over transcription
    transcript = ""
    caption_info = {
        'found': False,
        'preview': None,
        'source': 'none'
    }
    
    if caption_path and os.path.exists(caption_path):
        logger.info(f"[{analysis_id}] Reading captions from: {caption_path}")
        try:
            with open(caption_path, 'r', encoding='utf-8') as f:
                vtt_content = f.read()
            # Parse VTT to extract clean text
            transcript = parse_vtt_file(vtt_content)
            logger.info(f"[{analysis_id}] Parsed Caption Text ({len(transcript)} chars): {transcript[:500]}...")
            
            # Store caption info
            caption_info['found'] = True
            caption_info['preview'] = transcript[:1000] if transcript else "VTT file found but no text extracted"
            caption_info['source'] = 'captions'
            
        except Exception as e:
            logger.error(f"[{analysis_id}] Error parsing VTT file: {e}")
            caption_info['preview'] = f"VTT file found but parse error: {str(e)}"
            # If VTT parsing fails, this is a critical error since we require captions
            logger.error(f"[{analysis_id}] Critical error: VTT file found but cannot be parsed")
            raise ValueError(f"Caption file found but corrupted or unreadable: {e}")
    else:
        # This should never happen since we error out if no captions are found during download
        logger.error(f"[{analysis_id}] Critical error: No caption file found in analysis phase")
        raise ValueError("No caption file found - this should have been caught during download")

    # 2. Define the parallel frame analysis tasks
    if os.path.exists(frames_dir):
        frame_files = sorted([os.path.join(frames_dir, f) for f in os.listdir(frames_dir) if f.endswith('.jpg')])
        
        # Define the group of parallel tasks for the chord header
        header = group(analyze_frame_task.s(frame_path) for frame_path in frame_files)
        
        # Define the callback task that will run after the header is complete
        callback = synthesize_and_save_task.s(transcript=transcript, analysis_id=analysis_id, caption_info=caption_info)
        
        # Execute the chord
        chord(header)(callback)
        logger.info(f"[{analysis_id}] Launched a chord of {len(frame_files)} frame analysis tasks.")
    else:
        logger.warning(f"[{analysis_id}] Frames directory not found. Cannot start analysis.")
        # If there are no frames, we should probably mark the task as failed.
        db = SessionLocal()
        try:
            analysis = db.query(VideoAnalysis).filter(VideoAnalysis.id == analysis_id).first()
            if analysis:
                analysis.status = "FAILED"
                db.commit()
        finally:
            db.close()

@celery_app.task(bind=True, name='app.worker.process_video_direct')
def process_video_direct(self, analysis_id: int, youtube_url: str, persist_files: bool = False):
    """
    Downloads a video from YouTube and analyzes it directly with Gemini 1.5 Pro.
    This is the new simplified approach that doesn't require frame extraction or transcription.
    """
    logger.info(f"Worker received direct video analysis task for analysis ID: {analysis_id}")
    db = SessionLocal()

    base_data_dir = "video_data"
    persistent_dir = os.path.join(base_data_dir, str(analysis_id))
    
    try:
        analysis = db.query(VideoAnalysis).filter(VideoAnalysis.id == analysis_id).first()
        if not analysis:
            logger.error(f"Analysis with ID {analysis_id} not found.")
            return

        analysis.status = "PROCESSING"
        db.commit()

        # Create directory for video download
        os.makedirs(persistent_dir, exist_ok=True)
        
        try:
            # Download video only (no need for captions, audio extraction, or frame extraction)
            video_id = get_video_id(youtube_url)
            if not video_id:
                raise ValueError("Could not extract video ID.")

            video_path = os.path.join(persistent_dir, f"{video_id}.mp4")
            
            logger.info("Downloading video for direct analysis...")
            ydl_opts = {
                'format': 'best[ext=mp4]/best',
                'outtmpl': video_path,
                'quiet': False,
                'ignoreconfig': True,
                'nocheckcertificate': True,
                'no_cachedir': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([youtube_url])
            
            if not os.path.exists(video_path):
                raise FileNotFoundError(f"Video download failed: {video_path}")

            logger.info(f"Video downloaded successfully: {video_path}")
            
            # Analyze video directly with Gemini 1.5 Pro
            logger.info(f"[{analysis_id}] Starting direct video analysis...")
            golf_analysis = analyze_golf_video_direct(video_path)
            logger.info(f"[{analysis_id}] Golf Analysis Complete:\n{golf_analysis}")
            
            # Store results
            analysis.result = golf_analysis
            analysis.status = "COMPLETE"
            db.commit()
            
            logger.info(f"[{analysis_id}] Analysis complete and saved to DB.")
            
            # Clean up video file if not persisting
            if not persist_files:
                try:
                    os.remove(video_path)
                    logger.info(f"Cleaned up video file: {video_path}")
                except Exception as e:
                    logger.warning(f"Could not clean up video file: {e}")

        except Exception as e:
            logger.error(f"An error occurred during processing for analysis ID {analysis_id}: {e}", exc_info=True)
            analysis.status = "FAILED"
            db.commit()
            return f"Failed to process video: {youtube_url}"
            
    except Exception as e:
        logger.error(f"An error occurred in process_video_direct for analysis ID {analysis_id}: {e}", exc_info=True)
        db = SessionLocal()
        try:
            analysis = db.query(VideoAnalysis).filter(VideoAnalysis.id == analysis_id).first()
            if analysis:
                analysis.status = "FAILED"
                db.commit()
        finally:
            db.close()
    finally:
        if 'db' in locals() and db.is_active:
            db.close()

@celery_app.task(bind=True, name='app.worker.process_video')
def process_video(self, analysis_id: int, youtube_url: str, skip_download: bool = False, persist_files: bool = False):
    """
    LEGACY METHOD - Downloads a video from YouTube, processes it, and updates the database.
    NOTE: This method is deprecated in favor of process_video_direct()
    """
    logger.warning(f"Using legacy process_video method for analysis ID: {analysis_id}. Consider using process_video_direct instead.")
    
    logger.info(f"Worker received task for analysis ID: {analysis_id}. persist_files={persist_files}, skip_download={skip_download}")
    db = SessionLocal()

    base_data_dir = "video_data"
    persistent_dir = os.path.join(base_data_dir, str(analysis_id))
    
    try:
        analysis = db.query(VideoAnalysis).filter(VideoAnalysis.id == analysis_id).first()
        if not analysis:
            logger.error(f"Analysis with ID {analysis_id} not found.")
            return

        analysis.status = "PROCESSING"
        db.commit()

        target_dir = None
        if skip_download:
            logger.info(f"[{analysis_id}] Re-analyzing. Using persistent directory: {persistent_dir}")
            target_dir = persistent_dir
        else:
            # Always use persistent files since async tasks need access to frames
            logger.info(f"[{analysis_id}] Using persistent directory: {persistent_dir}")
            os.makedirs(persistent_dir, exist_ok=True)
            target_dir = persistent_dir

        try:
            if skip_download:
                video_id = get_video_id(youtube_url)
                frames_dir = os.path.join(target_dir, "frames")
                
                # Look for captions (required)
                caption_path = None
                caption_variants = [
                    f"{video_id}.en.vtt",
                    f"{video_id}.en-US.vtt",
                    f"{video_id}.en-GB.vtt"
                ]
                for variant in caption_variants:
                    full_path = os.path.join(target_dir, variant)
                    if os.path.exists(full_path) and os.path.getsize(full_path) > 100:
                        caption_path = full_path
                        logger.info(f"Found existing caption file: {variant}")
                        break
                
                # Error if no captions found
                if not caption_path:
                    raise ValueError(f"No caption files found in {target_dir} for re-analysis. Captions are required.")
                
                # No audio needed since we have captions
                audio_path = None
            else:
                 video_id, audio_path, frames_dir, caption_path = _download_and_process_video(youtube_url, target_dir)
            
            # Launch the async pipeline
            _perform_ai_analysis(analysis_id, video_id, audio_path, frames_dir, caption_path)

        except Exception as e:
            logger.error(f"An error occurred during processing for analysis ID {analysis_id}: {e}", exc_info=True)
            analysis.status = "FAILED"
            db.commit()
            return f"Failed to process video: {youtube_url}"
        finally:
            # Note: We're using persistent directories now to avoid cleanup issues with async tasks
            pass
    except Exception as e:
        logger.error(f"An error occurred in process_video for analysis ID {analysis_id}: {e}", exc_info=True)
        # We might not have an 'analysis' object if the DB query fails
        db = SessionLocal()
        try:
            analysis = db.query(VideoAnalysis).filter(VideoAnalysis.id == analysis_id).first()
            if analysis:
                analysis.status = "FAILED"
                db.commit()
        finally:
            db.close()
    finally:
        if 'db' in locals() and db.is_active:
            db.close() 