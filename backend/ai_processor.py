"""
AI Processing Module - Python Implementation
Matches the refined Next.js AI generation logic exactly
"""

import os
import logging
import tempfile
import subprocess
import re
import random
from typing import Optional, Dict, Any
from pathlib import Path
try:
    from elevenlabs import ElevenLabs
    client = ElevenLabs()
except ImportError:
    # Fallback for older version
    from elevenlabs import generate, save
import requests
import boto3
from botocore.exceptions import ClientError
import anthropic

logger = logging.getLogger(__name__)

class AIProcessor:
    """AI processing for video analysis and audio generation"""
    
    def __init__(self, 
                 anthropic_api_key: Optional[str] = None,
                 elevenlabs_api_key: Optional[str] = None):
        
        # Configure Anthropic Claude
        if anthropic_api_key:
            self.anthropic_client = anthropic.Anthropic(api_key=anthropic_api_key)
        else:
            self.anthropic_client = None
            logger.warning("Anthropic API key not provided - AI analysis disabled")
        
        # Configure ElevenLabs
        self.elevenlabs_api_key = elevenlabs_api_key
        if not elevenlabs_api_key:
            logger.warning("ElevenLabs API key not provided - audio generation disabled")
        
        # Configure DigitalOcean Spaces
        self.spaces_client = None
        self.spaces_bucket = os.getenv('SPACES_BUCKET_NAME', 'golf-directory-audio')
        self.spaces_region = os.getenv('SPACES_REGION', 'nyc3')
        self.spaces_endpoint = f'https://{self.spaces_region}.digitaloceanspaces.com'
        self.cdn_endpoint = os.getenv('SPACES_CDN_ENDPOINT', f'https://{self.spaces_bucket}.{self.spaces_region}.cdn.digitaloceanspaces.com')
        
        spaces_key = os.getenv('SPACES_ACCESS_KEY')
        spaces_secret = os.getenv('SPACES_SECRET_KEY')
        
        if spaces_key and spaces_secret:
            try:
                self.spaces_client = boto3.client(
                    's3',
                    region_name=self.spaces_region,
                    endpoint_url=self.spaces_endpoint,
                    aws_access_key_id=spaces_key,
                    aws_secret_access_key=spaces_secret
                )
                logger.info(f"DigitalOcean Spaces configured: {self.spaces_bucket}")
            except Exception as e:
                logger.error(f"Failed to configure DigitalOcean Spaces: {e}")
                self.spaces_client = None
        else:
            logger.warning("Spaces credentials not provided - falling back to local storage")
    
    def download_transcript(self, video_id: str) -> Optional[str]:
        """
        Download video transcript - try real transcript first, fallback to description
        """
        # First try to get actual transcript using youtube-transcript-api
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            
            # Check if we need to use a proxy (for cloud servers)
            api = None
            proxy_url = os.environ.get('YOUTUBE_PROXY_URL')  # Format: http://user:pass@proxy:port
            
            if proxy_url:
                try:
                    from youtube_transcript_api.proxies import GenericProxyConfig
                    logger.info(f"Using proxy for transcript fetching: {proxy_url.split('@')[-1] if '@' in proxy_url else proxy_url}")
                    proxy_config = GenericProxyConfig(
                        http_url=proxy_url,
                        https_url=proxy_url
                    )
                    api = YouTubeTranscriptApi(proxy_config=proxy_config)
                except Exception as proxy_error:
                    logger.warning(f"Failed to configure proxy: {proxy_error}, falling back to direct connection")
                    api = YouTubeTranscriptApi()
            else:
                # No proxy configured, use direct connection
                api = YouTubeTranscriptApi()
            
            logger.info(f"Attempting to fetch transcript for video {video_id}")
            transcript_list = api.list(video_id)
            
            # Find and fetch English transcript
            for transcript in transcript_list:
                if transcript.language_code == 'en':
                    fetched = transcript.fetch()
                    
                    # Combine all transcript segments into one text
                    transcript_text = ' '.join([segment.text for segment in fetched])
                    
                    if transcript_text and len(transcript_text) > 100:
                        logger.info(f"Successfully fetched FULL transcript: {len(transcript_text)} characters")
                        return transcript_text  # Return full transcript for chunk processing
                    break
                
        except Exception as e:
            logger.warning(f"Could not fetch transcript via youtube-transcript-api: {e}")
        
        # Fallback to video description if transcript not available
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
    
    def generate_announcer_summary(self, transcript: str, video_title: str) -> Optional[str]:
        """
        Generate golf announcer-style trailer summary (matches Next.js Gemini prompt exactly)
        """
        if not self.anthropic_client:
            logger.error("Anthropic API not configured")
            return None
        
        try:
            # If transcript is very long, use chunk-and-combine approach
            if len(transcript) > 15000:
                logger.info(f"Transcript is {len(transcript)} chars - using chunk summarization approach")
                
                # Step 1: Split transcript into chunks
                chunk_size = 10000  # ~2000 words per chunk
                chunks = []
                for i in range(0, len(transcript), chunk_size):
                    chunks.append(transcript[i:i + chunk_size])
                
                logger.info(f"Split into {len(chunks)} chunks for summarization")
                
                # Step 2: Summarize each chunk
                chunk_summaries = []
                for i, chunk in enumerate(chunks):
                    chunk_prompt = f"""Summarize this part {i+1} of {len(chunks)} of a golf video transcript. 
                    Focus on: key moments, scores, player actions, dramatic turns, and outcomes.
                    Keep it concise (100-150 words).
                    
                    Transcript chunk: {chunk}"""
                    
                    response = self.anthropic_client.messages.create(
                        model="claude-3-haiku-20240307",
                        max_tokens=300,
                        messages=[{"role": "user", "content": chunk_prompt}]
                    )
                    
                    if response and response.content:
                        chunk_summary = response.content[0].text.strip()
                        chunk_summaries.append(f"Part {i+1}: {chunk_summary}")
                        logger.info(f"Summarized chunk {i+1}/{len(chunks)}")
                
                # Step 3: Generate final summary from all chunk summaries
                combined_summaries = "\n\n".join(chunk_summaries)
                logger.info(f"Combined summaries total: {len(combined_summaries)} chars")
                
                # Use the combined summaries as the transcript for the final prompt
                transcript = f"Video Overview (summarized from full transcript):\n{combined_summaries}"
            
            # Final announcer-style summary prompt
            prompt = f"""You are "The Professor" - a golf commentator who blends Jim Nantz's elegance, Colt Knost's tour insight, and Kevin Kisner's everyman appeal. Create a compelling TRAILER-STYLE preview for this golf video: "{video_title}"

Based on this transcript: {transcript[:10000]}

Your Mission:
- Create a 45-second audio preview (110-130 words of natural speech)
- Include 2-3 SPECIFIC examples from the video without spoiling outcomes
- Mention actual shots, holes, scores, courses, or moments from the transcript
- Reference real situations and techniques viewers will learn about

Your Personality:
- Sophisticated yet approachable (Jim's warmth + Kisner's relatability)
- Tour-level golf knowledge (Colt's insider perspective)
- Subtle humor without being goofy (Kisner's wit + Jim's class)
- The voice of someone who's "been there" but speaks to all golfers

Structure Guidelines:
- Start with an intriguing hook about a specific moment from THIS video
- Provide context about the course, conditions, or situation shown
- Reference 2-3 actual moments/shots/techniques from the transcript
- Build anticipation without revealing outcomes
- End with what viewers will learn or experience

Think: Jim Nantz introducing a moment, but with the insight of a former tour player and the humor of your weekend foursome's best storyteller.

CRITICAL FORMATTING RULES:
- Write ONLY the spoken words, nothing else
- Do NOT start with "*clears throat*" or any stage directions
- Do NOT include tone descriptions like "*speaks in a smooth voice*"
- Do NOT use asterisks (*) anywhere in your response
- Do NOT include "[voice direction]" or "(tone instruction)" 
- Start immediately with the actual commentary words
- This text will be sent directly to text-to-speech, so only include speakable words

Write directly in the commentator's voice. Aim for 45 seconds of natural, conversational speech with concrete details from the video."""

            response = self.anthropic_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            if response and response.content and len(response.content) > 0:
                summary = response.content[0].text.strip()
                logger.info(f"Generated Claude summary: {len(summary)} characters")
                return summary
            else:
                logger.error("Empty response from Claude")
                return None
                
        except Exception as e:
            logger.error(f"Error generating Claude summary: {e}")
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
            clean_text = text.replace('[AI-generated from video transcript]', '').strip()
            
            # Remove stage directions and tone instructions
            # Remove content between asterisks (like *clears throat*)
            clean_text = re.sub(r'\*[^*]+\*', '', clean_text).strip()
            
            # Remove bracketed instructions [like this]
            clean_text = re.sub(r'\[.*?\]', '', clean_text).strip()
            
            # Remove parenthetical stage directions at the start
            if clean_text.startswith('(') and ')' in clean_text[:100]:
                clean_text = re.sub(r'^\([^)]+\)\s*', '', clean_text).strip()
            
            # Remove any remaining asterisks
            clean_text = clean_text.replace('*', '').strip()
            
            # Remove any leading/trailing punctuation after instruction removal
            clean_text = re.sub(r'^[,.\s]+|[,.\s]+$', '', clean_text).strip()
            
            # If the text still starts with lowercase, it might be a continuation from removed stage direction
            # Capitalize the first letter
            if clean_text and clean_text[0].islower():
                clean_text = clean_text[0].upper() + clean_text[1:]
            
            logger.info(f"Generating ElevenLabs audio for video {video_id}, text length: {len(clean_text)}")
            
            # Multiple voice options for variety - randomly select one
            voices = {
                'Eric': 'cjVigY5qzO86Huf0OWal',              # Original smooth tenor
                'Brian': 'nPczCjzI2devNBz1zQrb',             # Deep, confident
                'Matthew': 'Yko7PKHZNXotIFUBG7I9',           # Professional, clear
                'Bill': 'pqHfZKP75CvOlQylNhV4',             # Experienced, friendly
                'Grandpa Spuds Oxley': 'NOpBlnGInO9m6vDvFkFC' # Wise grandfather voice
            }
            
            # Randomly select a voice for variety
            voice_name = random.choice(list(voices.keys()))
            voice_id = voices[voice_name]
            logger.info(f"Selected voice: {voice_name} ({voice_id})")
            
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
            
            # Save audio file to DigitalOcean Spaces or local directory
            audio_url = self._save_audio_file(response.content, video_id)
            if audio_url:
                logger.info(f"Audio saved: {audio_url}")
                # _save_audio_file returns either a full CDN URL (Spaces) or filename (local)
                if audio_url.startswith('http'):
                    return audio_url  # Full CDN URL from Spaces
                else:
                    return f"/audio/{audio_url}"  # Local filename - add prefix
            
            return None
            
        except Exception as e:
            logger.error(f"Error generating ElevenLabs audio: {e}")
            return None
    
    def _save_audio_file(self, audio_data: bytes, video_id: str) -> Optional[str]:
        """Save audio file to DigitalOcean Spaces or fallback to local storage"""
        filename = f"audio-{video_id}.mp3"
        
        # Try to upload to DigitalOcean Spaces first
        if self.spaces_client:
            try:
                # Upload to Spaces
                self.spaces_client.put_object(
                    Bucket=self.spaces_bucket,
                    Key=filename,
                    Body=audio_data,
                    ContentType='audio/mpeg',
                    ACL='public-read'  # Make publicly accessible
                )
                
                # Return the CDN URL
                cdn_url = f"{self.cdn_endpoint}/{filename}"
                logger.info(f"Audio file uploaded to Spaces: {cdn_url}")
                return cdn_url
                
            except ClientError as e:
                logger.error(f"Failed to upload to Spaces: {e}")
                # Fall through to local storage
            except Exception as e:
                logger.error(f"Error uploading to Spaces: {e}")
                # Fall through to local storage
        
        # Fallback to local storage (for development or if Spaces fails)
        try:
            # Use local path for development, production path for server
            if os.path.exists("/opt/golf-directory"):
                audio_dir = "/root/golfllm/frontend/golf-directory/public/audio"
            else:
                # Local development path
                audio_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "golf-directory", "public", "audio")
            
            os.makedirs(audio_dir, exist_ok=True)
            filepath = os.path.join(audio_dir, filename)
            
            with open(filepath, 'wb') as f:
                f.write(audio_data)
            
            logger.info(f"Audio file saved locally to {filepath}")
            return filename  # Return relative path for local storage
            
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
            logger.info("Generating announcer-style summary...")
            summary = self.generate_announcer_summary(transcript, video_title)
            
            if not summary:
                result['error'] = "Could not generate AI summary"
                return result
            
            result['summary'] = summary
            
            # Step 3: Generate audio
            logger.info("Generating audio narration...")
            audio_filename = self.generate_audio(summary, video_id)
            
            if audio_filename:
                result['audio_url'] = audio_filename  # Full URL (Spaces) or /audio/filename (local)
            
            logger.info("Transcript summary generation completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error in transcript summary generation: {e}")
            result['error'] = str(e)
            return result