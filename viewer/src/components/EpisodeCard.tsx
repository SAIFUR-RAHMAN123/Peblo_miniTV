import { Link } from "react-router-dom";
import { LazyImage } from "./LazyImage";
import type { CatalogEntry } from "../api/types";

function formatDuration(seconds: number | null): string {
  if (!seconds) return "";
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${s.toString().padStart(2, "0")}`;
}

export function EpisodeCard({ entry, showSlug }: { entry: CatalogEntry; showSlug?: string }) {
  const primary = entry.languages[0];
  const content = (
    <>
      <LazyImage src={entry.thumbnail_url} alt={entry.episode_title} className="episode-card-thumb" />
      <div className="episode-card-body">
        <div className="episode-card-title">{entry.episode_title}</div>
        <div className="episode-card-meta">
          {entry.season_number > 0 && (
            <span>
              S{entry.season_number}E{entry.episode_number} ·{" "}
            </span>
          )}
          {formatDuration(primary?.duration_seconds ?? null)}
        </div>
        <div className="language-pills">
          {entry.languages.map((l) => (
            <span key={l.language} className="pill pill-lang">
              {l.language}
            </span>
          ))}
        </div>
      </div>
    </>
  );

  if (showSlug) {
    return (
      <Link to={`/shows/${showSlug}`} className="episode-card">
        {content}
      </Link>
    );
  }
  return (
    <Link to={`/shows/${entry.show_slug}`} className="episode-card">
      <div className="episode-card-show-title">{entry.show_title}</div>
      {content}
    </Link>
  );
}