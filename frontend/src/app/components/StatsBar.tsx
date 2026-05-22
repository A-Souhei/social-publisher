import { CheckCircle2, Clock, FileText, XCircle } from "lucide-react";
import type { Stats } from "./types";

const STAT_CARDS = [
  {
    key: "draft" as const,
    label: "Draft",
    icon: FileText,
    iconClass: "text-slate-400",
    cardClass: "border-slate-500/20",
  },
  {
    key: "scheduled" as const,
    label: "Scheduled",
    icon: Clock,
    iconClass: "text-amber-400",
    cardClass: "border-amber-500/20",
  },
  {
    key: "published" as const,
    label: "Published",
    icon: CheckCircle2,
    iconClass: "text-green-400",
    cardClass: "border-green-500/20",
  },
  {
    key: "failed" as const,
    label: "Failed",
    icon: XCircle,
    iconClass: "text-red-400",
    cardClass: "border-red-500/20",
  },
];

export default function StatsBar({ stats }: { stats: Stats }) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
      {STAT_CARDS.map(({ key, label, icon: Icon, iconClass, cardClass }) => (
        <div
          key={key}
          className={`bg-gray-900 border ${cardClass} rounded-xl p-4 flex items-center gap-3`}
        >
          <Icon className={`w-6 h-6 flex-shrink-0 ${iconClass}`} />
          <div>
            <p className="text-2xl font-bold text-gray-100">{stats[key]}</p>
            <p className="text-xs text-gray-500 mt-0.5">{label}</p>
          </div>
        </div>
      ))}
    </div>
  );
}
