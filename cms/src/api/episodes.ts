import { apiRequest } from "./client";
import type { ArtworkItem, Episode, Paginated } from "./types";

export interface EpisodeListParams {
  show_id?: number;
  status?: string;
  language?: string;
  search?: string;
  page?: number;
  page_size?: number;
}

export function listEpisodes(params: EpisodeListParams) {
  const qs = new URLSearchParams();
  if (params.show_id) qs.set("show_id", String(params.show_id));
  if (params.status) qs.set("status", params.status);
  if (params.language) qs.set("language", params.language);
  if (params.search) qs.set("search", params.search);
  qs.set("page", String(params.page ?? 1));
  qs.set("page_size", String(params.page_size ?? 50));
  return apiRequest<Paginated<Episode>>(`/admin/episodes?${qs.toString()}`);
}

export function getEpisode(id: number) {
  return apiRequest<Episode>(`/admin/episodes/${id}`);
}

export interface EpisodeInput {
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

export function createEpisode(input: EpisodeInput) {
  return apiRequest<Episode>("/admin/episodes", { method: "POST", body: input });
}

export function updateEpisode(id: number, input: Partial<EpisodeInput>) {
  return apiRequest<Episode>(`/admin/episodes/${id}`, { method: "PATCH", body: input });
}

export function deleteEpisode(id: number) {
  return apiRequest<void>(`/admin/episodes/${id}`, { method: "DELETE" });
}

export function listArtwork(episodePk: number) {
  return apiRequest<ArtworkItem[]>(`/admin/episodes/${episodePk}/artwork`);
}

export function uploadArtwork(episodePk: number, kind: string, file: File) {
  const form = new FormData();
  form.set("kind", kind);
  form.set("file", file);
  return apiRequest<ArtworkItem>(`/admin/episodes/${episodePk}/artwork`, {
    method: "POST",
    body: form,
    isFormData: true,
  });
}