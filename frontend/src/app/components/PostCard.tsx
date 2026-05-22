import { Camera, Trash2 } from "lucide-react";
import PlatformBadge from "./PlatformBadge";
import StatusBadge from "./StatusBadge";

export interface Post {
  id: string;
  text: string;
  text_preview: string;
  targets: string[];
  image_path: string | null;
  has_image: boolean;
  scheduled_time: string;
  status: string;
  created_at: string;
  error: string | null;
}

function formatUtc(iso: string): string {
  try {
    return new Date(iso.endsWith("Z") ? iso : iso + "Z").toLocaleString(
      undefined,
      {
        year: "numeric",
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      }
    );
  } catch {
    return iso;
  }
}

interface PostCardProps {
  post: Post;
  onCancel: (id: string) => void;
}

export default function PostCard({ post, onCancel }: PostCardProps) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 flex flex-col gap-3">
      <div className="flex items-start justify-between gap-2">
        <div className="flex flex-wrap gap-1.5">
          {post.targets.map((t) => (
            <PlatformBadge key={t} platform={t} />
          ))}
        </div>
        <StatusBadge status={post.status} />
      </div>

      <p className="text-sm text-gray-300 leading-relaxed line-clamp-3">
        {post.text_preview}
      </p>

      {post.has_image && (
        <div className="flex items-center gap-1.5 text-xs text-gray-500">
          <Camera className="w-3.5 h-3.5" />
          <span>Has image</span>
        </div>
      )}

      {post.status === "failed" && post.error && (
        <div className="bg-red-950/50 border border-red-800/40 rounded-lg px-3 py-2">
          <p className="text-xs text-red-400 font-medium">Error</p>
          <p className="text-xs text-red-300 mt-0.5">{post.error}</p>
        </div>
      )}

      <div className="mt-auto pt-2 border-t border-gray-800 flex items-end justify-between gap-2">
        <div>
          <p className="text-xs text-gray-400">
            Scheduled:{" "}
            <span className="text-gray-300">
              {formatUtc(post.scheduled_time)}
            </span>
          </p>
          <p className="text-xs text-gray-600 mt-0.5">
            Created: {formatUtc(post.created_at)}
          </p>
        </div>

        {post.status === "pending" && (
          <button
            onClick={() => onCancel(post.id)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-red-950/60 text-red-400 border border-red-800/40 hover:bg-red-900/60 hover:border-red-700/50 transition-colors"
          >
            <Trash2 className="w-3.5 h-3.5" />
            Cancel
          </button>
        )}
      </div>
    </div>
  );
}
