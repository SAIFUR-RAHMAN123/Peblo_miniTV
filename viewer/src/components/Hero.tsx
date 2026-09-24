import { Link } from "react-router-dom";
import { LazyImage } from "./LazyImage";
import type { ShowEntry } from "../api/types";

export function Hero({ show }: { show: ShowEntry }) {
  return (
    <section className="hero">
      <LazyImage src={show.banner_url} alt={show.title} className="hero-banner" />
      <div className="hero-overlay">
        <h1 className="hero-title">{show.title}</h1>
        <p className="hero-synopsis">{show.synopsis}</p>
        <div className="hero-categories">
          {show.categories.map((c) => (
            <span key={c} className="pill">
              {c}
            </span>
          ))}
        </div>
        <Link to={`/shows/${show.slug}`} className="hero-cta">
          More Info
        </Link>
      </div>
    </section>
  );
}