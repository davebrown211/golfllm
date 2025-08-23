-- Migration 007: Add Instructional Golf Channels to Whitelist
-- Generated: 2025-08-22
-- Purpose: Add 12 new instructional golf channels found via YouTube API lookup

-- Add instructional golf channels with conflict prevention
INSERT INTO whitelisted_channels (channel_id, name, channel_type, active, created_at) VALUES 
('UCRdhuKpjc5HHhJWNO38cFpA', 'Your guide to better golf - Marcus Edblad PGA Pro', 'instructional', true, NOW()),
('UCpJdS27RPLIk35V9jfia-Kw', 'Lower My Handicap', 'instructional', true, NOW()),
('UCl-VhMIMNZl5_WEnLCJEMvA', 'Sonic Titan Golf', 'instructional', true, NOW()),
('UCycctzzo7hka446fumoKpVA', 'World Class Golf Swing Motion', 'instructional', true, NOW()),
('UCQsD1erhJDFIkU6VRdfrwwg', 'Short Game Golf Academy', 'instructional', true, NOW()),
('UCVHju40gfZd3rYju6lnUkmA', 'Short Game Sous Chef', 'instructional', true, NOW()),
('UCo-lKZldxD7u_ZtBw9PnZXg', 'Kerrod Gray Golf', 'instructional', true, NOW()),
('UC6gTua_lAUwmZcw9Y0j2ohQ', 'thegolfprojx', 'instructional', true, NOW()),
('UCWmpcXvVbE3hSt04S7qMoUw', 'Bausek Golf', 'instructional', true, NOW()),
('UCy_goEdC7q0Zz2IHYGOGK2g', 'Ashley Knoll Golf', 'instructional', true, NOW()),
('UCBvj-_3BiEtW1uHYLdj4s7Q', 'Jerome Rufin', 'instructional', true, NOW()),
('UCSUVEHltWL-HQePj4lRE0_g', 'Steve Pratt Golf', 'instructional', true, NOW())
ON CONFLICT (channel_id) DO NOTHING;

-- Summary: Added 12 new instructional channels
-- Notable channels: Kerrod Gray Golf (132k subs), Jerome Rufin (108k subs), Steve Pratt Golf (118k subs)
-- Note: Danny Maude and Eric Cogorno were already whitelisted