#!/usr/bin/env python3
"""
Generate X (Twitter) post for current Video of the Day
Run this script to get a ready-to-copy post for the current VOD
"""

import os
import sys
import psycopg2
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()
load_dotenv(Path(__file__).parent / ".env")

def get_current_vod():
    """Get current Video of the Day from database"""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not found in environment")
        return None
    
    try:
        # Load the shared VOD query
        shared_query_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            'shared', 
            'video-of-the-day-query.sql'
        )
        
        with open(shared_query_path, 'r') as f:
            query = f.read().strip()
        
        with psycopg2.connect(database_url) as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                result = cur.fetchone()
                
                if not result:
                    print("❌ No Video of the Day found for today")
                    return None
                
                # Map query results to dict (ai_analysis is at index 11 based on shared query)
                return {
                    'video_id': result[0],
                    'title': result[1],
                    'channel_name': result[2],
                    'view_count': result[3],
                    'published_at': result[6],  # published_at is at index 6
                    'duration_seconds': result[9],  # duration_seconds is at index 9
                    'ai_summary': result[11] if len(result) > 11 and result[11] else None  # ai_analysis
                }
                
    except Exception as e:
        print(f"❌ Error getting VOD: {e}")
        return None

def get_creator_x_handle(channel_name):
    """Get X handle for creator from database"""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        return None
    
    try:
        with psycopg2.connect(database_url) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT x_handle 
                    FROM whitelisted_channels 
                    WHERE LOWER(name) = LOWER(%s) 
                    AND x_handle IS NOT NULL
                    AND active = true
                """, (channel_name,))
                
                result = cur.fetchone()
                return result[0] if result else None
                
    except Exception as e:
        print(f"⚠️  Could not get X handle: {e}")
        return None

def generate_contextual_question(title, ai_summary):
    """Generate a contextual question based on video content using AI"""
    try:
        import google.generativeai as genai
        
        # Configure Gemini API
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            return None
            
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""Based on this golf video title and summary, generate ONE engaging question (under 50 characters) that would get golf fans to comment and engage on Twitter/X.

Title: {title}
Summary: {ai_summary}

The question should:
- Be specific to the video content
- Encourage personal responses/experiences 
- Create discussion/debate
- Be conversational and casual
- End with a question mark

Examples of good questions:
- "What's your handicap vs these guys?"
- "Could you handle Bryson's power?"
- "Best course management tip here?"
- "Your go-to recovery shot?"

Generate just the question, nothing else:"""

        response = model.generate_content(prompt)
        question = response.text.strip()
        
        # Validate the response
        if question and len(question) < 60 and question.endswith('?'):
            return question
        else:
            return None
            
    except Exception as e:
        print(f"⚠️ Could not generate contextual question: {e}")
        return None

def format_duration(seconds):
    """Format duration in human readable format"""
    if not seconds or seconds == 0:
        return ""
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    
    if hours > 0:
        return f"{hours}h {minutes}m"
    elif minutes > 0:
        return f"{minutes}m"
    else:
        seconds = int(seconds)
        return f"{seconds}s"

def generate_vod_post(vod_data):
    """Generate X post for Video of the Day"""
    import random
    
    # Get creator X handle if available
    x_handle = get_creator_x_handle(vod_data['channel_name'])
    creator_tag = f" by {x_handle}" if x_handle else f" by {vod_data['channel_name']}"
    
    # Truncate title if too long
    title = vod_data['title']
    if len(title) > 90:
        title = title[:87] + "..."
    
    # Engaging hooks (random selection)
    hooks = [
        "This is why I love golf content 👇",
        "Found something good today 🎯", 
        "Golf Twitter, thoughts on this? 👀",
        "This caught my attention 🔥",
        "Weekend golf vibes incoming 🏌️‍♂️",
        "Your next golf rabbit hole 👇",
        "Golf content that actually delivers 💯"
    ]
    
    # Generate contextual question using AI if we have summary
    contextual_question = None
    if vod_data.get('ai_summary'):
        contextual_question = generate_contextual_question(vod_data['title'], vod_data['ai_summary'])
    
    # Fallback engaging questions if AI generation fails
    fallback_questions = [
        "What's your biggest takeaway from this?",
        "Thoughts on this approach?", 
        "Who else needs to see this?",
        "What would you do differently?",
        "Does this change how you think about golf?"
    ]
    
    # Random selections
    hook = random.choice(hooks)
    question = contextual_question if contextual_question else random.choice(fallback_questions)
    
    # Get AI summary snippet for context
    context = ""
    if vod_data.get('ai_summary') and isinstance(vod_data['ai_summary'], str):
        summary = vod_data['ai_summary']
        # Extract most interesting part (look for specific examples)
        sentences = summary.split('.')
        for sentence in sentences:
            if any(word in sentence.lower() for word in ['hole', 'shot', 'yards', 'putt', 'fairway', 'green']):
                if len(sentence.strip()) > 20:
                    context = sentence.strip()[:80] + "..." if len(sentence.strip()) > 80 else sentence.strip()
                    break
        if not context and len(summary) > 50:
            context = summary[:80] + "..."
    
    # Build the post with personality
    if context:
        post = f"""{hook}

{title}{creator_tag}

{context}

{question}

🎧 AI breakdown: streamingrange.net
📺 youtu.be/{vod_data['video_id']}

#Golf #GolfTips #GolfContent"""
    else:
        post = f"""{hook}

{title}{creator_tag}

{question}

🎧 AI breakdown: streamingrange.net  
📺 youtu.be/{vod_data['video_id']}

#Golf #GolfTips #GolfContent"""
    
    return post

def main():
    """Main function"""
    print("\n" + "="*60)
    print("🏌️  STREAMING RANGE - VOD X POST GENERATOR")
    print("="*60 + "\n")
    
    # Get current VOD
    print("📊 Fetching current Video of the Day...")
    vod = get_current_vod()
    
    if not vod:
        print("\n⚠️  No Video of the Day available to post about")
        print("   Make sure the scheduler has run today to select a VOD")
        return
    
    # Generate the post
    post = generate_vod_post(vod)
    
    # Display the post
    print("\n✅ Generated X Post:")
    print("-" * 60)
    print(post)
    print("-" * 60)
    
    # Character count
    char_count = len(post)
    print(f"\n📏 Character count: {char_count}/280")
    
    if char_count > 280:
        print("⚠️  Post is too long! Need to trim it down.")
    else:
        print("✅ Ready to copy and paste to X!")
    
    print("\n🔗 Video Info:")
    print(f"   Title: {vod['title']}")
    print(f"   Channel: {vod['channel_name']}")
    print(f"   Views: {vod['view_count']:,}")
    if isinstance(vod['published_at'], datetime):
        print(f"   Published: {vod['published_at'].strftime('%Y-%m-%d')}")
    print(f"   YouTube: https://youtu.be/{vod['video_id']}")
    
    print("\n" + "="*60)
    print("📱 Copy the post above and paste it to @streamingrange")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()