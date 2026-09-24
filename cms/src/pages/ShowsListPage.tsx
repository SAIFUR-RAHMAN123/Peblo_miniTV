import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { listShows } from "../api/shows";
import { getReferenceData } from "../api/admin";
import { ApiError } from "../api/client";
import { Loading, ErrorView, PermissionDenied, EmptyState } from "../components/StateViews";
import { Pagination } from "../components/Pagination";

export function ShowsListPage() {
  const [search, setSearch] = useState("");
  const [section, setSection] = useState("");
  const [page, setPage] = useState(1);

  const refQuery = useQuery({ queryKey: ["reference"], queryFn: getReferenceData });
  const showsQuery = useQuery({
    queryKey: ["shows", search, section, page],
    queryFn: () => listShows({ search: search || undefined, section: section || undefined, page, page_size: 20 }),
  });

  if (showsQuery.isPending) return <Loading label="Loading shows..." />;
  if (showsQuery.isError) {
    const e = showsQuery.error;
    if (e instanceof ApiError && (e.status === 401 || e.status === 403)) return <PermissionDenied />;
    return <ErrorView messages={e instanceof ApiError ? e.messages : ["Failed to load shows."]} />;
  }

  const data = showsQuery.data;

  return (
    <div>
      <div className="page-header">
        <h1>Shows</h1>
        <Link className="button button-primary" to="/shows/new">
          + New Show
        </Link>
      </div>

      <div className="filters-bar">
        <input
          placeholder="Search by title..."
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            setPage(1);
          }}
        />
        <select
          value={section}
          onChange={(e) => {
            setSection(e.target.value);
            setPage(1);
          }}
        >
          <option value="">All sections</option>
          {refQuery.data?.sections.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
      </div>

      {data.items.length === 0 ? (
        <EmptyState>No shows match your filters.</EmptyState>
      ) : (
        <table className="data-table">
          <thead>
            <tr>
              <th>Title</th>
              <th>Slug</th>
              <th>Section</th>
              <th>Episodes</th>
              <th>Published</th>
            </tr>
          </thead>
          <tbody>
            {data.items.map((show) => (
              <tr key={show.id}>
                <td>
                  <Link to={`/shows/${show.id}`}>{show.title}</Link>
                </td>
                <td className="muted">{show.slug}</td>
                <td>
                  {show.section ? (
                    show.section
                  ) : (
                    <span className="warning-text">no section</span>
                  )}
                </td>
                <td>{show.episode_count}</td>
                <td>{show.published_episode_count}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <Pagination page={data.page} pageSize={data.page_size} total={data.total} onChange={setPage} />
    </div>
  );
}