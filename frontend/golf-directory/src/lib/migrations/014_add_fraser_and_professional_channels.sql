-- Migration: Add Fraser Golf Institute and Professional Golf channels
-- Adds Fraser Golf Institute to instructional and creates professional golf category

-- Add Fraser Golf Institute to instructional channels
INSERT INTO whitelisted_channels (channel_id, name, channel_type, active, created_at, updated_at)
VALUES ('UCp2vwIOWZ1lSBY36MvainhA', 'Fraser Golf Institute', 'instructional', true, NOW(), NOW())
ON CONFLICT (channel_id) DO UPDATE
SET channel_type = 'instructional',
    name = 'Fraser Golf Institute',
    updated_at = NOW();

-- Add Professional Golf channels
-- PGA Tour
INSERT INTO whitelisted_channels (channel_id, name, channel_type, active, created_at, updated_at)
VALUES ('UCKwGZZMrhNYKzucCtTPY2Nw', 'PGA TOUR', 'professional', true, NOW(), NOW())
ON CONFLICT (channel_id) DO UPDATE
SET channel_type = 'professional',
    name = 'PGA TOUR',
    updated_at = NOW();

-- Golf Channel
INSERT INTO whitelisted_channels (channel_id, name, channel_type, active, created_at, updated_at)
VALUES ('UC5igJFdBQVqg7hXFI7075OQ', 'Golf Channel', 'professional', true, NOW(), NOW())
ON CONFLICT (channel_id) DO UPDATE
SET channel_type = 'professional',
    name = 'Golf Channel',
    updated_at = NOW();

-- DP World Tour (formerly European Tour)
INSERT INTO whitelisted_channels (channel_id, name, channel_type, active, created_at, updated_at)
VALUES ('UCvZwbZt6YZQ4wj_7qyjPDZw', 'DP World Tour', 'professional', true, NOW(), NOW())
ON CONFLICT (channel_id) DO UPDATE
SET channel_type = 'professional',
    name = 'DP World Tour',
    updated_at = NOW();

-- LPGA
INSERT INTO whitelisted_channels (channel_id, name, channel_type, active, created_at, updated_at)
VALUES ('UCWZbPo5_riXyCFDyaMl2yRA', 'LPGA', 'professional', true, NOW(), NOW())
ON CONFLICT (channel_id) DO UPDATE
SET channel_type = 'professional',
    name = 'LPGA',
    updated_at = NOW();

-- Korn Ferry Tour
INSERT INTO whitelisted_channels (channel_id, name, channel_type, active, created_at, updated_at)
VALUES ('UCZoQ6VBnQGF2T3hwevWLJUA', 'Korn Ferry Tour', 'professional', true, NOW(), NOW())
ON CONFLICT (channel_id) DO UPDATE
SET channel_type = 'professional',
    name = 'Korn Ferry Tour',
    updated_at = NOW();

-- LIV Golf
INSERT INTO whitelisted_channels (channel_id, name, channel_type, active, created_at, updated_at)
VALUES ('UCuC-Is0pVH9RudfZJw-LSmw', 'LIV Golf', 'professional', true, NOW(), NOW())
ON CONFLICT (channel_id) DO UPDATE
SET channel_type = 'professional',
    name = 'LIV Golf',
    updated_at = NOW();

-- PGA of America (Ryder Cup, PGA Championship)
INSERT INTO whitelisted_channels (channel_id, name, channel_type, active, created_at, updated_at)
VALUES ('UCwlBZF9q_d9B17FcaJeN7Mg', 'PGA of America', 'professional', true, NOW(), NOW())
ON CONFLICT (channel_id) DO UPDATE
SET channel_type = 'professional',
    name = 'PGA of America',
    updated_at = NOW();

-- USGA (US Open, US Amateur, etc)
INSERT INTO whitelisted_channels (channel_id, name, channel_type, active, created_at, updated_at)
VALUES ('UCsZsn_S93Zs8JOdKMRbklmg', 'United States Golf Association (USGA)', 'professional', true, NOW(), NOW())
ON CONFLICT (channel_id) DO UPDATE
SET channel_type = 'professional',
    name = 'United States Golf Association (USGA)',
    updated_at = NOW();

-- The R&A (The Open Championship, AIG Women's Open)
INSERT INTO whitelisted_channels (channel_id, name, channel_type, active, created_at, updated_at)
VALUES ('UCZ5fOnOmQunH18xZGhu9f_Q', 'The R&A', 'professional', true, NOW(), NOW())
ON CONFLICT (channel_id) DO UPDATE
SET channel_type = 'professional',
    name = 'The R&A',
    updated_at = NOW();

-- Ladies European Tour
INSERT INTO whitelisted_channels (channel_id, name, channel_type, active, created_at, updated_at)
VALUES ('UC9NboheGgkad3FwqEIk0JlA', 'Ladies European Tour', 'professional', true, NOW(), NOW())
ON CONFLICT (channel_id) DO UPDATE
SET channel_type = 'professional',
    name = 'Ladies European Tour',
    updated_at = NOW();