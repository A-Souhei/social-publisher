"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import PostCard, { Post } from "./components/PostCard";
import StatsBar from "./components/StatsBar";
import StatusBadge from "./components/StatusBadge";

type StatusFilter =
  | "all"
  | "pending"
  | "publishing"
  | "published"
  | "failed"
  | "cancelled";

interface Stats {
  pending: number;
  publishing: number;
  published: number;
  failed: number;
  cancelled: number;
}

const FILTER_TABS: StatusFilter[] = [
  "all",
  "pending",
  "publishing",
  "published",
  "failed",
  "cancelled",
];

interface Toast {
  id: number;
  message: string;
}

export default function DashboardPage() {
  const [posts, setPosts] = useState<Post[]>([]);
  const [stats, setStats] = useState<Stats>({
    pending: 0,
    publishing: 0,
    published: 0,
    failed: 0,
    cancelled: 0,
  });
  const [filter, setFilter] = useState<StatusFilter>("all");
  const [loading, setLoading] = useState(true);
  const [toasts, setToasts] = useState<Toast[]>([]);
  const toastCounter = useRef(0);

  const showToast = useCallback((message: string) => {
    const id = ++toastCounter.current;
    setToasts((prev) => [...prev, { id, message }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 3000);
  }, []);

  const fetchData = useCallback(async () => {
    try {
      const [postsRes, statsRes] = await Promise.all([
        fetch("/api/posts"),
        fetch("/api/stats"),
      ]);
      if (postsRes.ok) setPosts(await postsRes.json());
      if (statsRes.ok) setStats(await statsRes.json());
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30_000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const handleCancel = useCallback(
    async (id: string) => {
      setPosts((prev) => prev.filter((p) => p.id !== id));
      setStats((prev) => ({
        ...prev,
        pending: Math.max(0, prev.pending - 1),
        cancelled: prev.cancelled + 1,
      }));
      showToast("Post cancelled");
      try {
        await fetch(`/api/posts/${id}`, { method: "DELETE" });
      } catch {
        fetchData();
      }
    },
    [showToast, fetchData]
  );

  const filteredPosts =
    filter === "all" ? posts : posts.filter((p) => p.status === filter);

  const countFor = (s: StatusFilter): number => {
    if (s === "all") return posts.length;
    return stats[s as keyof Stats] ?? 0;
  };

  return (
    <div className="min-h-screen bg-gray-950">
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-100">
            Scheduled Posts
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Auto-refreshes every 30 seconds
          </p>
        </div>

        <StatsBar stats={stats} />

        <div className="flex flex-wrap gap-2 mb-6">
          {FILTER_TABS.map((tab) => (
            <button
              key={tab}
              onClick={() => setFilter(tab)}
              className={`flex items-center gap-2 px-4 py-1.5 rounded-full text-sm font-medium transition-colors ${
                filter === tab
                  ? "bg-gray-700 text-gray-100"
                  : "bg-gray-900 text-gray-400 hover:bg-gray-800 hover:text-gray-300"
              }`}
            >
              {tab === "all" ? "All" : <StatusBadge status={tab} />}
              <span
                className={`text-xs px-1.5 py-0.5 rounded-full ${
                  filter === tab ? "bg-gray-600" : "bg-gray-800"
                }`}
              >
                {countFor(tab)}
              </span>
            </button>
          ))}
        </div>

        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {Array.from({ length: 6 }).map((_, i) => (
              <div
                key={i}
                className="bg-gray-900 border border-gray-800 rounded-xl p-5 h-48 animate-pulse"
              />
            ))}
          </div>
        ) : filteredPosts.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-24 text-gray-600">
            <p className="text-lg font-medium">No posts found</p>
            <p className="text-sm mt-1">
              {filter === "all"
                ? "No scheduled posts yet"
                : `No posts with status "${filter}"`}
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {filteredPosts.map((post) => (
              <PostCard key={post.id} post={post} onCancel={handleCancel} />
            ))}
          </div>
        )}
      </div>

      <div className="fixed bottom-6 right-6 flex flex-col gap-2 z-50">
        {toasts.map((toast) => (
          <div
            key={toast.id}
            className="bg-gray-800 border border-gray-700 text-gray-200 text-sm px-4 py-2.5 rounded-lg shadow-lg"
          >
            {toast.message}
          </div>
        ))}
      </div>
    </div>
  );
}
