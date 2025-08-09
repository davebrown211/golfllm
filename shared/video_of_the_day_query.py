"""
Video of the Day Query
Shared between frontend and backend to ensure consistent selection logic
"""

import os

def get_video_of_the_day_query():
    """Read the shared video of the day SQL query"""
    query_path = os.path.join(os.path.dirname(__file__), 'video-of-the-day-query.sql')
    with open(query_path, 'r') as f:
        return f.read()