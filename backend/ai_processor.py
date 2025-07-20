"""
AI Processing Module - Python Implementation
Matches the refined Next.js AI generation logic exactly
"""

import os
import logging
import tempfile
import subprocess
import re
from typing import Optional, Dict, Any
from pathlib import Path
import google.generativeai as genai
try:
    from elevenlabs import ElevenLabs
    client = ElevenLabs()
except ImportError:
    # Fallback for older version
    from elevenlabs import generate, save
import requests

logger = logging.getLogger(__name__)

class AIProcessor:
    """AI processing for video analysis and audio generation"""
    
    def __init__(self, 
                 google_api_key: Optional[str] = None,
                 elevenlabs_api_key: Optional[str] = None):
        
        # Configure Google Gemini
        if google_api_key:
            genai.configure(api_key=google_api_key)
            self.genai_model = genai.GenerativeModel('gemini-1.5-pro')
        else:
            self.genai_model = None
            logger.warning("Google API key not provided - AI analysis disabled")
        
        # Configure ElevenLabs
        self.elevenlabs_api_key = elevenlabs_api_key
        if not elevenlabs_api_key:
            logger.warning("ElevenLabs API key not provided - audio generation disabled")
    
    def download_transcript(self, video_id: str) -> Optional[str]:
        """
        Download video transcript using YouTube Data API v3 (fallback to description)
        """
        try:
            # Import here to avoid circular dependency
            from googleapiclient.discovery import build
            
            # Use the same API key as for video data
            youtube_api_key = os.environ.get('YOUTUBE_API_KEY') or os.environ.get('GOOGLE_API_KEY')
            if not youtube_api_key:
                logger.error("No YouTube API key available")
                return None
                
            youtube = build('youtube', 'v3', developerKey=youtube_api_key)
            
            # Get video details and use description as content for AI analysis
            video_response = youtube.videos().list(
                part='snippet',
                id=video_id
            ).execute()
            
            if video_response['items']:
                video_data = video_response['items'][0]['snippet']
                title = video_data['title']
                description = video_data['description']
                
                # Create a pseudo-transcript from title and description
                content = f"Video Title: {title}\n\nVideo Description:\n{description}"
                
                if len(content.strip()) > 50:  # Only use if there's meaningful content
                    logger.info(f"Using video metadata for AI analysis: {len(content)} characters")
                    return content[:3000]  # Limit to 3000 chars for AI processing
                else:
                    logger.info("Video description too short for meaningful analysis")
                    return None
            
            return None
                
        except Exception as e:
            logger.error(f"Error getting video metadata: {e}")
            # Try the old yt-dlp method as ultimate fallback
            return self._download_transcript_ytdlp_fallback(video_id)
    
    def _download_transcript_ytdlp_fallback(self, video_id: str) -> Optional[str]:
        """
        Ultimate fallback method using yt-dlp (may fail on cloud IPs)
        """
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                cmd = [
                    'yt-dlp',
                    '--write-auto-sub',
                    '--sub-lang', 'en',
                    '--sub-format', 'vtt',
                    '--skip-download',
                    '--output', f'{temp_dir}/%(title)s.%(ext)s',
                    f'https://www.youtube.com/watch?v={video_id}'
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                
                if result.returncode != 0:
                    logger.error(f"yt-dlp fallback failed: {result.stderr}")
                    return None
                
                vtt_files = list(Path(temp_dir).glob('*.vtt'))
                if not vtt_files:
                    return None
                
                with open(vtt_files[0], 'r', encoding='utf-8') as f:
                    vtt_content = f.read()
                
                transcript = self._parse_vtt_content(vtt_content)
                logger.info(f"Transcript downloaded via fallback: {len(transcript)} characters")
                return transcript
                
        except Exception as e:
            logger.error(f"yt-dlp fallback error: {e}")
            return None
    
    def _parse_vtt_content(self, vtt_content: str) -> str:
        """Parse VTT file content (matches Next.js parsing logic)"""
        lines = vtt_content.split('\n')
        transcript_lines = []
        
        for line in lines:
            line = line.strip()
            
            # Skip timestamp lines and empty lines
            if '-->' in line or not line or line.startswith('WEBVTT'):
                continue
            
            # Skip lines that are just numbers (cue numbers)
            if line.isdigit():
                continue
            
            # Remove HTML tags and formatting
            line = re.sub(r'<[^>]+>', '', line)
            line = re.sub(r'&nbsp;', ' ', line)
            line = re.sub(r'&[a-zA-Z]+;', '', line)
            
            if line:
                transcript_lines.append(line)
        
        return ' '.join(transcript_lines)
    
    def generate_jim_nantz_summary(self, transcript: str, video_title: str) -> Optional[str]:
        """
        Generate Jim Nantz-style trailer summary (matches Next.js Gemini prompt exactly)
        """
        if not self.genai_model:
            logger.error("Gemini API not configured")
            return None
        
        try:
            # Exact prompt from Next.js
            prompt = f"""You are channeling the legendary golf announcer Jim Nantz. Create a compelling TRAILER-STYLE preview in Jim's distinctive broadcasting style for this golf video: "{video_title}"

Based on this transcript: {transcript[:4000]}

Guidelines:
- Channel Jim Nantz's warm, sophisticated, and reverent tone
- Build anticipation without revealing outcomes  
- Focus on what viewers WILL SEE, not what happens
- Use phrases like "Coming up", "You'll witness", "We'll see"
- MAXIMUM 60-75 words (30 seconds of speaking time)
- End with intrigue that makes people want to watch
- Avoid spoiling any results or outcomes

Create a preview that captures the excitement and draws viewers in, just like Jim would introduce a major golf moment on CBS."""

            response = self.genai_model.generate_content(prompt)
            
            if response and response.text:
                summary = response.text.strip()
                logger.info(f"Generated Gemini summary: {len(summary)} characters")
                return summary
            else:
                logger.error("Empty response from Gemini")
                return None
                
        except Exception as e:
            logger.error(f"Error generating Gemini summary: {e}")
            return None
    
    def generate_audio(self, text: str, video_id: str) -> Optional[str]:
        """
        Generate audio using ElevenLabs (matches Next.js logic)
        """
        if not self.elevenlabs_api_key:
            logger.error("ElevenLabs API not configured")
            return None
        
        try:
            # Clean the text for audio generation (matches Next.js logic)
            clean_text = text.replace('[AI-generated from video transcript]', '').replace('**', '').replace('*', '').strip()
            
            logger.info(f"Generating ElevenLabs audio for video {video_id}, text length: {len(clean_text)}")
            
            # Use Grandpa Spuds Oxley voice (same as frontend)
            voice_id = 'NOpBlnGInO9m6vDvFkFC'
            
            # ElevenLabs TTS API call
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
            headers = {
                'xi-api-key': self.elevenlabs_api_key,
                'Content-Type': 'application/json',
            }
            data = {
                'text': clean_text,
                'model_id': 'eleven_multilingual_v2',
                'voice_settings': {
                    'stability': 0.5,
                    'similarity_boost': 0.8,
                    'style': 0.2,
                    'use_speaker_boost': True
                }
            }
            
            response = requests.post(url, headers=headers, json=data)
            
            if not response.ok:
                logger.error(f"ElevenLabs API error: {response.status_code} {response.text}")
                return None
            
            # Save audio file to public directory
            audio_filename = self._save_audio_file(response.content, video_id)
            if audio_filename:
                logger.info(f"Audio saved as {audio_filename}")
                return f"/audio/{audio_filename}"
            
            return None
            
        except Exception as e:
            logger.error(f"Error generating ElevenLabs audio: {e}")
            return None
    
    def _save_audio_file(self, audio_data: bytes, video_id: str) -> Optional[str]:
        """Save audio file to public directory (matches Next.js logic)"""
        try:
            # Save to current directory (on droplet) and return relative URL
            # The frontend will need to serve these files via an API endpoint
            audio_dir = "/opt/golf-directory/audio"
            os.makedirs(audio_dir, exist_ok=True)
            
            filename = f"jim-nantz-{video_id}.mp3"
            filepath = os.path.join(audio_dir, filename)
            
            with open(filepath, 'wb') as f:
                f.write(audio_data)
            
            logger.info(f"Audio file saved to {filepath}")
            return filename
            
        except Exception as e:
            logger.error(f"Error saving audio file: {e}")
            return None
    
    def generate_transcript_summary(self, video_id: str, video_title: str) -> Dict[str, Any]:
        """
        Complete transcript summary generation (matches Next.js API endpoint logic)
        """
        result = {
            'video_id': video_id,
            'summary': None,
            'audio_url': None,
            'error': None
        }
        
        try:
            # Step 1: Download transcript
            logger.info(f"Downloading transcript for video: {video_title} ({video_id})")
            transcript = self.download_transcript(video_id)
            
            if not transcript:
                result['error'] = "Could not download transcript"
                return result
            
            # Step 2: Generate AI summary
            logger.info("Generating Jim Nantz-style summary...")
            summary = self.generate_jim_nantz_summary(transcript, video_title)
            
            if not summary:
                result['error'] = "Could not generate AI summary"
                return result
            
            result['summary'] = summary
            
            # Step 3: Generate audio
            logger.info("Generating audio narration...")
            audio_filename = self.generate_audio(summary, video_id)
            
            if audio_filename:
                result['audio_url'] = f"/audio/{audio_filename}"
            
            logger.info("Transcript summary generation completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error in transcript summary generation: {e}")
            result['error'] = str(e)
            return result