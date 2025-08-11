-- Migration: Add video overrides table for Video of the Day scheduling
-- Allows specific videos to receive 100x multiplier on specific dates

CREATE TABLE IF NOT EXISTS video_overrides (
    id SERIAL PRIMARY KEY,
    override_date DATE NOT NULL,
    video_id VARCHAR(255) NOT NULL,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for fast lookups by date
CREATE INDEX IF NOT EXISTS idx_video_overrides_date_active ON video_overrides(override_date, active) WHERE active = true;

-- Create index for video_id lookups
CREATE INDEX IF NOT EXISTS idx_video_overrides_video_id ON video_overrides(video_id) WHERE active = true;

-- Example data (uncomment and modify as needed):
-- INSERT INTO video_overrides (override_date, video_id) VALUES
-- ('2025-08-11', 'exampleVideoId1'),
-- ('2025-08-11', 'anotherVideoId'),
-- ('2025-12-25', 'christmasSpecial');