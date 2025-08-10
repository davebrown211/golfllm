import HomePage from '../components/HomePage'
import pool from '@/lib/database'

export const revalidate = 60 // Revalidate every 60 seconds

async function getCuratedVideos(offset: number = 0, limit: number = 200) {
  const client = await pool.connect()
  try {
    const query = `
      SELECT 
        ROW_NUMBER() OVER (ORDER BY yv.published_at DESC) as rank,
        yv.title,
        yc.title as channel,
        yv.view_count::text as views,
        yv.like_count::text as likes,
        CONCAT(ROUND(CAST(yv.engagement_rate AS numeric), 2), '%') as engagement,
        yv.published_at::text as published,
        CONCAT('https://youtube.com/watch?v=', yv.id) as url,
        yv.thumbnail_url as thumbnail
      FROM youtube_videos yv
      JOIN youtube_channels yc ON yv.channel_id = yc.id
      JOIN whitelisted_channels wc ON yv.channel_id = wc.channel_id
      WHERE wc.channel_type = 'regular' 
        AND wc.active = true
        AND yv.published_at >= NOW() - INTERVAL '14 days'
        AND yv.engagement_rate >= 1.0
        AND (yv.duration_seconds IS NULL OR yv.duration_seconds >= 120)
      ORDER BY yv.published_at DESC
      LIMIT $1 OFFSET $2
    `
    
    const result = await client.query(query, [limit, offset])
    return result.rows
  } finally {
    client.release()
  }
}

async function getDiscoveryVideos(offset: number = 0, limit: number = 200) {
  const client = await pool.connect()
  try {
    const query = `
      SELECT 
        ROW_NUMBER() OVER (ORDER BY yv.published_at DESC) as rank,
        yv.title,
        yc.title as channel,
        yv.view_count::text as views,
        yv.like_count::text as likes,
        CONCAT(ROUND(CAST(yv.engagement_rate AS numeric), 2), '%') as engagement,
        yv.published_at::text as published,
        CONCAT('https://youtube.com/watch?v=', yv.id) as url,
        yv.thumbnail_url as thumbnail
      FROM youtube_videos yv
      JOIN youtube_channels yc ON yv.channel_id = yc.id
      WHERE yv.title ILIKE '%golf%'
        AND yv.published_at >= NOW() - INTERVAL '14 days'
        AND yv.engagement_rate >= 2.0
        AND yv.view_count >= 5000
        AND (yv.duration_seconds IS NULL OR yv.duration_seconds >= 120)
        AND NOT EXISTS (
          SELECT 1 FROM whitelisted_channels wc 
          WHERE wc.channel_id = yv.channel_id AND wc.active = true
        )
      ORDER BY yv.published_at DESC
      LIMIT $1 OFFSET $2
    `
    
    const result = await client.query(query, [limit, offset])
    return result.rows
  } finally {
    client.release()
  }
}

async function getInstructionalVideos(offset: number = 0, limit: number = 200) {
  const client = await pool.connect()
  try {
    const query = `
      SELECT 
        ROW_NUMBER() OVER (ORDER BY yv.published_at DESC) as rank,
        yv.title,
        yc.title as channel,
        yv.view_count::text as views,
        yv.like_count::text as likes,
        CONCAT(ROUND(CAST(yv.engagement_rate AS numeric), 2), '%') as engagement,
        yv.published_at::text as published,
        CONCAT('https://youtube.com/watch?v=', yv.id) as url,
        yv.thumbnail_url as thumbnail
      FROM youtube_videos yv
      JOIN youtube_channels yc ON yv.channel_id = yc.id
      JOIN whitelisted_channels wc ON yv.channel_id = wc.channel_id
      WHERE wc.channel_type = 'instructional'
        AND wc.active = true
        AND yv.published_at >= NOW() - INTERVAL '14 days'
        AND yv.engagement_rate >= 0.5
        AND (yv.duration_seconds IS NULL OR yv.duration_seconds >= 120)
      ORDER BY yv.published_at DESC
      LIMIT $1 OFFSET $2
    `
    
    const result = await client.query(query, [limit, offset])
    return result.rows
  } finally {
    client.release()
  }
}

async function getStats() {
  const client = await pool.connect()
  try {
    const totalVideosQuery = 'SELECT COUNT(*) FROM youtube_videos'
    const totalChannelsQuery = 'SELECT COUNT(DISTINCT channel_id) FROM youtube_videos'
    
    const [videosResult, channelsResult] = await Promise.all([
      client.query(totalVideosQuery),
      client.query(totalChannelsQuery)
    ])
    
    return {
      total_videos: parseInt(videosResult.rows[0].count),
      total_channels: parseInt(channelsResult.rows[0].count),
      categories: {},
      last_updated: new Date().toISOString()
    }
  } finally {
    client.release()
  }
}

async function getVideosWithAudio() {
  const client = await pool.connect()
  try {
    const query = `
      SELECT 
        yv.id as video_id,
        yv.title,
        yc.title as channel,
        yv.view_count::text as views,
        yv.like_count::text as likes,
        CONCAT(ROUND(CAST(yv.engagement_rate AS numeric), 2), '%') as engagement,
        yv.published_at::text as published,
        CONCAT('https://youtube.com/watch?v=', yv.id) as url,
        yv.thumbnail_url as thumbnail,
        yv.view_velocity,
        yv.duration_seconds,
        yv.view_count as raw_view_count,
        va.result as ai_analysis,
        va.character_analysis,
        va.captions_preview,
        va.audio_url,
        va.status as analysis_status
      FROM youtube_videos yv
      JOIN youtube_channels yc ON yv.channel_id = yc.id
      JOIN video_analyses va ON va.youtube_url LIKE '%' || yv.id || '%'
      WHERE va.audio_url IS NOT NULL
        AND va.status = 'COMPLETED'
        AND yv.published_at >= NOW() - INTERVAL '30 days'
        AND (yv.duration_seconds IS NULL OR yv.duration_seconds >= 120)
      ORDER BY yv.published_at DESC
      LIMIT 10
    `
    
    const result = await client.query(query)
    return result.rows.map(video => ({
      ...video,
      is_short: video.duration_seconds && video.duration_seconds <= 60,
      days_ago: Math.floor((Date.now() - new Date(video.published).getTime()) / (1000 * 60 * 60 * 24))
    }))
  } finally {
    client.release()
  }
}

async function getVideoOfTheDay() {
  const client = await pool.connect()
  try {
    const { getVideoOfTheDayQuery } = require('../lib/video-of-the-day-query')
    
    const query = getVideoOfTheDayQuery()
    
    const result = await client.query(query)
    
    if (result.rows.length === 0) {
      return null
    }
    
    const video = result.rows[0]
    
    return {
      video_id: video.video_id,
      title: video.title,
      channel: video.channel,
      views: (video.view_count || 0).toString(),
      likes: (video.like_count || 0).toString(),
      engagement: video.engagement_rate ? `${video.engagement_rate}%` : 'N/A',
      published: video.published_at.toISOString().split('T')[0],
      url: `https://youtube.com/watch?v=${video.video_id}`,
      thumbnail: video.thumbnail_url,
      view_velocity: Math.round(video.view_velocity),
      momentum_score: Math.round(video.momentum_score),
      duration_seconds: video.duration_seconds,
      is_short: video.duration_seconds && video.duration_seconds <= 60,
      days_ago: Math.floor((Date.now() - new Date(video.published_at).getTime()) / (1000 * 60 * 60 * 24)),
      has_ai_analysis: !!video.ai_analysis,
      analysis_status: video.analysis_status || null,
      ai_summary: null, // Skip AI summary parsing for now since it's not displayed on main page
      audio_url: video.audio_url
    }
  } finally {
    client.release()
  }
}

function generateSummaryFromAnalysis(analysis: {
  result: string | null
  character_analysis: string | null
  captions_preview?: string | null
}): string {
  let summary = ''
  
  try {
    if (analysis.result) {
      const result = JSON.parse(analysis.result)
      
      if (result.summary) {
        summary += result.summary + '\n\n'
      } else if (result.analysis) {
        summary += result.analysis + '\n\n'
      }
      
      if (result.total_score || result.scores) {
        summary += `🏌️ Golf Performance: ${result.total_score || 'Multiple scores recorded'}\n\n`
      }
    }
    
    if (analysis.character_analysis) {
      const characters = JSON.parse(analysis.character_analysis)
      if (characters && characters.length > 0) {
        summary += '👥 Key Players:\n'
        characters.slice(0, 3).forEach((char: any) => {
          summary += `• ${char.name || 'Player'}: ${char.role || char.personality || 'Golf enthusiast'}\n`
        })
        summary += '\n'
      }
    }
    
    if (!summary && analysis.captions_preview) {
      summary = `📝 Video Content Preview:\n${analysis.captions_preview.substring(0, 300)}...\n\n`
    }
    
  } catch (error) {
    console.error('Error parsing analysis data:', error)
  }
  
  return summary || 'AI analysis completed but summary content is not available.'
}

export default async function Home() {
  const [curatedVideos, instructionalVideos, discoveryVideos, stats, videosWithAudio, videoOfTheDay] = await Promise.all([
    getCuratedVideos(),
    getInstructionalVideos(),
    getDiscoveryVideos(),
    getStats(),
    getVideosWithAudio(),
    getVideoOfTheDay()
  ])

  return (
    <HomePage 
      initialCuratedVideos={curatedVideos}
      initialInstructionalVideos={instructionalVideos}
      initialDiscoveryVideos={discoveryVideos}
      initialStats={stats}
      initialVideosWithAudio={videosWithAudio}
      initialVideoOfTheDay={videoOfTheDay}
    />
  )
}