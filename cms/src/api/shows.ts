import { apiRequest } from "./client";
import type { Paginated, Show, ShowListItem } from "./types";

export interface ShowListParams {
  search?: string;
  section?: string;
  page?: number;
  page_size?: number;
}

export function listShows(params: ShowListParams) {
  const qs = new URLSearchParams();
  if (params.search) qs.set("search", params.search);
  if (params.section) qs.set("section", params.section);
  qs.set("page", String(params.page ?? 1));
  qs.set("page_size", String(params.page_size ?? 20));
  return apiRequest<Paginated<ShowListItem>>(`/admin/shows?${qs.toString()}`);
}

export function getShow(id: number) {
  return apiRequest<Show>(`/admin/shows/${id}`);
}

export interface ShowInput {
  slug: string;
  title: string;
  section: string | null;
  synopsis: string;
  categories: string[];
}

export function createShow(input: ShowInput) {
  return apiRequest<Show>("/admin/shows", { method: "POST", body: input });
}

export function updateShow(id: number, input: Partial<ShowInput>) {
  return apiRequest<Show>(`/admin/shows/${id}`, { method: "PATCH", body: input });
}

export function deleteShow(id: number) {
  return apiRequest<void>(`/admin/shows/${id}`, { method: "DELETE" });
}