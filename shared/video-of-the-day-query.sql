-- Video of the Day Query
-- Shared between frontend (page.tsx) and backend (ai_video_of_day_runner.py)
-- This ensures both use identical selection logic

WITH trending_candidates AS (
  SELECT 
    yv.id,
    yv.title,
    yc.title as channel,
    yv.view_count,
    yv.like_count,
    yv.engagement_rate,
    yv.published_at,
    yv.view_velocity,
    yv.thumbnail_url,
    yv.duration_seconds,
    va.result as ai_analysis,
    va.character_analysis,
    va.captions_preview,
    va.audio_url,
    va.status as analysis_status,
    CASE 
      WHEN vo.video_id IS NOT NULL THEN yv.view_count * 10000
      WHEN yv.published_at >= CURRENT_DATE THEN yv.view_count * 5000
      WHEN yv.published_at >= NOW() - '1 day'::interval THEN yv.view_count * 100
      WHEN yv.published_at >= NOW() - '2 day'::interval THEN yv.view_count * 10
      WHEN yv.published_at >= NOW() - '3 day'::interval THEN yv.view_count * 1
      ELSE yv.view_count * 0.001
    END as momentum_score
  FROM youtube_videos yv
  JOIN youtube_channels yc ON yv.channel_id = yc.id
  LEFT JOIN video_analyses va ON va.youtube_url LIKE '%' || yv.id || '%'
    AND va.status = 'COMPLETED'
  LEFT JOIN video_overrides vo ON vo.video_id = yv.id 
    AND vo.override_date = CURRENT_DATE 
    AND vo.active = true
  WHERE yv.published_at >= NOW() - '14 day'::interval
    AND yv.view_count > 100
    AND (yv.engagement_rate > 0.1 OR yv.engagement_rate IS NULL)
    AND yv.thumbnail_url IS NOT NULL
    AND (yv.duration_seconds IS NULL OR yv.duration_seconds >= 120)
    AND yv.channel_id IN (SELECT channel_id FROM whitelisted_channels WHERE active = true AND channel_type = 'regular')
    AND yv.title !~ '[あ-ん]'  -- Exclude Japanese hiragana
    AND yv.title !~ '[ア-ン]'  -- Exclude Japanese katakana
    AND yv.title !~ '[一-龯]'  -- Exclude Chinese/Japanese kanji
    AND yv.title !~ '[À-ÿ]'   -- Exclude accented characters
    AND yv.title NOT ILIKE '%volkswagen%'
    AND yv.title NOT ILIKE '%vw golf%'
    AND yv.title NOT ILIKE '%gta%'
    AND yv.title NOT ILIKE '%forza%'
    AND yv.title NOT ILIKE '%drive beyond%'
    AND yv.title NOT ILIKE '%golf cart%'
)
SELECT 
  id as video_id,
  title,
  channel,
  view_count,
  like_count,
  engagement_rate,
  published_at,
  view_velocity,
  thumbnail_url,
  duration_seconds,
  momentum_score,
  ai_analysis,
  character_analysis,
  captions_preview,
  audio_url,
  analysis_status
FROM trending_candidates
ORDER BY momentum_score DESC, view_velocity DESC, engagement_rate DESC
LIMIT 1;