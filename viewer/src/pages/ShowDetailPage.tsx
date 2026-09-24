import { useMemo, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getCatalog } from "../api/catalog";
import { LazyImage } from "../components/LazyImage";
import { Loading, ErrorState } from "../components/StateViews";
import type { CatalogEntry, ShowEntry } from "../api/types";

function formatDuration(seconds: number | null): string {
  if (!seconds) return "";
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${s.toString().padStart(2, "0")}`;
}

function EpisodeRow({ entry }: { entry: CatalogEntry }) {
  const [activeLang, setActiveLang] = useState(entry.languages[0]?.language);
  const activeVariant = entry.languages.find((l) => l.language === activeLang) ?? entry.languages[0];

  return (
    <div className="episode-row">
      <LazyImage
        src={activeVariant?.thumbnail_url ?? entry.thumbnail_url}
        alt={entry.episode_title}
        className="episode-row-thumb"
      />
      <div className="episode-row-body">
        <div className="episode-row-title">
          {entry.season_number > 0 ? `${entry.episode_number}. ` : ""}
          {entry.episode_title}
        </div>
        <div className="episode-row-meta">{formatDuration(activeVariant?.duration_seconds ?? null)}</div>
        {entry.languages.length > 1 && (
          <div className="language-pills">
            {entry.languages.map((l) => (
              <button
                key={l.language}
                className={`pill pill-lang pill-lang-button ${l.language === activeLang ? "active" : ""}`}
                onClick={() => setActiveLang(l.language)}
              >
                {l.language}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export function ShowDetailPage() {
  const { slug } = useParams<{ slug: string }>();
  const { data, isPending, isError } = useQuery({ queryKey: ["catalog"], queryFn: getCatalog });

  const show: ShowEntry | undefined = useMemo(() => {
    if (!data) return undefined;
    for (const sec of data.sections) {
      const found = sec.shows.find((s) => s.slug === slug);
      if (found) return found;
    }
    return undefined;
  }, [data, slug]);

  if (isPending) return <Loading />;
  if (isError) return <ErrorState message="Couldn't load this show. Is the API running?" />;
  if (!show) {
    return (
      <div className="show-detail-page">
        <Link to="/" className="detail-back-btn detail-back-btn-static">
          &larr;
        </Link>
        <p style={{ padding: "80px 40px", color: "var(--muted)" }}>This show isn't available.</p>
      </div>
    );
  }

  return (
    <div className="show-detail-page">
      <div className="show-detail-hero">
        <LazyImage src={show.banner_url} alt={show.title} className="show-detail-banner" />
        <div className="show-detail-hero-overlay">
          <Link to="/" className="detail-back-btn" aria-label="Back to home">
            &larr;
          </Link>
          <div className="show-detail-hero-content">
            <h1>{show.title}</h1>
            <div className="hero-categories">
              {show.categories.map((c) => (
                <span key={c} className="pill">
                  {c}
                </span>
              ))}
            </div>
            <p className="show-detail-synopsis">{show.synopsis}</p>
          </div>
        </div>
      </div>

      <div className="show-detail-body">
        {show.trailers.length > 0 && (
          <section className="episodes-section">
            <h2>Trailers</h2>
            <div className="episode-list">
              {show.trailers.map((t) => (
                <EpisodeRow key={t.content_group} entry={t} />
              ))}
            </div>
          </section>
        )}

        {show.seasons.map((season) => (
          <section key={season.season_number} className="episodes-section">
            <h2>Season {season.season_number}</h2>
            <div className="episode-list">
              {season.episodes.map((ep) => (
                <EpisodeRow key={ep.content_group} entry={ep} />
              ))}
            </div>
          </section>
        ))}
      </div>
    </div>
  );
}