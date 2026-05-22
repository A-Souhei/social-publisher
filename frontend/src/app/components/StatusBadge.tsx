import type { Status } from "./types";

const STATUS_STYLES: Record<Status, string> = {
  draft: "bg-slate-500/20 text-slate-400 border border-slate-500/30",
  scheduled: "bg-amber-500/20 text-amber-400 border border-amber-500/30",
  publishing: "bg-blue-500/20 text-blue-400 border border-blue-500/30",
  published: "bg-green-500/20 text-green-400 border border-green-500/30",
  failed: "bg-red-500/20 text-red-400 border border-red-500/30",
};

const STATUS_LABELS: Record<Status, string> = {
  draft: "Draft",
  scheduled: "Scheduled",
  publishing: "Publishing",
  published: "Published",
  failed: "Failed",
};

export default function StatusBadge({ status }: { status: string }) {
  const styles =
    STATUS_STYLES[status as Status] ??
    "bg-gray-500/20 text-gray-400 border border-gray-500/30";
  const label = STATUS_LABELS[status as Status] ?? status;
  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${styles}`}
    >
      {label}
    </span>
  );
}
