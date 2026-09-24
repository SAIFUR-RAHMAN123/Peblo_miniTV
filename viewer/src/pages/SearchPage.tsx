import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { searchCatalog, getReferenceData } from "../api/catalog";
import { EpisodeCard } from "../components/EpisodeCard";
import { Loading, ErrorState, EmptyState } from "../components/StateViews";

export function SearchPage() {
  const [q, setQ] = useState("");
  const [category, setCategory] = useState("");
  const [language, setLanguage] = useState("");
  const [section, setSection] = useState("");

  const refQuery = useQuery({ queryKey: ["reference"], queryFn: getReferenceData });
  const searchQuery = useQuery({
    queryKey: ["search", q, category, language, section],
    queryFn: () => searchCatalog({ q: q || undefined, category: category || undefined, language: language || undefined, section: section || undefined }),
  });

  return (
    <div className="search-page">
      <h1>Search</h1>
      <div className="search-controls">
        <input
          className="search-input"
          placeholder="Search shows, episodes, categories..."
          value={q}
          onChange={(e) => setQ(e.target.value)}
          autoFocus
        />
        <div className="filters-bar">
          <select value={section} onChange={(e) => setSection(e.target.value)}>
            <option value="">All sections</option>
            {refQuery.data?.sections.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
          <select value={category} onChange={(e) => setCategory(e.target.value)}>
            <option value="">All categories</option>
            {refQuery.data?.categories.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
          <select value={language} onChange={(e) => setLanguage(e.target.value)}>
            <option value="">All languages</option>
            {refQuery.data?.languages.map((l) => (
              <option key={l} value={l}>
                {l}
              </option>
            ))}
          </select>
        </div>
      </div>

      {searchQuery.isPending && <Loading />}
      {searchQuery.isError && <ErrorState message="Search failed. Is the API running?" />}
      {searchQuery.data && searchQuery.data.results.length === 0 && (
        <EmptyState>
          {q || category || language || section
            ? "No results match your search. Try different filters."
            : "Nothing published yet."}
        </EmptyState>
      )}
      {searchQuery.data && searchQuery.data.results.length > 0 && (
        <div className="episode-grid">
          {searchQuery.data.results.map((entry) => (
            <EpisodeCard key={`${entry.content_group}`} entry={entry} />
          ))}
        </div>
      )}
    </div>
  );
}