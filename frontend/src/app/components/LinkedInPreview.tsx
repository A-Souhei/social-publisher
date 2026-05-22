import { parseISO } from "./time";

interface LinkedInPreviewProps {
  text: string;
  imageUrl: string | null;
  scheduledTime: string | null;
  createdAt: string;
}

function relativeTime(iso: string | null): string {
  if (!iso) return "Just now";
  try {
    const d = parseISO(iso);
    const diffMs = Date.now() - d.getTime();
    const diffMin = Math.round(diffMs / 60000);
    if (diffMin < 1) return "Just now";
    if (diffMin < 60) return `${diffMin}m`;
    const diffH = Math.round(diffMin / 60);
    if (diffH < 24) return `${diffH}h`;
    const diffD = Math.round(diffH / 24);
    return `${diffD}d`;
  } catch {
    return "";
  }
}

export default function LinkedInPreview({
  text,
  imageUrl,
  scheduledTime,
  createdAt,
}: LinkedInPreviewProps) {
  const displayTime = relativeTime(scheduledTime ?? createdAt);

  return (
    <div
      className="bg-white rounded-xl shadow-md overflow-hidden"
      style={{
        fontFamily:
          '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif',
      }}
    >
      {/* Header */}
      <div className="flex items-start gap-2.5 px-4 pt-3 pb-2">
        <div
          className="w-12 h-12 rounded-lg flex items-center justify-center text-white font-bold text-base flex-shrink-0"
          style={{ backgroundColor: "#0A66C2" }}
        >
          Y
        </div>
        <div className="min-w-0">
          <p className="text-sm font-semibold text-gray-900 leading-tight">
            Your LinkedIn Page
          </p>
          <p className="text-xs text-gray-500 leading-tight">Company</p>
          <p className="text-xs text-gray-400 mt-0.5">
            {displayTime} · 🌐
          </p>
        </div>
      </div>

      {/* Text */}
      <div className="px-4 pb-3">
        <p className="text-sm text-gray-900 leading-relaxed whitespace-pre-wrap">
          {text}
        </p>
      </div>

      {/* Image */}
      {imageUrl && (
        <div className="w-full bg-gray-100">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={imageUrl}
            alt="Post image"
            className="w-full object-cover max-h-80"
          />
        </div>
      )}

      {/* Divider + footer */}
      <div className="px-4 pt-2 pb-1">
        <div className="border-t border-gray-200 pt-1 flex items-center justify-around text-xs text-gray-500 font-medium">
          <button className="flex items-center gap-1.5 py-1.5 px-2 rounded hover:bg-gray-100 transition-colors">
            <span>👍</span> Like
          </button>
          <button className="flex items-center gap-1.5 py-1.5 px-2 rounded hover:bg-gray-100 transition-colors">
            <span>💬</span> Comment
          </button>
          <button className="flex items-center gap-1.5 py-1.5 px-2 rounded hover:bg-gray-100 transition-colors">
            <span>🔁</span> Repost
          </button>
          <button className="flex items-center gap-1.5 py-1.5 px-2 rounded hover:bg-gray-100 transition-colors">
            <span>✉️</span> Send
          </button>
        </div>
      </div>
    </div>
  );
}
