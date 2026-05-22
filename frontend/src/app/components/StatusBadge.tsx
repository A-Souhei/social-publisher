import type { Status } from "./types";

const STATUS_STYLES: Record<Status, string> = {
  draft:
    "bg-slate-100 text-slate-600 border border-slate-300 dark:bg-slate-500/20 dark:text-slate-400 dark:border-slate-500/30",
  scheduled:
    "bg-amber-100 text-amber-700 border border-amber-300 dark:bg-amber-500/20 dark:text-amber-400 dark:border-amber-500/30",
  publishing:
    "bg-blue-100 text-blue-700 border border-blue-300 dark:bg-blue-500/20 dark:text-blue-400 dark:border-blue-500/30",
  published:
    "bg-green-100 text-green-700 border border-green-300 dark:bg-green-500/20 dark:text-green-400 dark:border-green-500/30",
  failed:
    "bg-red-100 text-red-700 border border-red-300 dark:bg-red-500/20 dark:text-red-400 dark:border-red-500/30",
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
    "bg-gray-100 text-gray-600 border border-gray-300 dark:bg-gray-500/20 dark:text-gray-400 dark:border-gray-500/30";
  const label = STATUS_LABELS[status as Status] ?? status;
  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${styles}`}
    >
      {label}
    </span>
  );
}
