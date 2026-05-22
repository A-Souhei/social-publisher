type Status = "pending" | "publishing" | "published" | "failed" | "cancelled";

const STATUS_STYLES: Record<Status, string> = {
  pending:
    "bg-amber-500/20 text-amber-400 border border-amber-500/30",
  publishing:
    "bg-blue-500/20 text-blue-400 border border-blue-500/30",
  published:
    "bg-green-500/20 text-green-400 border border-green-500/30",
  failed:
    "bg-red-500/20 text-red-400 border border-red-500/30",
  cancelled:
    "bg-gray-500/20 text-gray-400 border border-gray-500/30",
};

export default function StatusBadge({ status }: { status: string }) {
  const styles =
    STATUS_STYLES[status as Status] ??
    "bg-gray-500/20 text-gray-400 border border-gray-500/30";
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${styles}`}>
      {status}
    </span>
  );
}
