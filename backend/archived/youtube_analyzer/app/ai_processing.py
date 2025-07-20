import os
import time
import google.generativeai as genai
from PIL import Image

def configure_genai():
    """Configures the Gemini API key."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable not set.")
    genai.configure(api_key=api_key)

def transcribe_audio(audio_path: str) -> str:
    """
    Transcribes an audio file using the Gemini API.

    Args:
        audio_path: The path to the audio file.

    Returns:
        The transcribed text.
    """
    configure_genai()
    
    print(f"Uploading audio file: {audio_path}")
    audio_file = genai.upload_file(path=audio_path)

    # The Gemini file processing can take a moment, so we wait until it's ready.
    while audio_file.state.name == "PROCESSING":
        print("Waiting for audio processing...")
        time.sleep(10)
        audio_file = genai.get_file(name=audio_file.name)

    if audio_file.state.name == "FAILED":
        raise ValueError("Audio processing failed.")

    model = genai.GenerativeModel('gemini-1.5-flash-latest')
    try:
        response = model.generate_content(["Transcribe this audio.", audio_file])
        # It's good practice to free up the file on the server once we're done.
        genai.delete_file(name=audio_file.name)
        return response.text
    except Exception as e:
        print(f"Error transcribing audio: {e}")
        return f"Error transcribing audio: {e}"

def analyze_frame(image_path: str, prompt: str) -> str:
    """
    Analyzes a single image frame using the Gemini Vision model.

    Args:
        image_path: The path to the image file.
        prompt: The text prompt to guide the analysis.

    Returns:
        The text response from the model.
    """
    configure_genai()
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Verify image exists and is valid
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image file not found: {image_path}")
            
            img = Image.open(image_path)
            # Verify image can be loaded
            img.verify()
            # Reopen image for processing since verify() invalidates it
            img = Image.open(image_path)
            
            response = model.generate_content([prompt, img])
            
            if response.text:
                return response.text
            else:
                print(f"Empty response from AI for frame {image_path}, attempt {attempt + 1}")
                if attempt == max_retries - 1:
                    return "Error: Empty response from AI"
                time.sleep(2)  # Wait before retry
                
        except Exception as e:
            print(f"Error analyzing frame {image_path} (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                return f"Error analyzing frame after {max_retries} attempts: {e}"
            time.sleep(2)  # Wait before retry
    
    return "Error: Maximum retries exceeded"

def analyze_golf_video_direct(video_file_path: str) -> str:
    """
    Analyzes a golf video using Gemini 1.5 Pro with direct video upload.
    This is the new preferred method over frame extraction + OCR.

    Args:
        video_file_path: Path to the local video file

    Returns:
        A JSON string with the final golf analysis
    """
    configure_genai()
    
    print(f"Uploading video file: {video_file_path}...")
    video_file = genai.upload_file(path=video_file_path)
    print("Upload complete.")

    # Wait for processing
    while video_file.state.name == "PROCESSING":
        print("Waiting for video processing...")
        time.sleep(10)
        video_file = genai.get_file(name=video_file.name)

    if video_file.state.name == "FAILED":
        raise ValueError("Video processing failed.")

    prompt = """
Analyze this golf video to extract final scores and key tournament information.

INSTRUCTIONS:
1. Watch the video and analyze both visual scoreboards/graphics AND audio commentary
2. Track scoring events (birdies, eagles, pars, bogeys) throughout the video
3. Calculate final scores by combining baseline scores with scoring events
4. Prioritize audio commentary over potentially outdated graphics

OUTPUT FORMAT (JSON only):
{
  "tournament_name": "Tournament/Event name if mentioned",
  "final_leaderboard": [
    {
      "rank": 1,
      "player_name": "Player Name",
      "final_score": "+2",
      "key_moments": "Brief summary of major scoring events"
    }
  ],
  "summary": "30-second trailer-style preview that builds anticipation without spoilers (60-75 words max)"
}

Focus on accuracy. If you're unsure about a score, indicate lower confidence.
"""
    
    print("Sending multimodal request to Gemini...")
    model = genai.GenerativeModel('gemini-1.5-pro-latest')
    
    try:
        response = model.generate_content([prompt, video_file], 
                                          request_options={'timeout': 1800})
        
        # Clean up the uploaded file
        genai.delete_file(video_file.name)
        print(f"Deleted file: {video_file.name}")
        
        return response.text
    except Exception as e:
        # Clean up on error
        try:
            genai.delete_file(video_file.name)
        except:
            pass
        print(f"Error analyzing video: {e}")
        return f"Error analyzing video: {e}"

def synthesize_results(transcript: str, ocr_texts: list[str]) -> str:
    """
    Legacy method - Synthesizes the transcript and OCR text into a structured JSON object.
    NOTE: This method is deprecated in favor of analyze_golf_video_direct()

    Args:
        transcript: The full audio transcript.
        ocr_texts: A list of text extracted from on-screen graphics.

    Returns:
        A JSON string with the final, structured analysis.
    """
    configure_genai()
    
    # We can join the OCR texts, removing duplicates, to create a concise context
    unique_ocr_texts = "\n".join(sorted(list(set(ocr_texts))))

    prompt = f"""
You are a golf video analysis expert. Your task is to extract hole-by-hole scoring data from a golf video.

ANALYSIS APPROACH:
1. **RELY HEAVILY ON CAPTIONS/COMMENTARY** - This is your primary and most reliable source
2. **Use OCR data to supplement** - Graphics may show cumulative scores to help fill gaps
3. **Read the ENTIRE transcript carefully** - Scoring information may be scattered throughout

CONTENT UNDERSTANDING:
Golf videos may have various formats. Look for:
- Team names or player names mentioned repeatedly
- Match play vs stroke play format indicators
- Scoring announcements and running totals
- Money/charity elements (e.g., "$500 for birdie")
- Casual vs tournament play indicators

SCORING DETECTION STRATEGY:
1. **Look for donation amounts mentioned** - These often correlate with scoring:
   - "$500" or "five hundred" = likely a birdie was made
   - "$1000" or "thousand" = likely an eagle was made
   - Total money amounts can help track cumulative performance

2. **Search for explicit scoring terms throughout the ENTIRE transcript**:
   - "birdie", "eagle", "par", "bogey", "hole in one"
   - "makes", "made", "sinks", "drains" (followed by scoring terms)
   - "putting for [score]", "birdie putt", "eagle putt"

3. **Look for hole-specific information**:
   - "par 3", "par 4", "par 5" 
   - Yardage mentions like "388 to the pin"
   - Hole transitions: "next hole", "moving to"

4. **Track team performance mentions**:
   - References to which team is doing better
   - Cumulative money totals
   - Final scores or results

IMPORTANT: 
- Golf videos vary in length - scoring info may be spread throughout
- Don't assume holes are discussed in order - look for all scoring events
- If specific hole scores aren't mentioned, try to infer from cumulative totals
- Players/teams may not complete all holes - mark as "N/A" if not mentioned
- BE CONSERVATIVE with extreme scores: Multiple eagles or hole-in-ones are very rare
- If you assign an eagle (-2), make sure there's clear evidence in the commentary
- Final totals mentioned in commentary should match your calculated totals

ANALYSIS PROCESS:
1. Read through the ENTIRE transcript looking for ANY scoring references
2. Cross-reference with OCR data to confirm cumulative scores  
3. Try to piece together a complete scorecard for all players/teams
4. If you can't determine specific hole scores, use the cumulative information available

--- COMMENTARY/CAPTIONS (FULL TRANSCRIPT) ---
{transcript}

--- OCR TEXT FROM SCOREBOARDS ---
{unique_ocr_texts}

---

Analyze the complete transcript carefully and provide a JSON object with hole-by-hole scores for all players/teams.

REQUIRED JSON FORMAT (this exact structure):
```json
{{
  "holes": [
    {{
      "hole_number": 1,
      "par": 4,
      "player_scores": [
        {{
          "player_name": "Player/Team Name",
          "score": -1,
          "total_score_after_hole": -1
        }},
        {{
          "player_name": "Another Player/Team", 
          "score": 0,
          "total_score_after_hole": -1
        }}
      ]
    }}
  ]
}}
```

IMPORTANT: 
- Use ONLY this exact JSON structure
- "score" must be integer relative to par (-1 for birdie, 0 for par, +1 for bogey, etc.)
- Include all holes played with complete data for all teams/players
- VALIDATE: Listen for final score mentions in the commentary (e.g., "shot 8 under")
- Ensure your hole-by-hole scores sum to match any final totals mentioned
- If unsure between two possible scores, choose the more conservative option
- Do not include explanation text, only the JSON object
"""

    # Use Pro model for better analysis of long transcripts
    model = genai.GenerativeModel('gemini-1.5-pro-latest')
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error synthesizing results: {e}")
        return f"Error synthesizing results: {e}"

def extract_character_traits(transcript: str, ocr_texts: list[str]) -> str:
    """
    Analyzes the transcript and visual content to extract detailed character personality traits.
    
    Args:
        transcript: The full video transcript/captions.
        ocr_texts: OCR text from video frames (may contain player names, graphics).
    
    Returns:
        A JSON string with detailed character analysis for parody creation.
    """
    configure_genai()
    
    unique_ocr_texts = "\n".join(sorted(list(set(ocr_texts))))
    
    prompt = f"""
You are a character analysis expert specializing in extracting personality traits from golf video content for creative parody purposes.

OBJECTIVE: Analyze this golf video content to extract detailed personality profiles of each player/character that could be used to create exaggerated parody versions.

ANALYSIS FOCUS AREAS:

1. **SPEAKING PATTERNS & PERSONALITY**:
   - Catchphrases, repeated expressions, unique vocabulary
   - Confidence level (humble vs cocky vs insecure)
   - Humor style (dry, slapstick, self-deprecating, trash talk)
   - Competitiveness (laid-back vs intense vs overly dramatic)
   - Reaction patterns to good/bad shots

2. **GOLF-SPECIFIC BEHAVIORS**:
   - Playing style (aggressive risk-taker vs conservative strategist)
   - Celebration style (subdued vs animated vs excessive showboating)
   - How they handle pressure or failure
   - Superstitions or rituals mentioned
   - Attitude toward rules, money, competition

3. **INTERPERSONAL DYNAMICS**:
   - How they interact with teammates/partners
   - Leadership vs follower tendencies  
   - Trash talk frequency and style
   - Support vs rivalry with others

4. **PHYSICAL/VISUAL CHARACTERISTICS** (from commentary AND visual analysis):
   - Clothing style, colors, brands mentioned or visible
   - Physical build, height references, distinctive features
   - Hair style/color, facial hair, accessories
   - Body language and mannerisms described or observed
   - Distinctive equipment (golf clubs, shoes, gear)

5. **BACKGROUND/CONTEXT CLUES**:
   - Skill level indicators (pro, amateur, beginner references)
   - Channel/brand associations mentioned
   - Previous video references that reveal character history

EXTRACTION STRATEGY:
- Look for direct quotes that reveal personality
- Note recurring behavioral patterns mentioned
- Identify any running jokes or personality-based comedy
- Pay attention to how commentators describe each person
- Extract specific moments that define their character

--- FULL TRANSCRIPT/CAPTIONS ---
{transcript}

--- OCR/VISUAL TEXT ---  
{unique_ocr_texts}

---

Provide a detailed JSON analysis focusing on personality traits suitable for creating exaggerated parody characters:

```json
{{
  "characters": [
    {{
      "name": "Character Name",
      "channel_or_brand": "Channel/Brand if mentioned",
      
      "personality_traits": {{
        "confidence_level": 7.5,
        "humor_level": 8.0, 
        "competitiveness": 6.0,
        "trash_talk_frequency": 4.0
      }},
      
      "speaking_patterns": {{
        "catchphrases": ["specific phrase 1", "specific phrase 2"],
        "speaking_style": "casual/technical/dramatic",
        "notable_quotes": ["memorable quote 1", "memorable quote 2"],
        "profanity_usage": 3.0,
        "accent_description": "regional/international accent if notable"
      }},
      
      "golf_characteristics": {{
        "skill_level": "amateur/semi-pro/pro",
        "playing_style": "aggressive/conservative/unpredictable", 
        "reaction_to_bad_shots": "calm/frustrated/explosive",
        "reaction_to_good_shots": "humble/confident/showboat",
        "celebration_style": "subdued/animated/excessive"
      }},
      
      "visual_traits": {{
        "clothing_style": "detailed clothing description (colors, brands, style)",
        "physical_build": "height/build references or observations",
        "hair_facial_features": "hair color/style, facial hair, distinctive features",
        "accessories": "hats, glasses, jewelry, watches mentioned or visible",
        "equipment_style": "golf equipment brands, colors, distinctive gear",
        "body_language": "posture, gestures, mannerisms described",
        "overall_appearance": "general style impression for character design"
      }},
      
      "parody_potential": {{
        "most_exaggeratable_trait": "trait that could be amplified for comedy",
        "signature_moments": ["moment 1 that defines them", "moment 2"],
        "comedy_angle": "how this character could be made funnier"
      }}
    }}
  ]
}}
```

IMPORTANT:
- Only include characters with substantial screen time/dialogue
- Rate traits on 1-10 scale based on evidence from content
- Extract actual quotes when possible, not paraphrases  
- Focus on traits that would translate well to parody/comedy
- If multiple videos feature same people, note evolving characteristics
- Be specific about moments that reveal character traits
"""

    # Use Pro model for detailed character analysis
    model = genai.GenerativeModel('gemini-1.5-pro-latest')
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error extracting character traits: {e}")
        return f"Error extracting character traits: {e}" 