'use client'

import Marquee from "react-fast-marquee"

interface PowerRanking {
  channel_name: string
  total_views: number
  video_count: number
  percent_change: number
}

interface PowerRankingsTickerProps {
  rankings: PowerRanking[]
}

export default function PowerRankingsTicker({ rankings }: PowerRankingsTickerProps) {
  const formatViews = (views: number) => {
    if (views >= 1000000) {
      return `${(views / 1000000).toFixed(1)}M`
    } else if (views >= 1000) {
      return `${Math.round(views / 1000)}K`
    }
    return views.toString()
  }

  return (
    <>
      <div className="relative w-full bg-gray-900 border-b border-gray-800">
        <Marquee
          speed={50}
          gradient={false}
          pauseOnHover={false}
          className="h-10"
        >
          {rankings.map((channel, index) => (
            <div key={channel.channel_name} className="flex items-center mx-6">
              <span className="text-gray-400 text-sm">#{index + 1}</span>
              <span className="text-white text-sm font-medium mx-2">{channel.channel_name}</span>
              <span className="text-gray-400 text-sm">({formatViews(channel.total_views)})</span>
              <span 
                className={`text-sm font-medium mx-2 ${
                  channel.percent_change > 0 
                    ? 'text-green-400' 
                    : channel.percent_change < 0 
                    ? 'text-red-400' 
                    : 'text-gray-400'
                }`}
              >
                {channel.percent_change > 0 ? '+' : ''}{channel.percent_change}%
              </span>
              <span className="text-gray-600 mx-2">•</span>
            </div>
          ))}
        </Marquee>
      </div>
      <div className="text-center py-1">
        <span className="text-xs text-gray-600">7 day performance</span>
      </div>
    </>
  )
}