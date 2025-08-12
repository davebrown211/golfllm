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
                
                # Map query results to dict
                return {
                    'video_id': result[0],
                    'title': result[1],
                    'channel_name': result[2],
                    'view_count': result[3],
                    'published_at': result[4],
                    'duration_seconds': result[5],
                    'ai_summary': result[6] if len(result) > 6 else None
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
    
    # Get creator X handle if available
    x_handle = get_creator_x_handle(vod_data['channel_name'])
    creator_tag = f" by {x_handle}" if x_handle else f" by {vod_data['channel_name']}"
    
    # Truncate title if too long
    title = vod_data['title']
    if len(title) > 100:
        title = title[:97] + "..."
    
    # Get AI summary snippet if available
    summary_snippet = ""
    if vod_data.get('ai_summary') and isinstance(vod_data['ai_summary'], str):
        # Extract first sentence or 100 chars
        summary = vod_data['ai_summary']
        if len(summary) > 150:
            summary = summary[:147] + "..."
        summary_snippet = f"\n{summary}\n"
    
    # Build the post
    post = f"""🏌️ VIDEO OF THE DAY 🏌️

{title}{creator_tag}
{summary_snippet}
🎧 AI audio summary: streamingrange.net
📺 Watch: https://youtu.be/{vod_data['video_id']}

#GolfContent #VideoOfTheDay #Golf"""
    
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