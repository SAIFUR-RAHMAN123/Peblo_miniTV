export interface LanguageVariant {
  language: string;
  episode_id: string;
  duration_seconds: number | null;
  thumbnail_url: string | null;
}

export interface CatalogEntry {
  content_group: string;
  show_id: number;
  show_slug: string;
  show_title: string;
  section: string;
  categories: string[];
  season_number: number;
  episode_number: number;
  episode_title: string;
  languages: LanguageVariant[];
  poster_url: string | null;
  banner_url: string | null;
  thumbnail_url: string | null;
}

export interface SeasonGroup {
  season_number: number;
  episodes: CatalogEntry[];
}

export interface ShowEntry {
  id: number;
  slug: string;
  title: string;
  synopsis: string;
  categories: string[];
  section: string;
  poster_url: string | null;
  banner_url: string | null;
  seasons: SeasonGroup[];
  trailers: CatalogEntry[];
}

export interface SectionGroup {
  section: string;
  shows: ShowEntry[];
}

export interface CatalogResponse {
  generated_at: string | null;
  hero: ShowEntry | null;
  sections: SectionGroup[];
  entries: CatalogEntry[];
  publish_run_id?: number;
}

export interface SearchResponse {
  query: string | null;
  filters: { category: string | null; language: string | null; section: string | null };
  count: number;
  results: CatalogEntry[];
}

export interface ReferenceData {
  sections: string[];
  categories: string[];
  languages: string[];
}