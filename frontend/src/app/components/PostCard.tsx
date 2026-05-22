"use client";

import { ChevronDown, ChevronUp, Copy, ExternalLink } from "lucide-react";
import { useState } from "react";
import FacebookPreview from "./FacebookPreview";
import LinkedInPreview from "./LinkedInPreview";
import StatusBadge from "./StatusBadge";
import { parseISO } from "./time";
import type { Platform, Post } from "./types";

function formatUtc(iso: string | null | undefined): string {
  if (!iso) return "—";
  try {
    const d = parseISO(iso);
    return d.toLocaleString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

function relativeLabel(iso: string | null | undefined): string {
  if (!iso) return "";
  try {
    const d = parseISO(iso);
    const diffMs = d.getTime() - Date.now();
    const absSec = Math.abs(diffMs) / 1000;
    const future = diffMs > 0;
    if (absSec < 60) return future ? "in a moment" : "just now";
    const min = Math.round(absSec / 60);
    if (min < 60) return future ? `in ${min}m` : `${min}m ago`;
    const h = Math.round(min / 60);
    if (h < 24) return future ? `in ${h}h` : `${h}h ago`;
    const d2 = Math.round(h / 24);
    return future ? `in ${d2}d` : `${d2}d ago`;
  } catch {
    return "";
  }
}

const PLATFORM_LABELS: Record<Platform, string> = {
  linkedin_page: "LinkedIn",
  facebook_page: "Facebook",
};

interface PostCardProps {
  post: Post;
}

export default function PostCard({ post }: PostCardProps) {
  const [copied, setCopied] = useState(false);
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [activePlatform, setActivePlatform] = useState<Platform>(
    post.platforms[0] ?? "linkedin_page"
  );
  const [idCopied, setIdCopied] = useState(false);

  const copyToClipboard = async (value: string): Promise<boolean> => {
    try {
      if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(value);
        return true;
      }
    } catch {
      // fall through to legacy fallback (e.g. insecure context / denied permission)
    }
    try {
      const ta = document.createElement("textarea");
      ta.value = value;
      ta.style.position = "fixed";
      ta.style.opacity = "0";
      document.body.appendChild(ta);
      ta.select();
      const ok = document.execCommand("copy");
      document.body.removeChild(ta);
      return ok;
    } catch {
      return false;
    }
  };

  const handleCopy = async () => {
    if (await copyToClipboard(post.text)) {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleCopyId = async () => {
    if (await copyToClipboard(post.id)) {
      setIdCopied(true);
      setTimeout(() => setIdCopied(false), 1500);
    }
  };

  const multiPlatform = post.platforms.length > 1;

  return (
    <div className="rounded-xl overflow-hidden shadow-lg">
      {/* Toolbar */}
      <div className="bg-white border border-gray-200 dark:bg-gray-900 dark:border-gray-800 rounded-t-xl px-4 py-2.5 flex items-center justify-between gap-3 flex-wrap">
        <div className="flex items-center gap-2 flex-wrap">
          {/* Platform toggle if multi-platform */}
          {multiPlatform ? (
            <div className="flex rounded-lg overflow-hidden border border-gray-300 dark:border-gray-700 text-xs font-medium">
              {post.platforms.map((p) => (
                <button
                  key={p}
                  onClick={() => setActivePlatform(p)}
                  className={`px-2.5 py-1 transition-colors ${
                    activePlatform === p
                      ? "bg-slate-800 text-white dark:bg-gray-700 dark:text-gray-100"
                      : "bg-white text-slate-500 hover:bg-gray-100 dark:bg-gray-900 dark:text-gray-400 dark:hover:bg-gray-800"
                  }`}
                >
                  {PLATFORM_LABELS[p] ?? p}
                </button>
              ))}
            </div>
          ) : (
            <span className="text-xs font-medium text-slate-600 bg-gray-100 dark:text-gray-400 dark:bg-gray-800 px-2.5 py-1 rounded-lg">
              {PLATFORM_LABELS[post.platforms[0]] ?? post.platforms[0] ?? "—"}
            </span>
          )}
          <StatusBadge status={post.status} />
        </div>

        <div className="flex items-center gap-2">
          {post.image_url && (
            <a
              href={post.image_url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1 text-xs text-slate-500 hover:text-slate-800 dark:text-gray-400 dark:hover:text-gray-200 transition-colors"
            >
              <ExternalLink className="w-3.5 h-3.5" />
              Image
            </a>
          )}
          <button
            onClick={handleCopy}
            className="flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-lg bg-gray-100 text-slate-700 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700 dark:hover:text-gray-100 transition-colors"
          >
            <Copy className="w-3.5 h-3.5" />
            {copied ? "Copied!" : "Copy text"}
          </button>
        </div>
      </div>

      {/* Platform preview */}
      <div className="border-x border-gray-200 bg-gray-100 dark:border-gray-800 dark:bg-gray-950 p-3">
        {activePlatform === "facebook_page" ? (
          <FacebookPreview
            text={post.text}
            imageUrl={post.image_url}
            scheduledTime={post.scheduled_time}
            createdAt={post.created_at}
          />
        ) : (
          <LinkedInPreview
            text={post.text}
            imageUrl={post.image_url}
            scheduledTime={post.scheduled_time}
            createdAt={post.created_at}
          />
        )}
      </div>

      {/* Error */}
      {post.status === "failed" && post.error && (
        <div className="border-x border-gray-200 bg-red-50 dark:border-gray-800 dark:bg-red-950/40 px-4 py-2.5">
          <p className="text-xs font-medium text-red-600 dark:text-red-400">Error</p>
          <p className="text-xs text-red-500 dark:text-red-300 mt-0.5">{post.error}</p>
        </div>
      )}

      {/* Details toggle */}
      <div className="bg-white border border-t-0 border-gray-200 dark:bg-gray-900 dark:border-gray-800 rounded-b-xl">
        <button
          onClick={() => setDetailsOpen((v) => !v)}
          className="w-full flex items-center justify-between px-4 py-2.5 text-xs text-slate-500 hover:text-slate-800 dark:text-gray-500 dark:hover:text-gray-300 transition-colors"
        >
          <span className="font-medium">Details</span>
          {detailsOpen ? (
            <ChevronUp className="w-4 h-4" />
          ) : (
            <ChevronDown className="w-4 h-4" />
          )}
        </button>

        {detailsOpen && (
          <div className="px-4 pb-4 border-t border-gray-200 dark:border-gray-800 pt-3 grid grid-cols-[auto_1fr] gap-x-4 gap-y-1.5 text-xs">
            {/* ID */}
            <span className="text-slate-400 dark:text-gray-500 self-center">ID</span>
            <button
              onClick={handleCopyId}
              className="font-mono text-slate-700 dark:text-gray-300 text-left truncate hover:text-slate-900 dark:hover:text-gray-100 transition-colors"
              title="Click to copy"
            >
              {idCopied ? "Copied!" : post.id}
            </button>

            <span className="text-slate-400 dark:text-gray-500">Status</span>
            <span className="text-slate-700 dark:text-gray-300">{post.status}</span>

            <span className="text-slate-400 dark:text-gray-500">Platforms</span>
            <span className="text-slate-700 dark:text-gray-300">{post.platforms.join(", ") || "—"}</span>

            {post.scheduled_time && (
              <>
                <span className="text-slate-400 dark:text-gray-500">Scheduled</span>
                <span className="text-slate-700 dark:text-gray-300">
                  {formatUtc(post.scheduled_time)}{" "}
                  <span className="text-slate-400 dark:text-gray-500">
                    ({relativeLabel(post.scheduled_time)})
                  </span>
                </span>
              </>
            )}

            <span className="text-slate-400 dark:text-gray-500">Created</span>
            <span className="text-slate-700 dark:text-gray-300">{formatUtc(post.created_at)}</span>

            {post.updated_at && (
              <>
                <span className="text-slate-400 dark:text-gray-500">Updated</span>
                <span className="text-slate-700 dark:text-gray-300">{formatUtc(post.updated_at)}</span>
              </>
            )}

            {post.published_at && (
              <>
                <span className="text-slate-400 dark:text-gray-500">Published</span>
                <span className="text-slate-700 dark:text-gray-300">{formatUtc(post.published_at)}</span>
              </>
            )}

            {post.image_path && (
              <>
                <span className="text-slate-400 dark:text-gray-500">Image path</span>
                <span className="font-mono text-slate-500 dark:text-gray-400 break-all">
                  {post.image_path}
                </span>
              </>
            )}

            {post.error && (
              <>
                <span className="text-slate-400 dark:text-gray-500">Error</span>
                <span className="text-red-500 dark:text-red-400 break-words">{post.error}</span>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
