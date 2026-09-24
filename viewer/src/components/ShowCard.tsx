import { Link } from "react-router-dom";
import { LazyImage } from "./LazyImage";
import type { ShowEntry } from "../api/types";

export function ShowCard({ show }: { show: ShowEntry }) {
  return (
    <Link to={`/shows/${show.slug}`} className="show-card">
      <LazyImage src={show.poster_url} alt={show.title} className="show-card-poster" />
      <div className="show-card-title">{show.title}</div>
    </Link>
  );
}