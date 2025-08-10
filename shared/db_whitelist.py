"""
Database whitelist helper - replaces JSON file-based whitelist
"""
import os
import psycopg2
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

def get_whitelisted_channel_ids() -> List[str]:
    """Get all active whitelisted channel IDs from database"""
    conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    try:
        cur = conn.cursor()
        cur.execute("SELECT channel_id FROM whitelisted_channels WHERE active = true ORDER BY channel_id")
        return [row[0] for row in cur.fetchall()]
    finally:
        conn.close()

def get_whitelisted_channels() -> List[Dict[str, str]]:
    """Get all active whitelisted channels with metadata from database"""
    conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    try:
        cur = conn.cursor()
        cur.execute("SELECT channel_id, name FROM whitelisted_channels WHERE active = true ORDER BY name")
        return [{"id": row[0], "name": row[1]} for row in cur.fetchall()]
    finally:
        conn.close()

def is_channel_whitelisted(channel_id: str) -> bool:
    """Check if a channel ID is whitelisted"""
    conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    try:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM whitelisted_channels WHERE channel_id = %s AND active = true", (channel_id,))
        return cur.fetchone() is not None
    finally:
        conn.close()

# Backward compatibility
WHITELISTED_CHANNELS = get_whitelisted_channel_ids()