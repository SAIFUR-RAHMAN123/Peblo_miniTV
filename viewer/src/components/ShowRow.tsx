import { ShowCard } from "./ShowCard";
import type { ShowEntry } from "../api/types";

const SECTION_LABELS: Record<string, string> = {
  featured: "Featured",
  series: "Series",
  minisodes: "Minisodes",
  songs: "Songs",
};

export function ShowRow({ section, shows }: { section: string; shows: ShowEntry[] }) {
  if (shows.length === 0) return null;
  return (
    <section className="show-row">
      <h2 className="show-row-title">{SECTION_LABELS[section] ?? section}</h2>
      <div className="show-row-scroll">
        {shows.map((show) => (
          <ShowCard key={show.id} show={show} />
        ))}
      </div>
    </section>
  );
}