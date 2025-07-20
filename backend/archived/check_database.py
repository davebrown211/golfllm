#!/usr/bin/env python3
"""
Check what data is stored in the golf directory database.
"""

import sqlite3
import os
from datetime import datetime

def check_database():
    db_path = "golf_directory_demo.db"  # Check demo database with sample data
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        print("Run data collection first: python -m youtube_analyzer.app.data_collector")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("=== GOLF DIRECTORY DATABASE CONTENTS ===\n")
    
    # Check tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables in database:")
    for table in tables:
        print(f"  • {table[0]}")
    
    # Check video count
    cursor.execute("SELECT COUNT(*) FROM youtube_videos")
    video_count = cursor.fetchone()[0]
    print(f"\nTotal videos stored: {video_count}")
    
    # Check channel count
    cursor.execute("SELECT COUNT(*) FROM youtube_channels")
    channel_count = cursor.fetchone()[0]
    print(f"Total channels stored: {channel_count}")
    
    # Sample video data
    print("\n=== SAMPLE VIDEO DATA ===")
    cursor.execute("""
        SELECT v.title, v.view_count, v.like_count, v.engagement_rate, 
               c.title as channel, v.published_at, v.category
        FROM youtube_videos v
        JOIN youtube_channels c ON v.channel_id = c.id
        ORDER BY v.view_count DESC
        LIMIT 5
    """)
    
    for row in cursor.fetchall():
        print(f"\nTitle: {row[0]}")
        print(f"Channel: {row[4]}")
        print(f"Views: {row[1]:,}")
        print(f"Likes: {row[2]:,}")
        print(f"Engagement: {row[3]:.2f}%")
        print(f"Category: {row[6]}")
        print(f"Published: {row[5]}")
    
    # Check latest updates
    cursor.execute("""
        SELECT MAX(updated_at) FROM youtube_videos
    """)
    last_update = cursor.fetchone()[0]
    print(f"\n\nLast database update: {last_update}")
    
    # Category breakdown
    print("\n=== CONTENT CATEGORIES ===")
    cursor.execute("""
        SELECT category, COUNT(*) as count
        FROM youtube_videos
        GROUP BY category
        ORDER BY count DESC
    """)
    
    for row in cursor.fetchall():
        print(f"{row[0]}: {row[1]} videos")
    
    # Storage info
    file_size = os.path.getsize(db_path) / 1024 / 1024  # MB
    print(f"\n\nDatabase size: {file_size:.2f} MB")
    
    conn.close()
    
    print("\n=== WHAT'S STORED ===")
    print("For each video:")
    print("  • Video ID, title, description")
    print("  • View count, likes, comments")
    print("  • Channel info (ID, name, subscribers)")
    print("  • Timestamps (published, discovered, updated)")
    print("  • Calculated metrics (engagement rate, view velocity)")
    print("  • Category classification")
    print("  • Thumbnail URLs")
    print("\nFor rankings:")
    print("  • Daily/weekly/all-time rankings")
    print("  • Ranking scores and positions")
    print("  • Timestamp of ranking calculation")


if __name__ == "__main__":
    check_database()