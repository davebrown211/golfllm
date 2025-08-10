-- Migration: Add channel types to support both regular and instructional channels

-- Add channel_type column
ALTER TABLE whitelisted_channels 
ADD COLUMN IF NOT EXISTS channel_type VARCHAR(50) DEFAULT 'regular';

-- Add index for performance
CREATE INDEX IF NOT EXISTS idx_whitelisted_channels_type ON whitelisted_channels(channel_type, active);

-- Update existing channels to be 'regular' type
UPDATE whitelisted_channels SET channel_type = 'regular' WHERE channel_type IS NULL;