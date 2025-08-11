-- Migration: Create migrations tracking table for automated deployment system
-- This table tracks which migrations have been applied to prevent duplicates

CREATE TABLE IF NOT EXISTS migrations (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL UNIQUE,
    migration_number INTEGER NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending', -- 'pending', 'completed', 'failed'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    applied_at TIMESTAMP NULL,
    error_message TEXT NULL
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_migrations_status ON migrations(status);
CREATE INDEX IF NOT EXISTS idx_migrations_number ON migrations(migration_number);
CREATE INDEX IF NOT EXISTS idx_migrations_created_at ON migrations(created_at);

-- Prepopulate with existing migrations that have already been applied
INSERT INTO migrations (filename, migration_number, status, created_at, applied_at) VALUES
('004_add_quota_tracking.sql', 4, 'completed', '2024-07-01 00:00:00', '2024-07-01 00:00:00'),
('005_add_audio_url_to_video_analyses.sql', 5, 'completed', '2024-07-01 00:00:00', '2024-07-01 00:00:00'),
('006_add_content_type.sql', 6, 'completed', '2024-07-01 00:00:00', '2024-07-01 00:00:00'),
('007_add_whitelisted_channels_table.sql', 7, 'completed', '2025-08-10 00:00:00', '2025-08-10 00:00:00'),
('008_add_channel_types.sql', 8, 'completed', '2025-08-10 00:00:00', '2025-08-10 00:00:00'),
('009_add_x_handle_to_whitelisted_channels.sql', 9, 'completed', '2025-08-10 00:00:00', '2025-08-10 00:00:00'),
('010_add_video_overrides_table.sql', 10, 'completed', '2025-08-10 00:00:00', '2025-08-10 00:00:00'),
('011_create_migrations_table.sql', 11, 'completed', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
ON CONFLICT (filename) DO NOTHING;