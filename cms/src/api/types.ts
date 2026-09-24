export type Role = "editor" | "admin";

export interface Show {
  id: number;
  slug: string;
  title: string;
  section: string | null;
  synopsis: string;
  categories: string[];
}

export interface ShowListItem extends Show {
  episode_count: number;
  published_episode_count: number;
}

export interface Episode {
  id: number;
  episode_id: string;
  show_id: number;
  season_number: number;
  episode_number: number;
  episode_title: string;
  duration_seconds: number | null;
  language: string;
  content_group: string;
  status: "draft" | "published";
}

export interface ArtworkItem {
  id: number;
  kind: "poster" | "banner" | "thumbnail";
  width: number;
  height: number;
  size_bytes: number;
  url: string;
}

export interface Paginated<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface ValidationIssue {
  code: string;
  message: string;
  episode_ids: string[];
  show_slug: string | null;
}

export interface ValidationReport {
  blocking: boolean;
  published_episode_count: number;
  published_show_count: number;
  issues: ValidationIssue[];
  informational: ValidationIssue[];
}

export interface PublishResult {
  outcome: "success" | "failed";
  reason?: string;
  publish_run_id?: number;
  shows_count?: number;
  episodes_count?: number;
  started_at?: string;
  finished_at?: string;
  issues?: { code: string; message: string }[];
}

export interface PublishRun {
  id: number;
  triggered_by: string;
  outcome: string;
  shows_count: number;
  episodes_count: number;
  started_at: string | null;
  finished_at: string | null;
  error: string | null;
}

export interface ArtworkSpec {
  aspect: string;
  target_px: [number, number];
  max_kb: number;
}

export interface ReferenceData {
  sections: string[];
  categories: string[];
  languages: string[];
  artwork_specs: Record<string, ArtworkSpec>;
}