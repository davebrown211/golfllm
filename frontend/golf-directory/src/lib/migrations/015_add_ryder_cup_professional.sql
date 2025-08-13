-- Migration: Add Ryder Cup to professional golf whitelist
-- Purpose: Add official Ryder Cup channel for professional golf coverage

INSERT INTO whitelisted_channels (channel_id, name, channel_type, active, created_at, updated_at)
VALUES ('UCFiswEI_awoQBRQ1JK6v0cA', 'Ryder Cup', 'professional', true, NOW(), NOW())
ON CONFLICT (channel_id) 
DO UPDATE SET 
    name = EXCLUDED.name,
    channel_type = EXCLUDED.channel_type,
    active = EXCLUDED.active,
    updated_at = NOW();