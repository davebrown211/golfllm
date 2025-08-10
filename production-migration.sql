-- PRODUCTION MIGRATION SCRIPT
-- Run this against the production database before deploying code changes
-- This creates the whitelisted_channels table and migrates data from JSON files

-- Step 1: Create whitelisted_channels table
CREATE TABLE IF NOT EXISTS whitelisted_channels (
    channel_id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(500),
    active BOOLEAN DEFAULT true,
    channel_type VARCHAR(50) DEFAULT 'regular',
    x_handle VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Step 2: Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_whitelisted_channels_active ON whitelisted_channels(active) WHERE active = true;
CREATE INDEX IF NOT EXISTS idx_whitelisted_channels_type ON whitelisted_channels(channel_type, active);
CREATE INDEX IF NOT EXISTS idx_whitelisted_channels_x_handle ON whitelisted_channels(x_handle) WHERE x_handle IS NOT NULL;

-- Step 3: Insert regular whitelist channels (from whitelist.json)
-- You'll need to run a data migration script to populate these
INSERT INTO whitelisted_channels (channel_id, name, channel_type, x_handle, active) VALUES
-- These are the channels that need to be migrated from your JSON files
-- Run the populate-whitelist-production.py script to populate this data
-- The script will read from whitelist.json and instructional_whitelist.json
('PLACEHOLDER', 'Run populate script', 'regular', null, true)
ON CONFLICT (channel_id) DO NOTHING;

-- Step 4: Verify the migration
SELECT 
    channel_type,
    COUNT(*) as channel_count,
    COUNT(x_handle) as channels_with_x_handle
FROM whitelisted_channels 
WHERE active = true
GROUP BY channel_type;