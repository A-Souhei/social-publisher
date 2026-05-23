export type Platform = "linkedin_page" | "facebook_page";
export type Status = "draft" | "scheduled" | "publishing" | "published" | "failed";

export interface Post {
  id: string;
  text: string;
  text_preview: string;
  platforms: Platform[];
  image_path: string | null;
  has_image: boolean;
  image_url: string | null;
  scheduled_time: string | null;
  status: Status;
  created_at: string;
  updated_at: string | null;
  published_at: string | null;
  error: string | null;
  fb_page: string | null;
}

export interface Stats {
  draft: number;
  scheduled: number;
  publishing: number;
  published: number;
  failed: number;
  total: number;
}
