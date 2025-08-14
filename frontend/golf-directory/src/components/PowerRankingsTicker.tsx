"use client";

import Marquee from "react-fast-marquee";

interface PowerRanking {
  channel_name: string;
  total_views: number;
  video_count: number;
  percent_change: number;
}

interface PowerRankingsTickerProps {
  rankings: PowerRanking[];
}

export default function PowerRankingsTicker({
  rankings,
}: PowerRankingsTickerProps) {
  const formatViews = (views: number) => {
    if (views >= 1000000) {
      return `${(views / 1000000).toFixed(1)}M`;
    } else if (views >= 1000) {
      return `${Math.round(views / 1000)}K`;
    }
    return views.toString();
  };

  return (
    <>
      <div className="relative w-full bg-gray-900 border-b border-gray-800">
        <Marquee
          speed={50}
          gradient={false}
          pauseOnHover={false}
          delay={3}
          className="h-10"
        >
          {rankings.map((channel, index) => (
            <div key={channel.channel_name} className="flex items-center mx-6">
              <span className="text-sm text-gray-400">#{index + 1}</span>
              <span className="mx-2 text-sm font-medium text-white">
                {channel.channel_name}
              </span>
              <span className="text-sm text-gray-400">
                ({formatViews(channel.total_views)})
              </span>
              <span
                className={`text-sm font-medium mx-2 ${
                  channel.percent_change > 0
                    ? "text-green-400"
                    : channel.percent_change < 0
                    ? "text-red-400"
                    : "text-gray-400"
                }`}
              >
                {channel.percent_change > 0 ? "+" : ""}
                {channel.percent_change}%
              </span>
              <span className="mx-2 text-gray-600">•</span>
            </div>
          ))}
        </Marquee>
      </div>
      <div className="py-1 text-center">
        <span className="text-xs text-gray-600">
          7 day view count performance
        </span>
      </div>
    </>
  );
}
