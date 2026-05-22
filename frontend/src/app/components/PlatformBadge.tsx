type PlatformKey = "linkedin_profile" | "linkedin_page" | "facebook_page";

const PLATFORM_META: Record<PlatformKey, { label: string; styles: string }> = {
  linkedin_profile: {
    label: "LinkedIn Profile",
    styles: "bg-blue-600/20 text-blue-400 border border-blue-600/30",
  },
  linkedin_page: {
    label: "LinkedIn Page",
    styles: "bg-blue-600/20 text-blue-400 border border-blue-600/30",
  },
  facebook_page: {
    label: "Facebook Page",
    styles: "bg-indigo-600/20 text-indigo-400 border border-indigo-600/30",
  },
};

export default function PlatformBadge({ platform }: { platform: string }) {
  const meta = PLATFORM_META[platform as PlatformKey];
  const label = meta?.label ?? platform;
  const styles =
    meta?.styles ?? "bg-gray-600/20 text-gray-400 border border-gray-600/30";
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${styles}`}
    >
      {label}
    </span>
  );
}
