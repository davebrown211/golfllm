"use client";

import { useState, useEffect, useRef } from "react";
import { Play, Eye } from "lucide-react";
import { api } from "@/lib/api";

interface VideoWithAudio {
  video_id: string;
  title: string;
  channel: string;
  views: string;
  likes: string;
  engagement: string;
  published: string;
  url: string;
  thumbnail: string;
  duration_seconds: number;
  is_short: boolean;
  days_ago: number;
  audio_url: string;
  ai_summary: string;
  is_video_of_day: boolean;
}

interface VideoOfTheDayCarouselMouseProps {
  initialVideosWithAudio?: any[];
  initialVideoOfTheDay?: any;
}

export default function VideoOfTheDayCarouselMouse({
  initialVideosWithAudio = [],
  initialVideoOfTheDay = null,
}: VideoOfTheDayCarouselMouseProps = {}) {
  // Initialize videos from server-side data
  const initialVideos = (() => {
    const data = { videos: initialVideosWithAudio };

    // Check if VOD is already in our list
    const hasVod = data.videos.some(
      (v: VideoWithAudio) => v.video_id === initialVideoOfTheDay?.video_id
    );

    if (!hasVod && initialVideoOfTheDay) {
      // Add VOD at the beginning
      data.videos.unshift({
        ...initialVideoOfTheDay,
        audio_url: initialVideoOfTheDay.audio_url || null,
        ai_summary: initialVideoOfTheDay.ai_summary || null,
        is_video_of_day: true,
      });
    }

    // Sort videos by creation date (most recent first) but keep video of the day first
    return [...data.videos].sort((a, b) => {
      // Video of the day always comes first
      if (a.is_video_of_day && !b.is_video_of_day) return -1;
      if (!a.is_video_of_day && b.is_video_of_day) return 1;

      // For other videos, sort by published date (newest first)
      return new Date(b.published).getTime() - new Date(a.published).getTime();
    });
  })();

  const [videos] = useState<VideoWithAudio[]>(initialVideos);
  const [, setCurrentIndex] = useState(0);
  const [error] = useState<string | null>(null);
  const [mobileCurrentIndex, setMobileCurrentIndex] = useState(0); // For mobile pagination
  const [focusedIndex, setFocusedIndex] = useState(() => {
    // Find the video of the day index (should be 0 after sorting)
    const vodIndex = initialVideos.findIndex(
      (v: VideoWithAudio) => v.is_video_of_day
    );
    return vodIndex !== -1 ? vodIndex : 0;
  });
  const containerRef = useRef<HTMLDivElement>(null);

  // Set the initial current index to match focused index
  useEffect(() => {
    const vodIndex = videos.findIndex((v: VideoWithAudio) => v.is_video_of_day);
    const initialIndex = vodIndex !== -1 ? vodIndex : 0;
    setCurrentIndex(initialIndex);
  }, [videos]);

  const formatViews = (views: string) => {
    const num = parseInt(views.replace(/,/g, ""));
    return api.formatViews(num);
  };

  const getDaysAgoText = (daysAgo: number) => {
    if (daysAgo === 0) return "Today";
    if (daysAgo === 1) return "Yesterday";
    if (daysAgo <= 7) return `${daysAgo} days ago`;
    const weeks = Math.floor(daysAgo / 7);
    return `${weeks} week${weeks > 1 ? "s" : ""} ago`;
  };

  // Mobile navigation functions
  const goToNext = () => {
    setMobileCurrentIndex((prev) => (prev + 1) % videos.length);
  };

  const goToPrevious = () => {
    setMobileCurrentIndex((prev) => (prev - 1 + videos.length) % videos.length);
  };

  // Handle clicking on video cards to focus them
  const handleVideoClick = (e: React.MouseEvent, clickedIndex: number) => {
    e.preventDefault();
    e.stopPropagation();

    // Don't change focus if clicking on interactive elements
    const target = e.target as HTMLElement;
    const tagName = target.tagName.toLowerCase();

    if (
      tagName === "audio" ||
      tagName === "button" ||
      tagName === "a" ||
      target.closest("audio") ||
      target.closest("button") ||
      target.closest("a")
    ) {
      return;
    }

    // Focus the clicked video
    setFocusedIndex(clickedIndex);
    setCurrentIndex(clickedIndex);
  };

  if (error || videos.length === 0) {
    return null;
  }

  return (
    <div className="mb-8 md:mb-16">
      {/* Desktop Carousel */}
      <div
        ref={containerRef}
        className="hidden md:block relative h-[500px] overflow-hidden"
      >
        {/* Videos Track */}
        <div className="flex absolute inset-0 justify-center items-center">
          {videos.map((video, index) => {
            // Calculate position and scale based on focused video
            const distance = Math.abs(index - focusedIndex);

            // Scale and opacity based on distance from center - make focus more prominent
            const scale = Math.max(0.3, 1 - distance * 0.5);
            const opacity = Math.max(0.15, 1 - distance * 0.5);
            const blur = distance > 0.2 ? Math.min(6, distance * 3) : 0;

            // Position calculation for smooth flow
            const baseSpacing = 350;
            const position = (index - focusedIndex) * baseSpacing;

            const zIndex = Math.round(100 - distance * 10);
            const isActive = index === focusedIndex;

            return (
              <div
                key={video.video_id}
                className="flex absolute justify-center items-center"
                style={{
                  transform: `translateX(${position}px) scale(${scale})`,
                  opacity: opacity,
                  filter: `blur(${blur}px)`,
                  zIndex: zIndex,
                  transition: "all 0.3s cubic-bezier(0.25, 0.1, 0.25, 1)",
                  width: "750px",
                  height: "450px",
                  left: "50%",
                  top: "50%",
                  marginLeft: "-375px",
                  marginTop: "-225px",
                  pointerEvents: "auto",
                }}
              >
                {/* Video Card */}
                <div
                  className={`bg-gradient-to-r from-purple-900 via-purple-800 to-indigo-900 rounded-3xl p-6 shadow-2xl border border-purple-500/20 ${
                    isActive ? "ring-2 ring-purple-400" : ""
                  }`}
                  onClick={(e) => handleVideoClick(e, index)}
                >
                  {/* Indicator */}
                  <div className="mb-4">
                    <p className="text-sm text-purple-300">
                      🔥{" "}
                      {video.is_video_of_day
                        ? "Video of the Day"
                        : "Featured Video"}{" "}
                      • {getDaysAgoText(video.days_ago)}
                    </p>
                  </div>

                  <div className="grid gap-6 items-center lg:grid-cols-2">
                    {/* Video Thumbnail */}
                    <div
                      className="relative cursor-pointer group"
                      onClick={() =>
                        isActive && window.open(video.url, "_blank")
                      }
                    >
                      <div className="overflow-hidden bg-gray-800 rounded-xl aspect-video">
                        <img
                          src={
                            video.thumbnail ||
                            "https://via.placeholder.com/640x360/1a1a1a/666666?text=No+Thumbnail"
                          }
                          alt={video.title}
                          className="object-cover w-full h-full"
                          loading="lazy"
                          onError={(e) => {
                            const target = e.target as HTMLImageElement;
                            target.src =
                              "https://via.placeholder.com/640x360/1a1a1a/666666?text=No+Thumbnail";
                          }}
                        />

                        {/* Play Button Overlay */}
                        {isActive && (
                          <div className="flex absolute inset-0 justify-center items-center opacity-0 transition-all duration-300 group-hover:opacity-100 bg-black/30">
                            <div className="flex justify-center items-center w-16 h-16 rounded-full shadow-lg bg-white/90">
                              <Play
                                className="ml-1 w-8 h-8 text-gray-900"
                                fill="currentColor"
                              />
                            </div>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Video Info */}
                    <div className="space-y-3">
                      <div>
                        <h3 className="mb-2 text-lg font-bold leading-tight text-white line-clamp-2">
                          {video.title}
                        </h3>
                        <div className="flex items-center justify-between">
                          <p className="text-sm font-medium text-purple-200">
                            {video.channel}
                          </p>
                          {/* YouTube Attribution Badge */}
                          <div className="flex items-center space-x-1 text-xs text-gray-400">
                            <svg className="w-3 h-3" viewBox="0 0 24 24" fill="currentColor">
                              <path d="M23.498 6.186a2.998 2.998 0 0 0-2.112-2.112C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.386.529A2.998 2.998 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a2.998 2.998 0 0 0 2.112 2.112c1.881.529 9.386.529 9.386.529s7.505 0 9.386-.529a2.998 2.998 0 0 0 2.112-2.112C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
                            </svg>
                            <span>YouTube</span>
                          </div>
                        </div>

                        {/* View count */}
                        <div className="flex items-center mt-2 space-x-2">
                          <Eye className="w-4 h-4 text-blue-400" />
                          <span className="text-sm text-blue-300">
                            {formatViews(video.views)} views
                          </span>
                        </div>
                      </div>

                      {/* Audio player if available and active */}
                      {isActive && video.audio_url && (
                        <div className="relative z-40 p-3 rounded-lg backdrop-blur-sm bg-white/10">
                          <div className="flex justify-between items-center">
                            <p className="text-sm font-medium text-white">
                              AI Preview
                            </p>

                            <audio
                              controls
                              className="relative z-50 h-8 scale-90"
                              preload="metadata"
                              style={{
                                pointerEvents: "auto",
                                cursor: "pointer",
                              }}
                            >
                              <source src={video.audio_url} type="audio/mpeg" />
                              Your browser does not support the audio element.
                            </audio>
                          </div>
                        </div>
                      )}

                      {/* Watch Button */}
                      {isActive && (
                        <button
                          onClick={() => window.open(video.url, "_blank")}
                          className="flex relative z-40 justify-center items-center px-4 py-2 space-x-2 w-full text-sm font-bold text-white bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg shadow-lg transition-all duration-300 hover:from-purple-600 hover:to-pink-600"
                          style={{ pointerEvents: "auto", cursor: "pointer" }}
                        >
                          <Play className="w-4 h-4" fill="currentColor" />
                          <span>Watch on YouTube</span>
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Progress Indicator */}
        <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2">
          <div className="w-64 h-2 rounded-full bg-white/10">
            <div
              className="h-full bg-purple-400 rounded-full transition-all duration-300"
              style={{
                width: `${(focusedIndex / (videos.length - 1)) * 100}%`,
              }}
            />
          </div>
        </div>
      </div>

      {/* Mobile Version - Simple Card */}
      <div className="md:hidden">
        {videos.length > 0 && (
          <div className="overflow-hidden rounded-2xl border border-gray-700 shadow-lg backdrop-blur-sm bg-gray-900/80">
            {/* Use current mobile index */}
            {(() => {
              const video = videos[mobileCurrentIndex];
              return (
                <>
                  {/* Video Thumbnail */}
                  <div
                    className="relative cursor-pointer"
                    onClick={() => window.open(video.url, "_blank")}
                  >
                    <div className="bg-gray-800 aspect-video">
                      <img
                        src={
                          video.thumbnail ||
                          "https://via.placeholder.com/640x360/1a1a1a/666666?text=No+Thumbnail"
                        }
                        alt={video.title}
                        className="object-cover w-full h-full"
                        loading="lazy"
                        onError={(e) => {
                          const target = e.target as HTMLImageElement;
                          target.src =
                            "https://via.placeholder.com/640x360/1a1a1a/666666?text=No+Thumbnail";
                        }}
                      />

                      {/* Play Button Overlay - Always visible on mobile */}
                      <div className="flex absolute inset-0 justify-center items-center bg-black/20">
                        <div className="flex justify-center items-center w-16 h-16 rounded-full shadow-lg bg-white/90">
                          <Play
                            className="ml-1 w-8 h-8 text-gray-900"
                            fill="currentColor"
                          />
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Video Info */}
                  <div className="p-4 space-y-3">
                    <div>
                      <p className="mb-2 text-xs text-purple-300">
                        🔥{" "}
                        {video.is_video_of_day
                          ? "Video of the Day"
                          : "Featured Video"}{" "}
                        • {getDaysAgoText(video.days_ago)}
                      </p>
                      <h3 className="text-lg font-bold leading-tight text-white line-clamp-2">
                        {video.title}
                      </h3>
                    </div>

                    <div className="flex justify-between items-center text-sm">
                      <p className="font-medium text-gray-300 truncate">
                        {video.channel}
                      </p>
                      <div className="flex items-center space-x-1">
                        <Eye className="w-4 h-4 text-blue-400" />
                        <span className="text-blue-300">
                          {formatViews(video.views)}
                        </span>
                      </div>
                    </div>

                    {/* Audio player for mobile */}
                    {video.audio_url && (
                      <div className="p-3 rounded-lg bg-white/5">
                        <div className="flex justify-between items-center">
                          <p className="text-sm font-medium text-white">
                            AI Preview
                          </p>
                          <audio
                            key={video.video_id} // Force re-render when video changes
                            controls
                            className="h-6 scale-90"
                            preload="metadata"
                          >
                            <source src={video.audio_url} type="audio/mpeg" />
                            Your browser does not support the audio element.
                          </audio>
                        </div>
                      </div>
                    )}
                  </div>
                  
                  {/* Mobile Navigation Controls */}
                  {videos.length > 1 && (
                    <div className="flex justify-between items-center px-4 py-3 border-t border-gray-700">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          goToPrevious();
                        }}
                        className="flex justify-center items-center w-10 h-10 rounded-full transition-colors bg-white/10 hover:bg-white/20"
                        aria-label="Previous video"
                      >
                        <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                        </svg>
                      </button>
                      
                      <div className="flex items-center space-x-2">
                        <span className="text-sm text-gray-400">
                          {mobileCurrentIndex + 1} of {videos.length}
                        </span>
                        {videos[mobileCurrentIndex].is_video_of_day && (
                          <span className="px-2 py-1 text-xs font-medium text-purple-300 bg-purple-900/50 rounded-full">
                            Featured
                          </span>
                        )}
                      </div>
                      
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          goToNext();
                        }}
                        className="flex justify-center items-center w-10 h-10 rounded-full transition-colors bg-white/10 hover:bg-white/20"
                        aria-label="Next video"
                      >
                        <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                        </svg>
                      </button>
                    </div>
                  )}
                </>
              );
            })()}
          </div>
        )}
      </div>
    </div>
  );
}
