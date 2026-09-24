import { useQuery } from "@tanstack/react-query";
import { getCatalog } from "../api/catalog";
import { Hero } from "../components/Hero";
import { ShowRow } from "../components/ShowRow";
import { Loading, ErrorState, EmptyState } from "../components/StateViews";

export function HomePage() {
  const { data, isPending, isError } = useQuery({ queryKey: ["catalog"], queryFn: getCatalog });

  if (isPending) return <Loading />;
  if (isError) return <ErrorState message="Couldn't load the catalogue. Is the API running?" />;

  if (data.sections.length === 0) {
    return (
      <EmptyState>
        Nothing has been published yet. Check back soon!
      </EmptyState>
    );
  }

  return (
    <div className="home-page">
      {data.hero && <Hero show={data.hero} />}
      <div className="show-rows">
        {data.sections.map((sec) => (
          <ShowRow key={sec.section} section={sec.section} shows={sec.shows} />
        ))}
      </div>
    </div>
  );
}