# YouTube Data API Capabilities for Golf Directory

## What You Can Get for Free (with API Key)

### 1. **Video Metadata**
- **Basic Info**: Title, description, upload date, duration
- **Statistics**: View count, like count, comment count, dislike count (hidden now)
- **Channel Info**: Channel name, channel ID
- **Thumbnails**: Multiple resolutions available
- **Tags**: Video tags (if made public by uploader)
- **Category**: Sports category (ID: 17)

### 2. **Search Capabilities**
```python
# Search parameters available:
- q: Query string ("golf", "PGA tour", "golf instruction")
- order: date, rating, relevance, title, viewCount
- publishedAfter/Before: Date filters
- videoDuration: short (<4min), medium (4-20min), long (>20min)
- videoDefinition: HD or SD
- regionCode: Country-specific results
```

### 3. **Channel Analytics**
- Subscriber count
- Total view count
- Video count
- Channel description
- Channel thumbnails

### 4. **Trending Detection**
- Filter by upload date + sort by views = trending videos
- Compare view velocity (views per day since upload)
- Track viral moments

## Data You CAN'T Get
- View history over time (only current total)
- Detailed demographics
- Revenue/monetization data
- Unlisted/private videos
- Retention graphs
- Click-through rates

## Quota Limits
- Default: 10,000 units per day
- Search costs: 100 units
- Video details: 1 unit per video
- This allows ~100 searches or ~10,000 video detail requests per day

## Pivot Strategy Using This Data

### Option 1: Golf Video Rankings
- **Daily/Weekly Leaderboards**: "Most Viewed Golf Videos"
- **Rising Stars**: Videos with high view velocity
- **Category Rankings**: Best instruction, equipment reviews, tour highlights
- **Channel Rankings**: Top golf YouTubers by subscribers/views

### Option 2: Golf Content Discovery Engine
- **Smart Search**: Better golf video search than YouTube itself
- **Curated Collections**: "Best Putting Tips", "Driver Reviews 2024"
- **Trending Alerts**: Notify when golf videos go viral
- **Tournament Trackers**: Aggregate all videos from major tournaments

### Option 3: Golf Creator Analytics Platform
- **Channel Tracking**: Monitor growth of golf content creators
- **Performance Benchmarks**: Compare video performance
- **Content Calendar**: Track what topics perform best when
- **Sponsorship Opportunities**: Connect brands with rising golf influencers

### Option 4: Hybrid Approach
- Use metadata to identify high-value videos
- Run AI analysis only on videos that cross certain thresholds:
  - Over 100k views
  - High engagement rate
  - From verified golf channels
- This reduces AI costs by 95%+ while still providing deep insights

## Implementation Approach

1. **Phase 1**: Build metadata aggregation (1-2 weeks)
   - Set up YouTube API integration
   - Create database for video/channel data
   - Build basic ranking algorithms

2. **Phase 2**: Add discovery features (2-3 weeks)
   - Implement search and filtering
   - Create category classifications
   - Build trending detection

3. **Phase 3**: User features (2-3 weeks)
   - User accounts and favorites
   - Email alerts for trending content
   - Social sharing features

4. **Phase 4**: Monetization (ongoing)
   - Premium features (advanced analytics)
   - Affiliate links to golf equipment
   - Sponsored content sections
   - API access for other developers

## Cost Comparison
- **Current approach**: $0.0015 per minute of video analyzed with Gemini
- **Metadata approach**: ~$0.00001 per video (just API quota)
- **Savings**: 99.99%+ reduction in costs

## Next Steps
1. Set up YouTube Data API credentials
2. Test the metadata extraction script
3. Analyze sample data to validate the pivot
4. Design the new directory structure
5. Build MVP focused on metadata features