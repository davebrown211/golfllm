// Utility functions for Golf Directory

// Format view count for display
export function formatViews(views: string | number): string {
  const num = typeof views === 'string' ? parseInt(views.replace(/,/g, '')) : views
  
  if (num >= 1000000) {
    return `${Math.floor(num / 1000000)}M`
  } else if (num >= 1000) {
    return `${Math.floor(num / 1000)}K`
  }
  
  return num.toLocaleString()
}

// Format duration from seconds to MM:SS
export function formatDuration(seconds: number): string {
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60
  return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`
}

// Parse engagement rate percentage
export function parseEngagement(engagement: string): number {
  return parseFloat(engagement.replace('%', ''))
}

// Export as api object for backwards compatibility
export const api = {
  formatViews,
  formatDuration,
  parseEngagement
}