-- Golf Directory Database Setup
-- Run this on your DigitalOcean PostgreSQL database

-- Create the main database schema
-- (Note: This assumes you're using the 'defaultdb' database)

-- YouTube Videos table
CREATE TABLE IF NOT EXISTS youtube_videos (
    id VARCHAR(20) PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    channel_id VARCHAR(30) NOT NULL,
    published_at TIMESTAMP WITH TIME ZONE NOT NULL,
    view_count BIGINT DEFAULT 0,
    like_count BIGINT DEFAULT 0,
    comment_count BIGINT DEFAULT 0,
    engagement_rate DECIMAL(5,2) DEFAULT 0,
    duration_seconds INTEGER DEFAULT 0,
    thumbnail_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- YouTube Channels table
CREATE TABLE IF NOT EXISTS youtube_channels (
    id VARCHAR(30) PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    subscriber_count BIGINT DEFAULT 0,
    video_count INTEGER DEFAULT 0,
    view_count BIGINT DEFAULT 0,
    thumbnail_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Video Analyses table (for AI-generated summaries)
CREATE TABLE IF NOT EXISTS video_analyses (
    id SERIAL PRIMARY KEY,
    video_id VARCHAR(20) NOT NULL REFERENCES youtube_videos(id),
    summary TEXT,
    audio_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(video_id)
);

-- API Quota Usage table
CREATE TABLE IF NOT EXISTS api_quota_usage (
    date DATE PRIMARY KEY,
    search_operations INTEGER DEFAULT 0,
    video_list_operations INTEGER DEFAULT 0,
    channel_list_operations INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Video View History table (for tracking view count changes)
CREATE TABLE IF NOT EXISTS video_view_history (
    id SERIAL PRIMARY KEY,
    video_id VARCHAR(20) NOT NULL REFERENCES youtube_videos(id),
    view_count BIGINT NOT NULL,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Monitored Channels table (for whitelisted channels)
CREATE TABLE IF NOT EXISTS monitored_channels (
    id SERIAL PRIMARY KEY,
    channel_id VARCHAR(30) NOT NULL UNIQUE,
    channel_name TEXT,
    is_whitelisted BOOLEAN DEFAULT true,
    priority INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_youtube_videos_channel_id ON youtube_videos(channel_id);
CREATE INDEX IF NOT EXISTS idx_youtube_videos_published_at ON youtube_videos(published_at);
CREATE INDEX IF NOT EXISTS idx_youtube_videos_view_count ON youtube_videos(view_count);
CREATE INDEX IF NOT EXISTS idx_youtube_videos_updated_at ON youtube_videos(updated_at);
CREATE INDEX IF NOT EXISTS idx_youtube_videos_duration ON youtube_videos(duration_seconds);

CREATE INDEX IF NOT EXISTS idx_video_analyses_video_id ON video_analyses(video_id);
CREATE INDEX IF NOT EXISTS idx_video_view_history_video_id ON video_view_history(video_id);
CREATE INDEX IF NOT EXISTS idx_video_view_history_recorded_at ON video_view_history(recorded_at);

-- Insert whitelisted channels (major golf creators)
INSERT INTO monitored_channels (channel_id, channel_name, is_whitelisted, priority) VALUES
('UCgz5-3igA0IfsU7StatmjMw', 'Good Good', true, 1),
('UCCz0skLgV2Yz1KsYFJMnVAw', 'Bob Does Sports', true, 1),
('UCiWLfSweyRNmLpgEHekhoAg', 'Rick Shiels Golf', true, 1),
('UC9xp_l1rNqX3v6k56-vRmLg', 'Mark Crossfield', true, 1),
('UCFeQXP9gzJJPJ6R1fgLQBaA', 'Peter Finch Golf', true, 1),
('UC2BAV5QR54tL80p-_RvANZA', 'TXG Tour Experience Golf', true, 1),
('UCBJVmUjgF1AJq7QfQi3LGfQ', 'The Golf Club', true, 1),
('UC4nJl-lPKKr_fNsApIpE4jQ', 'Fore Play', true, 1),
('UC4dSx4tHYW9a3n0gGPfR_Ng', 'Golfholics', true, 1),
('UCANFbrQgEFWmRJFZtA2CeFA', 'Me and My Golf', true, 1)
ON CONFLICT (channel_id) DO NOTHING;

-- Create a view for user-facing videos (matches the scheduler logic)
CREATE OR REPLACE VIEW user_facing_videos AS
WITH curated_videos AS (
    SELECT yv.id, yv.updated_at, yv.published_at, yv.view_count, 1 as priority
    FROM youtube_videos yv 
    JOIN youtube_channels yc ON yv.channel_id = yc.id
    JOIN monitored_channels mc ON yv.channel_id = mc.channel_id
    WHERE mc.is_whitelisted = true
      AND yv.published_at >= NOW() - INTERVAL '90 days'
      AND yv.view_count > 100
      AND yv.duration_seconds >= 180
    ORDER BY yv.published_at DESC
    LIMIT 50
),
video_of_day_candidates AS (
    SELECT yv.id, yv.updated_at, yv.published_at, yv.view_count, 2 as priority
    FROM youtube_videos yv
    JOIN youtube_channels yc ON yv.channel_id = yc.id
    JOIN monitored_channels mc ON yv.channel_id = mc.channel_id
    WHERE yv.published_at >= NOW() - INTERVAL '14 days'
      AND yv.view_count > 100
      AND mc.is_whitelisted = true
      AND yv.duration_seconds >= 60
      AND yv.thumbnail_url IS NOT NULL
    ORDER BY 
      CASE 
        WHEN yv.published_at >= NOW() - INTERVAL '1 day' THEN yv.view_count * 1000
        WHEN yv.published_at >= NOW() - INTERVAL '2 days' THEN yv.view_count * 100  
        WHEN yv.published_at >= NOW() - INTERVAL '3 days' THEN yv.view_count * 10
        ELSE yv.view_count
      END DESC
    LIMIT 20
)
SELECT * FROM curated_videos
UNION ALL
SELECT * FROM video_of_day_candidates;

-- Grant permissions (if needed)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO your_user;

-- Print success message
DO $$
BEGIN
    RAISE NOTICE 'Golf Directory database schema created successfully!';
    RAISE NOTICE 'Tables created: youtube_videos, youtube_channels, video_analyses, api_quota_usage, video_view_history, monitored_channels';
    RAISE NOTICE 'Indexes created for optimal performance';
    RAISE NOTICE 'Whitelisted channels inserted';
    RAISE NOTICE 'Ready for scheduler deployment!';
END $$;