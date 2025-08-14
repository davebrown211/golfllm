-- Power Rankings Query
-- Shared between frontend display and backend reporting
-- Shows top YouTube channels by views from last 7 days with percentage change

WITH channel_views AS (
  SELECT 
    yc.id,
    yc.title as channel_name,
    SUM(yv.view_count) as total_views,
    COUNT(yv.id) as video_count
  FROM youtube_videos yv
  JOIN youtube_channels yc ON yv.channel_id = yc.id
  JOIN whitelisted_channels wc ON yv.channel_id = wc.channel_id
  WHERE yv.published_at >= NOW() - INTERVAL '7 days'
    AND wc.active = true
  GROUP BY yc.id, yc.title
),
previous_period AS (
  SELECT 
    yc.id,
    SUM(yv.view_count) as prev_total_views
  FROM youtube_videos yv
  JOIN youtube_channels yc ON yv.channel_id = yc.id
  JOIN whitelisted_channels wc ON yv.channel_id = wc.channel_id
  WHERE yv.published_at >= NOW() - INTERVAL '14 days'
    AND yv.published_at < NOW() - INTERVAL '7 days'
    AND wc.active = true
  GROUP BY yc.id
)
SELECT 
  cv.channel_name,
  cv.total_views,
  cv.video_count,
  COALESCE(
    ROUND(((cv.total_views - pp.prev_total_views)::numeric / NULLIF(pp.prev_total_views, 0)::numeric) * 100, 1),
    0
  ) as percent_change
FROM channel_views cv
LEFT JOIN previous_period pp ON cv.id = pp.id
ORDER BY cv.total_views DESC
LIMIT 20;