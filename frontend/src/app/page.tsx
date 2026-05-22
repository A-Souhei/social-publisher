"use client";

import { useCallback, useEffect, useState } from "react";
import Image from "next/image";
import FilterTabs from "./components/FilterTabs";
import PostCard from "./components/PostCard";
import StatsBar from "./components/StatsBar";
import ThemeToggle from "./components/ThemeToggle";
import type { Platform, Post, Stats, Status } from "./components/types";

type StatusFilter = "all" | Status;
type PlatformFilter = "all" | Platform;

const EMPTY_STATS: Stats = {
  draft: 0,
  scheduled: 0,
  publishing: 0,
  published: 0,
  failed: 0,
  total: 0,
};

export default function DashboardPage() {
  const [posts, setPosts] = useState<Post[]>([]);
  const [stats, setStats] = useState<Stats>(EMPTY_STATS);
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [platformFilter, setPlatformFilter] = useState<PlatformFilter>("all");
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    try {
      const [postsRes, statsRes] = await Promise.all([
        fetch("/api/posts"),
        fetch("/api/stats"),
      ]);
      if (postsRes.ok) {
        const data = await postsRes.json();
        setPosts(data.posts ?? data);
      }
      if (statsRes.ok) {
        setStats(await statsRes.json());
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30_000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const filteredPosts = posts.filter((p) => {
    if (statusFilter !== "all" && p.status !== statusFilter) return false;
    if (platformFilter !== "all" && !p.platforms.includes(platformFilter)) return false;
    return true;
  });

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      {/* Header */}
      <div className="border-b border-gray-200 bg-gray-50/80 dark:border-gray-800 dark:bg-gray-950/80 backdrop-blur sticky top-0 z-10">
        <div className="max-w-2xl mx-auto px-4 py-4 flex items-center justify-between gap-3">
          <div className="flex items-center gap-3 min-w-0">
            <Image
              src="/logo.svg"
              alt="Social Publisher logo"
              width={36}
              height={36}
              className="rounded-[10px] shadow-sm flex-shrink-0"
              priority
            />
            <div className="min-w-0">
              <h1 className="text-xl font-bold text-slate-900 dark:text-gray-100 tracking-tight leading-tight">
                Social Publisher
              </h1>
              <p className="text-xs text-slate-500 dark:text-gray-500 mt-0.5">
                Read-only dashboard · auto-refreshes every 30s
              </p>
            </div>
          </div>
          <ThemeToggle />
        </div>
      </div>

      <div className="max-w-2xl mx-auto px-4 py-8">
        <StatsBar stats={stats} />

        <FilterTabs
          statusFilter={statusFilter}
          platformFilter={platformFilter}
          onStatusChange={setStatusFilter}
          onPlatformChange={setPlatformFilter}
          stats={stats}
          totalCount={posts.length}
        />

        {loading ? (
          <div className="flex flex-col gap-6">
            {Array.from({ length: 3 }).map((_, i) => (
              <div
                key={i}
                className="bg-white border border-gray-200 dark:bg-gray-900 dark:border-gray-800 rounded-xl h-64 animate-pulse"
              />
            ))}
          </div>
        ) : filteredPosts.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-24 text-slate-400 dark:text-gray-600">
            <p className="text-lg font-medium">No posts found</p>
            <p className="text-sm mt-1">
              {statusFilter === "all" && platformFilter === "all"
                ? "Ask Hermes to create a post to get started"
                : "Try adjusting your filters"}
            </p>
          </div>
        ) : (
          <div className="flex flex-col gap-6">
            {filteredPosts.map((post) => (
              <PostCard key={post.id} post={post} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
