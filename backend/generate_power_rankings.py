#!/usr/bin/env python3
"""
Generate Power Rankings for social media posts
Shows top YouTube golf channels by 7-day performance
"""

import os
import sys
import psycopg2
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()
load_dotenv(Path(__file__).parent / ".env")

def get_power_rankings(limit=10):
    """Get power rankings from database using shared query"""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not found in environment")
        return None
    
    try:
        # Read the shared query
        query_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            'shared', 
            'power-rankings-query.sql'
        )
        
        with open(query_path, 'r') as f:
            query = f.read()
        
        # Modify query to use custom limit
        query = query.replace('LIMIT 20', f'LIMIT {limit}')
        
        with psycopg2.connect(database_url) as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                columns = [desc[0] for desc in cur.description]
                results = []
                for row in cur.fetchall():
                    results.append(dict(zip(columns, row)))
                return results
                
    except Exception as e:
        print(f"❌ Error getting power rankings: {e}")
        return None

def format_views(views):
    """Format view count for display"""
    if views >= 1000000:
        return f"{views/1000000:.1f}M"
    elif views >= 1000:
        return f"{views/1000:.0f}K"
    return str(views)

def generate_rankings_post(rankings, style='tweet'):
    """Generate formatted rankings for social media"""
    if style == 'tweet':
        lines = ["🏆 Golf YouTube Power Rankings (7-day)"]
        lines.append("")  # Empty line after title
        
        for i, channel in enumerate(rankings[:10], 1):
            emoji = ""
            if i == 1: emoji = "🥇"
            elif i == 2: emoji = "🥈"
            elif i == 3: emoji = "🥉"
            else: emoji = f"#{i}"
            
            views = format_views(channel['total_views'])
            
            lines.append(f"{emoji} {channel['channel_name']} - {views} views")
        
        lines.append("")  # Empty line before footer
        lines.append("📊 Full rankings: streamingrange.net")
        return "\n".join(lines)
    
    elif style == 'detailed':
        lines = ["=" * 60]
        lines.append("GOLF YOUTUBE POWER RANKINGS - 7 DAY PERFORMANCE")
        lines.append("=" * 60)
        
        for i, channel in enumerate(rankings, 1):
            views = format_views(channel['total_views'])
            change = channel['percent_change']
            change_str = f"+{change}%" if change > 0 else f"{change}%"
            
            lines.append(f"\n#{i}. {channel['channel_name']}")
            lines.append(f"    Views: {views} ({channel['video_count']} videos)")
            lines.append(f"    Change: {change_str}")
        
        return "\n".join(lines)

def main():
    """Main function"""
    print("\n" + "="*60)
    print("🏌️  POWER RANKINGS GENERATOR")
    print("="*60 + "\n")
    
    # Get power rankings
    print("📊 Fetching current power rankings...")
    rankings = get_power_rankings(limit=20)
    
    if not rankings:
        print("\n⚠️  Could not fetch power rankings")
        return
    
    # Generate tweet version
    tweet = generate_rankings_post(rankings, style='tweet')
    print("\n✅ Tweet Version (280 chars):")
    print("-" * 60)
    print(tweet)
    print("-" * 60)
    print(f"Character count: {len(tweet)}/280")
    
    # Generate detailed version
    detailed = generate_rankings_post(rankings, style='detailed')
    print("\n📋 Detailed Version:")
    print(detailed)
    
    print("\n" + "="*60)
    print("📱 Copy the version you want for social media!")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()