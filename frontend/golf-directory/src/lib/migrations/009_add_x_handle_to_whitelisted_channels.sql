-- Migration: Add x_handle column for social media integration

-- Add x_handle column
ALTER TABLE whitelisted_channels 
ADD COLUMN IF NOT EXISTS x_handle VARCHAR(255);

-- Create index for x_handle lookups
CREATE INDEX IF NOT EXISTS idx_whitelisted_channels_x_handle ON whitelisted_channels(x_handle) WHERE x_handle IS NOT NULL;