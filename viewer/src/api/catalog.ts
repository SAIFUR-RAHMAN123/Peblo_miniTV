import { apiGet } from "./client";
import type { CatalogResponse, ReferenceData, SearchResponse } from "./types";

export function getCatalog() {
  return apiGet<CatalogResponse>("/catalog");
}

export interface SearchParams {
  q?: string;
  category?: string;
  language?: string;
  section?: string;
}

export function searchCatalog(params: SearchParams) {
  const qs = new URLSearchParams();
  if (params.q) qs.set("q", params.q);
  if (params.category) qs.set("category", params.category);
  if (params.language) qs.set("language", params.language);
  if (params.section) qs.set("section", params.section);
  return apiGet<SearchResponse>(`/catalog/search?${qs.toString()}`);
}

export function getReferenceData() {
  return apiGet<ReferenceData>("/reference");
}