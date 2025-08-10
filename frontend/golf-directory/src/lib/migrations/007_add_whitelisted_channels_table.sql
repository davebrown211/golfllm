-- Migration: Add whitelisted channels table
-- This replaces the JSON/file-based whitelist with a database table

CREATE TABLE IF NOT EXISTS whitelisted_channels (
    channel_id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(500),
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for performance
CREATE INDEX IF NOT EXISTS idx_whitelisted_channels_active ON whitelisted_channels(active) WHERE active = true;

-- Insert current whitelist data from JSON
-- This will be populated by the migration script