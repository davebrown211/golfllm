"""
Golf Channel Whitelist - Centralized list loaded from JSON file
Supports both channel IDs and handles (@username)
"""

import json
import os
from typing import List, Dict, Any

def load_whitelist() -> List[str]:
    """Load whitelist from JSON file"""
    # Get the path to the JSON file (one level up from backend)
    json_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'whitelist.json')
    
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        # Extract both IDs and handles
        channels = []
        for channel in data['channels']:
            if channel.get('id'):  # Only include non-empty IDs
                channels.append(channel['id'])
            if channel.get('handle'):
                channels.append(channel['handle'])  # Include handle if present
        
        return channels
    except Exception as e:
        print(f"Error loading whitelist from {json_path}: {e}")
        # Fallback to empty list - this will cause the system to fail safely
        return []

def get_channel_info() -> List[Dict[str, Any]]:
    """Get full channel information from JSON file"""
    json_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'whitelist.json')
    
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
        return data['channels']
    except Exception as e:
        print(f"Error loading channel info from {json_path}: {e}")
        return []

# Load the whitelist on import
WHITELISTED_CHANNELS = load_whitelist()