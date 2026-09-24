import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  createEpisode,
  deleteEpisode,
  getEpisode,
  listArtwork,
  updateEpisode,
  type EpisodeInput,
} from "../api/episodes";
import { getShow } from "../api/shows";
import { getReferenceData } from "../api/admin";
import { ApiError } from "../api/client";
import { Loading, ErrorView, PermissionDenied } from "../components/StateViews";
import { ArtworkSlot } from "../components/ArtworkSlot";

const ARTWORK_KINDS: Array<{ kind: "poster" | "banner" | "thumbnail"; label: string }> = [
  { kind: "poster", label: "Poster" },
  { kind: "banner", label: "Banner" },
  { kind: "thumbnail", label: "Thumbnail" },
];

export function EpisodeFormPage() {
  const params = useParams<{ showId?: string; id?: string }>();
  const isNew = params.id === undefined;
  const episodePk = isNew ? null : Number(params.id);
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const refQuery = useQuery({ queryKey: ["reference"], queryFn: getReferenceData });
  const episodeQuery = useQuery({
    queryKey: ["episode", episodePk],
    queryFn: () => getEpisode(episodePk as number),
    enabled: !isNew,
  });
  const artworkQuery = useQuery({
    queryKey: ["artwork", episodePk],
    queryFn: () => listArtwork(episodePk as number),
    enabled: !isNew,
  });

  const knownShowId = isNew ? Number(params.showId) : episodeQuery.data?.show_id;
  const showQuery = useQuery({
    queryKey: ["show", knownShowId],
    queryFn: () => getShow(knownShowId as number),
    enabled: !!knownShowId,
  });

  const [form, setForm] = useState<EpisodeInput>({
    episode_id: "",
    show_id: knownShowId ?? 0,
    season_number: 1,
    episode_number: 1,
    episode_title: "",
    duration_seconds: null,
    language: "en",
    content_group: "",
    status: "draft",
  });
  const [formError, setFormError] = useState<string[]>([]);

  useEffect(() => {
    if (episodeQuery.data) setForm(episodeQuery.data);
    else if (isNew && knownShowId) setForm((f) => ({ ...f, show_id: knownShowId }));
  }, [episodeQuery.data, isNew, knownShowId]);

  const saveMutation = useMutation({
    mutationFn: () => (isNew ? createEpisode(form) : updateEpisode(episodePk as number, form)),
    onSuccess: (result) => {
      setFormError([]);
      queryClient.invalidateQueries({ queryKey: ["episodes"] });
      if (isNew) navigate(`/episodes/${result.id}`);
      else queryClient.invalidateQueries({ queryKey: ["episode", episodePk] });
    },
    onError: (e: unknown) => {
      setFormError(e instanceof ApiError ? e.messages : ["Failed to save episode."]);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: () => deleteEpisode(episodePk as number),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["episodes"] });
      navigate(`/shows/${form.show_id}`);
    },
  });

  if (!isNew && (episodeQuery.isPending || artworkQuery.isPending)) return <Loading label="Loading episode..." />;
  if (!isNew && episodeQuery.isError) {
    const e = episodeQuery.error;
    if (e instanceof ApiError && (e.status === 401 || e.status === 403)) return <PermissionDenied />;
    return <ErrorView messages={e instanceof ApiError ? e.messages : ["Failed to load episode."]} />;
  }

  const artworkByKind = Object.fromEntries((artworkQuery.data ?? []).map((a) => [a.kind, a]));

  return (
    <div>
      <div className="page-header">
        <h1>{isNew ? "New Episode" : form.episode_title || "Edit Episode"}</h1>
        <Link to={showQuery.data ? `/shows/${showQuery.data.id}` : "/shows"}>
          &larr; Back to {showQuery.data?.title ?? "show"}
        </Link>
      </div>

      <form
        className="entity-form"
        onSubmit={(e) => {
          e.preventDefault();
          saveMutation.mutate();
        }}
      >
        <label>
          Episode ID (business key)
          <input
            value={form.episode_id}
            disabled={!isNew}
            onChange={(e) => setForm({ ...form, episode_id: e.target.value })}
            required
          />
        </label>

        <div className="form-row">
          <label>
            Season number
            <input
              type="number"
              min={0}
              value={form.season_number}
              onChange={(e) => setForm({ ...form, season_number: Number(e.target.value) })}
              required
            />
            <span className="field-hint">Season 0 = trailer</span>
          </label>
          <label>
            Episode number
            <input
              type="number"
              min={1}
              value={form.episode_number}
              onChange={(e) => setForm({ ...form, episode_number: Number(e.target.value) })}
              required
            />
          </label>
        </div>

        <label>
          Episode title
          <input
            value={form.episode_title}
            onChange={(e) => setForm({ ...form, episode_title: e.target.value })}
            required
          />
        </label>

        <div className="form-row">
          <label>
            Duration (seconds)
            <input
              type="number"
              min={1}
              value={form.duration_seconds ?? ""}
              onChange={(e) =>
                setForm({ ...form, duration_seconds: e.target.value ? Number(e.target.value) : null })
              }
            />
          </label>
          <label>
            Language
            <select value={form.language} onChange={(e) => setForm({ ...form, language: e.target.value })}>
              {refQuery.data?.languages.map((l) => (
                <option key={l} value={l}>
                  {l}
                </option>
              ))}
            </select>
          </label>
        </div>

        <label>
          Content group
          <input
            value={form.content_group}
            onChange={(e) => setForm({ ...form, content_group: e.target.value })}
            required
          />
          <span className="field-hint">
            Episodes sharing a content group are language variants of the same episode and collapse into one
            catalogue entry.
          </span>
        </label>

        <label>
          Status
          <select value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value as "draft" | "published" })}>
            <option value="draft">draft</option>
            <option value="published">published</option>
          </select>
        </label>

        {formError.length > 0 && <ErrorView messages={formError} />}

        <div className="form-actions">
          <button type="submit" className="button button-primary" disabled={saveMutation.isPending}>
            {saveMutation.isPending ? "Saving..." : "Save"}
          </button>
          {!isNew && (
            <button
              type="button"
              className="button button-danger"
              onClick={() => {
                if (confirm("Delete this episode? This cannot be undone.")) deleteMutation.mutate();
              }}
            >
              Delete episode
            </button>
          )}
        </div>
      </form>

      {!isNew && (
        <div className="artwork-section">
          <h2>Artwork</h2>
          <p className="muted">
            All three are required before this episode can be published. JPG or PNG, under{" "}
            {refQuery.data?.artwork_specs.poster.max_kb ?? 200}KB each.
          </p>
          <div className="artwork-slots">
            {ARTWORK_KINDS.map(({ kind, label }) => (
              <ArtworkSlot
                key={kind}
                episodePk={episodePk as number}
                kind={kind}
                label={label}
                spec={refQuery.data?.artwork_specs[kind]}
                existing={artworkByKind[kind]}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}