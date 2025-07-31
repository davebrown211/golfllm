"""
X (Twitter) Post Templates for Golf Video Content
"""

from typing import Dict, List, Optional
from datetime import datetime
import json
import os

class XPostTemplates:
    
    WEBSITE_URL = "https://golf-directory-frontend.vercel.app"
    
    @staticmethod
    def video_of_the_day(video_data: Dict, creator_x_handle: Optional[str] = None) -> str:
        """Generate post for daily video feature"""
        creator_tag = f" by {creator_x_handle}" if creator_x_handle else ""
        
        template = f"""🏌️ VIDEO OF THE DAY 🏌️

{video_data['title']}
{creator_tag}

{video_data.get('ai_summary', '')[:100]}...

Watch: https://youtu.be/{video_data['video_id']}
More: {XPostTemplates.WEBSITE_URL}

#GolfContent #VideoOfTheDay #Golf"""
        
        return template
    
    @staticmethod
    def creator_of_the_week(creator_data: Dict, videos_count: int, total_views: int) -> str:
        """Generate post for weekly creator spotlight"""
        x_handle = creator_data.get('x_handle', '')
        creator_mention = f"{x_handle} " if x_handle else ""
        
        template = f"""⭐ CREATOR OF THE WEEK ⭐

{creator_mention}has been crushing it with {videos_count} amazing videos this week!

🔥 {total_views:,} total views
🎬 Consistently great content
👏 Well deserved recognition

Discover more: {XPostTemplates.WEBSITE_URL}

#CreatorOfTheWeek #GolfContent #Golf"""
        
        return template
    
    @staticmethod
    def trending_video(video_data: Dict, momentum_score: float, creator_x_handle: Optional[str] = None) -> str:
        """Generate post for trending/viral videos"""
        creator_tag = f" by {creator_x_handle}" if creator_x_handle else ""
        
        template = f"""🚀 TRENDING NOW 🚀

This video is going VIRAL!{creator_tag}

"{video_data['title']}"

📈 {momentum_score:.1f}x momentum score
🔥 Don't miss this one!

Watch: https://youtu.be/{video_data['video_id']}
Discover more: {XPostTemplates.WEBSITE_URL}

#Trending #GolfViral #Golf"""
        
        return template
    
    @staticmethod
    def weekly_roundup(top_videos: List[Dict]) -> str:
        """Generate post for weekly content roundup"""
        video_list = ""
        for i, video in enumerate(top_videos[:3], 1):
            video_list += f"{i}. {video['title'][:50]}...\n"
        
        template = f"""📱 WEEKLY GOLF ROUNDUP 📱

This week's top videos:

{video_list}
Full collection: {XPostTemplates.WEBSITE_URL}

#WeeklyRoundup #GolfContent #Golf"""
        
        return template
    
    @staticmethod
    def engagement_post() -> str:
        """Generate engagement/community building posts"""
        templates = [
            f"""⛳ What's your go-to golf content on YouTube?

Drop your favorite golf creators below! 👇

We're always looking for new voices to feature.

Check out our curated collection: {XPostTemplates.WEBSITE_URL}

#GolfCommunity #Golf""",
            
            f"""🏌️‍♂️ Quick question for the golf fam:

What type of golf content do you love most?
• Course vlogs
• Instruction tips  
• Equipment reviews
• Tournament highlights

Let us know! 👇

Discover more: {XPostTemplates.WEBSITE_URL}

#GolfContent #Golf""",
            
            f"""📺 The golf content game is STRONG right now!

So many amazing creators making incredible videos. The variety and quality keeps getting better.

Who's your current favorite? 🏌️

Browse our favorites: {XPostTemplates.WEBSITE_URL}

#GolfContent #Golf"""
        ]
        
        import random
        return random.choice(templates)
    
    @staticmethod
    def brand_mention(occasion: str = "general") -> str:
        """Generate posts that mention the brand/clothing line goal"""
        if occasion == "general":
            return f"""🏌️ Building something special for the golf community...

Great content deserves great gear. 

Curating the best: {XPostTemplates.WEBSITE_URL}
Stay tuned for more. ⛳

#Golf #GolfFashion"""
        
        elif occasion == "teaser":
            return f"""👕 Something's brewing in the pro shop...

The best golf content + the cleanest golf apparel = 🔥

Discover great content: {XPostTemplates.WEBSITE_URL}
Coming soon. ⛳

#GolfFashion #Golf"""
        
        elif occasion == "launch":
            return f"""🚀 IT'S HERE!

Premium golf apparel designed by golfers, for golfers.

Born from our love of great golf content.
Discover our curated videos: {XPostTemplates.WEBSITE_URL}

Shop now: [CLOTHING_STORE_LINK]

#GolfFashion #Golf #NewDrop"""
    
    @staticmethod
    def get_creator_x_handle(creator_name: str) -> Optional[str]:
        """Get X handle for a creator from whitelist"""
        try:
            whitelist_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'whitelist.json')
            with open(whitelist_path, 'r') as f:
                data = json.load(f)
            
            for channel in data['channels']:
                if channel['name'].lower() == creator_name.lower():
                    return channel.get('x_handle')
            
            return None
        except Exception as e:
            print(f"Error getting X handle: {e}")
            return None

# Post scheduling recommendations
POST_SCHEDULE = {
    "video_of_the_day": {
        "frequency": "daily",
        "time": "9:00 AM EST",  # Peak engagement time
        "description": "Daily featured video with creator tag"
    },
    "creator_of_the_week": {
        "frequency": "weekly", 
        "time": "Monday 10:00 AM EST",
        "description": "Weekly creator spotlight"
    },
    "trending_video": {
        "frequency": "as_needed",
        "trigger": "momentum_score > 3.0",
        "description": "Viral/trending content alerts"
    },
    "engagement_post": {
        "frequency": "3x per week",
        "time": "Various",
        "description": "Community building posts"
    },
    "brand_mention": {
        "frequency": "1x per week",
        "time": "Friday 11:00 AM EST", 
        "description": "Brand awareness building"
    },
    "weekly_roundup": {
        "frequency": "weekly",
        "time": "Sunday 7:00 PM EST",
        "description": "Week's best content summary"
    }
}