-- Migration: Remove Brooks Holt from whitelist
-- Reason: Testing migration system

-- Remove Brooks Holt from whitelisted_channels
DELETE FROM whitelisted_channels 
WHERE channel_id = 'UC7m4k9X2pRxuvzpwSz5jWgQ'
   OR LOWER(name) = 'brooks holt';

-- Log the removal
DO $$
BEGIN
    RAISE NOTICE 'Removed Brooks Holt from whitelist at %', NOW();
END
$$;