"use client";

import { useState, useEffect } from "react";
import {
  Play,
  ChevronLeft,
  ChevronRight,
  Clock,
  RefreshCw,
} from "lucide-react";
import { api } from "@/lib/api";
import VideoOfTheDayCarouselMouse from "./VideoOfTheDayCarouselMouse";

interface VideoRanking {
  rank: number;
  title: string;
  channel: string;
  views: string;
  likes: string;
  engagement: string;
  published: string;
  url: string;
  thumbnail: string;
}

interface DirectoryStats {
  total_videos: number;
  total_channels: number;
  categories: Record<string, number>;
  last_updated: string;
}

interface VideoCardProps {
  video: VideoRanking;
  index: number;
  shouldAnimate?: boolean;
  className?: string;
}

function VideoCard({
  video,
  index,
  shouldAnimate = false,
  className = "",
}: VideoCardProps) {
  const formatViews = (views: string) => {
    const num = parseInt(views.replace(/,/g, ""));
    return api.formatViews(num);
  };

  const getDaysAgo = (published: string) => {
    // If the date is in YYYY-MM-DD format, parse it as local date, not UTC
    const [year, month, day] = published.split("T")[0].split("-");
    const publishedDate = new Date(
      parseInt(year),
      parseInt(month) - 1,
      parseInt(day)
    );

    const now = new Date();
    const todayStart = new Date(
      now.getFullYear(),
      now.getMonth(),
      now.getDate()
    );

    const diffTime = todayStart.getTime() - publishedDate.getTime();
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays === 0) return "Today";
    if (diffDays === 1) return "Yesterday";
    if (diffDays <= 7) return `${diffDays}d ago`;
    return `${Math.floor(diffDays / 7)}w ago`;
  };

  return (
    <div
      className={`transition-all duration-300 cursor-pointer group ${className}`}
      style={
        shouldAnimate
          ? {
              animationDelay: `${index * 100}ms`,
              animation: "fadeInUp 0.6s ease-out forwards",
            }
          : {}
      }
    >
      {/* Video Thumbnail - Mobile Optimized */}
      <div className="relative aspect-video rounded-xl overflow-hidden bg-gray-800 mb-3 group-hover:scale-[1.02] transition-transform duration-300 touch-manipulation">
        <img
          src={
            video.thumbnail ||
            "https://via.placeholder.com/480x270/1a1a1a/666666?text=No+Thumbnail"
          }
          alt={video.title}
          className="object-cover w-full h-full"
          loading="lazy"
          decoding="async"
          sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
          onError={(e) => {
            const target = e.target as HTMLImageElement;
            target.src =
              "https://via.placeholder.com/480x270/1a1a1a/666666?text=No+Thumbnail";
          }}
        />

        {/* Play Button Overlay - Responsive sizing */}
        <div className="flex absolute inset-0 justify-center items-center opacity-0 transition-all duration-300 group-hover:opacity-100 md:group-hover:opacity-100 active:opacity-100 bg-black/20">
          <div className="flex justify-center items-center w-12 h-12 rounded-full shadow-lg md:w-16 md:h-16 bg-white/90">
            <Play
              className="ml-1 w-5 h-5 text-gray-900 md:w-7 md:h-7"
              fill="currentColor"
            />
          </div>
        </div>

        {/* Duration Badge - Mobile optimized */}
        <div className="absolute right-2 bottom-2">
          <div className="px-2 py-1 text-xs font-medium text-white rounded backdrop-blur-sm bg-black/70">
            {getDaysAgo(video.published)}
          </div>
        </div>

        {/* External Link */}
        <a
          href={video.url}
          target="_blank"
          rel="noopener noreferrer"
          className="absolute inset-0 z-10"
          aria-label={`Watch ${video.title}`}
        />
      </div>

      {/* Video Info - Below thumbnail like YouTube */}
      <div className="px-1">
        <h3 className="mb-2 text-sm font-semibold leading-tight text-white transition-colors duration-300 md:text-sm line-clamp-2 group-hover:text-blue-300">
          {video.title}
        </h3>

        <p className="mb-1 text-sm text-gray-400 truncate">{video.channel}</p>

        <div className="flex items-center space-x-2 text-xs text-gray-500">
          <span className="truncate">{formatViews(video.views)} views</span>
          <span className="hidden sm:inline">•</span>
          <span className="hidden truncate sm:inline">
            {video.engagement} engagement
          </span>
        </div>
      </div>
    </div>
  );
}

interface CategorySectionProps {
  title: string;
  videos: VideoRanking[];
  onNext: () => void;
  onPrevious: () => void;
  onReset: () => void;
  canGoPrevious: boolean;
  isLoading?: boolean;
  currentPage?: number;
  sectionKey: string;
  refreshAnimating: string | null;
  hasNavigated: boolean;
}

function CategorySection({
  title,
  videos,
  onNext,
  onPrevious,
  onReset,
  canGoPrevious,
  isLoading = false,
  currentPage = 0,
  sectionKey,
  refreshAnimating,
  hasNavigated,
}: CategorySectionProps) {
  return (
    <div className="mb-16">
      {/* Section Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-white md:text-2xl">
            {title}
          </h2>
        </div>

        {/* Mobile Navigation Controls - Larger touch targets */}
        <div className="flex items-center space-x-1 md:space-x-2">
          <button
            onClick={onPrevious}
            disabled={!canGoPrevious || isLoading}
            className={`min-w-[44px] min-h-[44px] p-3 md:p-2 bg-white/10 hover:bg-white/20 rounded-lg transition-all duration-300 backdrop-blur-sm touch-manipulation ${
              !canGoPrevious
                ? "opacity-50 cursor-not-allowed"
                : "hover:scale-110 active:scale-95"
            }`}
            title="Previous videos"
            aria-label="Show previous videos"
          >
            <ChevronLeft className="w-5 h-5 text-white md:w-5 md:h-5" />
          </button>

          <span className="px-1 text-xs text-white/60 md:text-sm md:px-2">
            {currentPage + 1}
          </span>

          <button
            onClick={onNext}
            disabled={isLoading}
            className={`p-3 rounded-lg backdrop-blur-sm transition-all duration-300 min-w-[44px] min-h-[44px] md:p-2 bg-white/10 hover:bg-white/20 hover:scale-110 active:scale-95 touch-manipulation`}
            title="Next videos"
            aria-label="Show next videos"
          >
            <ChevronRight className="w-5 h-5 text-white md:w-5 md:h-5" />
          </button>

          <button
            onClick={onReset}
            disabled={currentPage === 0 || refreshAnimating === sectionKey}
            className={`min-w-[44px] min-h-[44px] p-3 md:p-2 bg-white/10 hover:bg-white/20 rounded-lg transition-all duration-300 backdrop-blur-sm touch-manipulation ${
              currentPage === 0 || refreshAnimating === sectionKey
                ? "opacity-50 cursor-not-allowed"
                : "hover:scale-110 active:scale-95"
            }`}
            title="Return to first page"
            aria-label="Return to first page of videos"
          >
            <RefreshCw
              className={`w-4 h-4 md:w-4 md:h-4 text-white ${
                refreshAnimating === sectionKey ? "refresh-spinning" : ""
              }`}
            />
          </button>
        </div>
      </div>

      {/* Video Grid - Mobile: 1 video, Desktop: 3 videos */}
      <div className="grid gap-6 grid-cols-1 lg:grid-cols-3">
        {videos.length > 0 ? (
          videos.map((video, index) => (
            <VideoCard
              key={`${title}-${video.url}-${index}`}
              video={video}
              index={index}
              shouldAnimate={hasNavigated}
              className={index >= 1 ? "hidden lg:block" : ""}
            />
          ))
        ) : (
          <div className="col-span-full py-8 text-center">
            <p className="text-gray-400">No videos available</p>
          </div>
        )}
      </div>

      {/* Info */}
      <div className="mt-2 text-xs text-gray-500">
        {videos.length} videos displayed {isLoading && "(loading...)"}
      </div>
    </div>
  );
}

interface HomePageProps {
  initialCuratedVideos: VideoRanking[];
  initialInstructionalVideos: VideoRanking[];
  initialDiscoveryVideos: VideoRanking[];
  initialStats: DirectoryStats;
  initialVideosWithAudio: any[];
  initialVideoOfTheDay: any;
}

export default function HomePage({
  initialCuratedVideos,
  initialInstructionalVideos,
  initialDiscoveryVideos,
  initialStats,
  initialVideosWithAudio,
  initialVideoOfTheDay,
}: HomePageProps) {
  const [curatedVideos, setCuratedVideos] = useState<VideoRanking[]>(
    initialCuratedVideos.slice(0, 3)
  );
  const [instructionalVideos, setInstructionalVideos] = useState<VideoRanking[]>(
    initialInstructionalVideos.slice(0, 3)
  );
  const [discoveryVideos, setDiscoveryVideos] = useState<VideoRanking[]>(
    initialDiscoveryVideos.slice(0, 3)
  );
  const [refreshingSection, setRefreshingSection] = useState<string | null>(
    null
  );
  const [curatedOffset, setCuratedOffset] = useState(0);
  const [instructionalOffset, setInstructionalOffset] = useState(0);
  const [discoveryOffset, setDiscoveryOffset] = useState(0);
  const [refreshAnimating, setRefreshAnimating] = useState<string | null>(null);
  const [hasNavigated, setHasNavigated] = useState(false);

  const navigateSection = async (
    section: string,
    direction: "next" | "previous" | "reset"
  ) => {
    try {
      console.log(`🔄 Refreshing ${section} section...`);
      setRefreshingSection(section);
      setHasNavigated(true);

      if (section === "curated") {
        let targetOffset = curatedOffset;

        if (direction === "next") {
          targetOffset = curatedOffset + 3;
        } else if (direction === "previous" && curatedOffset >= 3) {
          targetOffset = curatedOffset - 3;
        } else if (direction === "reset") {
          targetOffset = 0;
          setRefreshAnimating(section);
          setTimeout(() => setRefreshAnimating(null), 800);
        }

        // For now, just cycle through the initial data
        // In a full implementation, you'd need API endpoints or more sophisticated SSR
        const allVideos = initialCuratedVideos;
        const newVideos = allVideos.slice(targetOffset, targetOffset + 3);

        if (newVideos.length > 0) {
          setCuratedVideos(newVideos);
          setCuratedOffset(targetOffset);
        } else if (direction === "next" && targetOffset > 0) {
          // Loop back to beginning
          setCuratedVideos(allVideos.slice(0, 3));
          setCuratedOffset(0);
        }
      } else if (section === "instructional") {
        let targetOffset = instructionalOffset;

        if (direction === "next") {
          targetOffset = instructionalOffset + 3;
        } else if (direction === "previous" && instructionalOffset >= 3) {
          targetOffset = instructionalOffset - 3;
        } else if (direction === "reset") {
          targetOffset = 0;
          setRefreshAnimating(section);
          setTimeout(() => setRefreshAnimating(null), 800);
        }

        const allVideos = initialInstructionalVideos;
        const newVideos = allVideos.slice(targetOffset, targetOffset + 3);

        if (newVideos.length > 0) {
          setInstructionalVideos(newVideos);
          setInstructionalOffset(targetOffset);
        } else if (direction === "next" && targetOffset > 0) {
          // Loop back to beginning
          setInstructionalVideos(allVideos.slice(0, 3));
          setInstructionalOffset(0);
        }
      } else if (section === "discovery") {
        let targetOffset = discoveryOffset;

        if (direction === "next") {
          targetOffset = discoveryOffset + 3;
        } else if (direction === "previous" && discoveryOffset >= 3) {
          targetOffset = discoveryOffset - 3;
        } else if (direction === "reset") {
          targetOffset = 0;
          setRefreshAnimating(section);
          setTimeout(() => setRefreshAnimating(null), 800);
        }

        const allVideos = initialDiscoveryVideos;
        const newVideos = allVideos.slice(targetOffset, targetOffset + 3);

        if (newVideos.length > 0) {
          setDiscoveryVideos(newVideos);
          setDiscoveryOffset(targetOffset);
        } else if (direction === "next" && targetOffset > 0) {
          // Loop back to beginning
          setDiscoveryVideos(allVideos.slice(0, 3));
          setDiscoveryOffset(0);
        }
      }
    } catch (err) {
      console.error(`❌ Error refreshing ${section}:`, err);
    } finally {
      console.log(`✅ Finished refreshing ${section}`);
      setRefreshingSection(null);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-black to-gray-900">
      {/* Stats Bar - Mobile Optimized */}
      {initialStats && (
        <div className="border-b backdrop-blur-sm border-white/10 bg-black/30">
          <div className="px-4 py-3 mx-auto max-w-7xl md:px-6 md:py-4">
            <div className="flex justify-between items-center text-sm text-white md:text-base">
              <div className="flex flex-1 items-center space-x-4 md:space-x-8">
                <div className="flex items-center space-x-1 md:space-x-2">
                  <Play className="w-3 h-3 text-blue-400 md:w-4 md:h-4" />
                  <span className="text-xs font-bold md:text-base">
                    {initialStats.total_videos.toLocaleString()}
                  </span>
                  <span className="hidden text-xs text-gray-400 md:text-base sm:inline">
                    videos
                  </span>
                </div>
                <div className="flex items-center space-x-1 md:space-x-2">
                  <Clock className="w-3 h-3 text-green-400 md:w-4 md:h-4" />
                  <span className="text-xs font-bold md:text-base">
                    {initialStats.total_channels.toLocaleString()}
                  </span>
                  <span className="hidden text-xs text-gray-400 md:text-base sm:inline">
                    channels
                  </span>
                </div>
                <div className="hidden items-center space-x-2 md:flex">
                  <span className="text-gray-400">Updated</span>
                  <span className="font-bold">
                    {new Date(initialStats.last_updated).toLocaleTimeString()}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className="px-4 py-8 mx-auto max-w-7xl md:px-6 md:py-12">
        {/* Video of the Day */}
        <VideoOfTheDayCarouselMouse
          initialVideosWithAudio={initialVideosWithAudio}
          initialVideoOfTheDay={initialVideoOfTheDay}
        />

        {/* Curated Content from Whitelisted Creators */}
        <CategorySection
          title="Recently Uploaded"
          videos={curatedVideos}
          onNext={() => navigateSection("curated", "next")}
          onPrevious={() => navigateSection("curated", "previous")}
          onReset={() => navigateSection("curated", "reset")}
          canGoPrevious={curatedOffset > 0}
          isLoading={refreshingSection === "curated"}
          currentPage={Math.floor(curatedOffset / 3)}
          sectionKey="curated"
          refreshAnimating={refreshAnimating}
          hasNavigated={hasNavigated}
        />

        {/* Instructional Content */}
        <CategorySection
          title="Instructional Videos"
          videos={instructionalVideos}
          onNext={() => navigateSection("instructional", "next")}
          onPrevious={() => navigateSection("instructional", "previous")}
          onReset={() => navigateSection("instructional", "reset")}
          canGoPrevious={instructionalOffset > 0}
          isLoading={refreshingSection === "instructional"}
          currentPage={Math.floor(instructionalOffset / 3)}
          sectionKey="instructional"
          refreshAnimating={refreshAnimating}
          hasNavigated={hasNavigated}
        />

        {/* Discovery Content */}
        <CategorySection
          title="title like '%golf%'"
          videos={discoveryVideos}
          onNext={() => navigateSection("discovery", "next")}
          onPrevious={() => navigateSection("discovery", "previous")}
          onReset={() => navigateSection("discovery", "reset")}
          canGoPrevious={discoveryOffset > 0}
          isLoading={refreshingSection === "discovery"}
          currentPage={Math.floor(discoveryOffset / 3)}
          sectionKey="discovery"
          refreshAnimating={refreshAnimating}
          hasNavigated={hasNavigated}
        />
      </div>

      {/* CSS for animations */}
      <style jsx>{`
        @keyframes fadeInUp {
          from {
            opacity: 0;
            transform: translateY(30px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        @keyframes spin {
          from {
            transform: rotate(0deg);
          }
          to {
            transform: rotate(360deg);
          }
        }

        .refresh-spinning {
          animation: spin 0.8s ease-in-out;
        }

        .line-clamp-2 {
          display: -webkit-box;
          -webkit-line-clamp: 2;
          -webkit-box-orient: vertical;
          overflow: hidden;
        }
      `}</style>
    </div>
  );
}
