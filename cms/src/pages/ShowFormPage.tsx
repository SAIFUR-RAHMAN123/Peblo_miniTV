import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useNavigate, useParams } from "react-router-dom";
import { createShow, getShow, updateShow, type ShowInput } from "../api/shows";
import { listEpisodes } from "../api/episodes";
import { getReferenceData } from "../api/admin";
import { ApiError } from "../api/client";
import { Loading, ErrorView, PermissionDenied } from "../components/StateViews";
import { StatusBadge } from "../components/StatusBadge";

export function ShowFormPage() {
  const params = useParams();
  const isNew = params.id === "new";
  const showId = isNew ? null : Number(params.id);
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const refQuery = useQuery({ queryKey: ["reference"], queryFn: getReferenceData });
  const showQuery = useQuery({
    queryKey: ["show", showId],
    queryFn: () => getShow(showId as number),
    enabled: !isNew,
  });
  const episodesQuery = useQuery({
    queryKey: ["episodes", showId],
    queryFn: () => listEpisodes({ show_id: showId as number, page_size: 100 }),
    enabled: !isNew,
  });

  const [form, setForm] = useState<ShowInput>({ slug: "", title: "", section: null, synopsis: "", categories: [] });
  const [formError, setFormError] = useState<string[]>([]);

  useEffect(() => {
    if (showQuery.data) {
      setForm({
        slug: showQuery.data.slug,
        title: showQuery.data.title,
        section: showQuery.data.section,
        synopsis: showQuery.data.synopsis,
        categories: showQuery.data.categories,
      });
    }
  }, [showQuery.data]);

  const saveMutation = useMutation({
    mutationFn: () =>
      isNew
        ? createShow(form)
        : updateShow(showId as number, { title: form.title, section: form.section, synopsis: form.synopsis, categories: form.categories }),
    onSuccess: (result) => {
      setFormError([]);
      queryClient.invalidateQueries({ queryKey: ["shows"] });
      if (isNew) navigate(`/shows/${result.id}`);
      else queryClient.invalidateQueries({ queryKey: ["show", showId] });
    },
    onError: (e: unknown) => {
      setFormError(e instanceof ApiError ? e.messages : ["Failed to save show."]);
    },
  });

  if (!isNew && showQuery.isPending) return <Loading label="Loading show..." />;
  if (!isNew && showQuery.isError) {
    const e = showQuery.error;
    if (e instanceof ApiError && (e.status === 401 || e.status === 403)) return <PermissionDenied />;
    return <ErrorView messages={e instanceof ApiError ? e.messages : ["Failed to load show."]} />;
  }

  function toggleCategory(cat: string) {
    setForm((f) => ({
      ...f,
      categories: f.categories.includes(cat) ? f.categories.filter((c) => c !== cat) : [...f.categories, cat],
    }));
  }

  return (
    <div>
      <div className="page-header">
        <h1>{isNew ? "New Show" : form.title || "Edit Show"}</h1>
        <Link to="/shows">&larr; Back to shows</Link>
      </div>

      <form
        className="entity-form"
        onSubmit={(e) => {
          e.preventDefault();
          saveMutation.mutate();
        }}
      >
        <label>
          Slug {!isNew && <span className="muted">(cannot be changed)</span>}
          <input
            value={form.slug}
            disabled={!isNew}
            onChange={(e) => setForm({ ...form, slug: e.target.value })}
            required
          />
        </label>

        <label>
          Title
          <input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} required />
        </label>

        <label>
          Section
          <select
            value={form.section ?? ""}
            onChange={(e) => setForm({ ...form, section: e.target.value || null })}
          >
            <option value="">(none — required before publishing)</option>
            {refQuery.data?.sections.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </label>

        <label>
          Synopsis
          <textarea
            value={form.synopsis}
            onChange={(e) => setForm({ ...form, synopsis: e.target.value })}
            rows={3}
          />
        </label>

        <fieldset>
          <legend>Categories</legend>
          <div className="checkbox-grid">
            {refQuery.data?.categories.map((cat) => (
              <label key={cat} className="checkbox-item">
                <input
                  type="checkbox"
                  checked={form.categories.includes(cat)}
                  onChange={() => toggleCategory(cat)}
                />
                {cat}
              </label>
            ))}
          </div>
        </fieldset>

        {formError.length > 0 && <ErrorView messages={formError} />}

        <button type="submit" className="button button-primary" disabled={saveMutation.isPending}>
          {saveMutation.isPending ? "Saving..." : "Save"}
        </button>
      </form>

      {!isNew && (
        <div className="episodes-section">
          <div className="page-header">
            <h2>Episodes</h2>
            <Link className="button" to={`/shows/${showId}/episodes/new`}>
              + New Episode
            </Link>
          </div>
          {episodesQuery.isPending && <Loading label="Loading episodes..." />}
          {episodesQuery.data && episodesQuery.data.items.length === 0 && (
            <p className="muted">No episodes yet.</p>
          )}
          {episodesQuery.data && episodesQuery.data.items.length > 0 && (
            <table className="data-table">
              <thead>
                <tr>
                  <th>S/E</th>
                  <th>Title</th>
                  <th>Language</th>
                  <th>Content group</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {episodesQuery.data.items.map((ep) => (
                  <tr key={ep.id}>
                    <td>
                      {ep.season_number === 0 ? "Trailer" : `S${ep.season_number}E${ep.episode_number}`}
                    </td>
                    <td>
                      <Link to={`/episodes/${ep.id}`}>{ep.episode_title}</Link>
                    </td>
                    <td>{ep.language}</td>
                    <td className="muted">{ep.content_group}</td>
                    <td>
                      <StatusBadge status={ep.status} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  );
}