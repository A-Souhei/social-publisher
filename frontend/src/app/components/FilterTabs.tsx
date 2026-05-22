import type { Platform, Stats, Status } from "./types";

type StatusFilter = "all" | Status;
type PlatformFilter = "all" | Platform;

interface FilterTabsProps {
  statusFilter: StatusFilter;
  platformFilter: PlatformFilter;
  onStatusChange: (s: StatusFilter) => void;
  onPlatformChange: (p: PlatformFilter) => void;
  stats: Stats;
  totalCount: number;
}

const STATUS_TABS: { value: StatusFilter; label: string }[] = [
  { value: "all", label: "All" },
  { value: "draft", label: "Draft" },
  { value: "scheduled", label: "Scheduled" },
  { value: "published", label: "Published" },
  { value: "failed", label: "Failed" },
];

const PLATFORM_TABS: { value: PlatformFilter; label: string }[] = [
  { value: "all", label: "All Platforms" },
  { value: "linkedin_page", label: "LinkedIn" },
  { value: "facebook_page", label: "Facebook" },
];

export default function FilterTabs({
  statusFilter,
  platformFilter,
  onStatusChange,
  onPlatformChange,
  stats,
  totalCount,
}: FilterTabsProps) {
  const countFor = (s: StatusFilter): number => {
    if (s === "all") return totalCount;
    return stats[s as Status] ?? 0;
  };

  return (
    <div className="flex flex-col gap-3 mb-6">
      {/* Status tabs */}
      <div className="flex flex-wrap gap-2">
        {STATUS_TABS.map(({ value, label }) => (
          <button
            key={value}
            onClick={() => onStatusChange(value)}
            className={`flex items-center gap-2 px-4 py-1.5 rounded-full text-sm font-medium transition-colors ${
              statusFilter === value
                ? "bg-gray-700 text-gray-100"
                : "bg-gray-900 text-gray-400 hover:bg-gray-800 hover:text-gray-300"
            }`}
          >
            {label}
            <span
              className={`text-xs px-1.5 py-0.5 rounded-full ${
                statusFilter === value ? "bg-gray-600" : "bg-gray-800"
              }`}
            >
              {countFor(value)}
            </span>
          </button>
        ))}
      </div>

      {/* Platform filter */}
      <div className="flex flex-wrap gap-2">
        {PLATFORM_TABS.map(({ value, label }) => (
          <button
            key={value}
            onClick={() => onPlatformChange(value)}
            className={`px-3 py-1 rounded-full text-xs font-medium transition-colors border ${
              platformFilter === value
                ? "bg-gray-700 text-gray-100 border-gray-600"
                : "bg-transparent text-gray-500 border-gray-700 hover:border-gray-600 hover:text-gray-400"
            }`}
          >
            {label}
          </button>
        ))}
      </div>
    </div>
  );
}
