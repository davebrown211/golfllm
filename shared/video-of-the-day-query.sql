-- Video of the Day Query
-- Shared between frontend (page.tsx) and backend (ai_video_of_day_runner.py)
-- SIMPLIFIED: Pick the highest view count video published TODAY from whitelisted channels

SELECT 
  yv.id as video_id,
  yv.title,
  yc.title as channel,
  yv.view_count,
  yv.like_count,
  yv.engagement_rate,
  yv.published_at,
  yv.view_velocity,
  yv.thumbnail_url,
  yv.duration_seconds,
  yv.view_count as momentum_score,  -- Just use view count as the score
  va.result as ai_analysis,
  va.character_analysis,
  va.captions_preview,
  va.audio_url,
  va.status as analysis_status
FROM youtube_videos yv
JOIN youtube_channels yc ON yv.channel_id = yc.id
LEFT JOIN video_analyses va ON va.youtube_url LIKE '%' || yv.id || '%'
  AND va.status = 'COMPLETED'
WHERE DATE(yv.published_at AT TIME ZONE 'UTC') = CURRENT_DATE - INTERVAL '1 day'  -- Published YESTERDAY (gives time for views to accumulate)
  AND yv.view_count > 10000  -- Minimum threshold for quality
  AND yv.thumbnail_url IS NOT NULL
  AND (yv.duration_seconds IS NULL OR yv.duration_seconds >= 120)  -- At least 2 minutes
  AND yv.channel_id IN (SELECT channel_id FROM whitelisted_channels WHERE active = true AND channel_type = 'regular')
  -- Exclude non-golf content
  AND yv.title !~ '[あ-ん]'  -- Exclude Japanese hiragana
  AND yv.title !~ '[ア-ン]'  -- Exclude Japanese katakana
  AND yv.title !~ '[一-龯]'  -- Exclude Chinese/Japanese kanji
  AND yv.title NOT ILIKE '%volkswagen%'
  AND yv.title NOT ILIKE '%vw golf%'
  AND yv.title NOT ILIKE '%gta%'
  AND yv.title NOT ILIKE '%forza%'
  AND yv.title NOT ILIKE '%golf cart%'
ORDER BY yv.view_count DESC  -- Highest view count wins
LIMIT 1;