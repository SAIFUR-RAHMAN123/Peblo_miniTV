import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { getPublishRuns, getValidationReport, publishCatalog } from "../api/admin";
import { useAuth } from "../auth/AuthContext";
import { ApiError } from "../api/client";
import { Loading, ErrorView } from "../components/StateViews";
import type { PublishResult } from "../api/types";
import { useState } from "react";

export function PublishPage() {
  const { role } = useAuth();
  const queryClient = useQueryClient();
  const [lastResult, setLastResult] = useState<PublishResult | null>(null);

  const reportQuery = useQuery({ queryKey: ["validation-report"], queryFn: getValidationReport });
  const runsQuery = useQuery({ queryKey: ["publish-runs"], queryFn: getPublishRuns });

  const publishMutation = useMutation({
    mutationFn: publishCatalog,
    onSuccess: (result) => {
      setLastResult(result);
      queryClient.invalidateQueries({ queryKey: ["publish-runs"] });
      queryClient.invalidateQueries({ queryKey: ["validation-report"] });
    },
  });

  if (reportQuery.isPending) return <Loading label="Loading validation report..." />;
  if (reportQuery.isError) {
    const e = reportQuery.error;
    return <ErrorView messages={e instanceof ApiError ? e.messages : ["Failed to load validation report."]} />;
  }

  const report = reportQuery.data;
  const isAdmin = role === "admin";

  let disabledReason: string | null = null;
  if (!isAdmin) disabledReason = "Only admins can publish. Ask an admin to run this.";
  else if (report.blocking) disabledReason = `${report.issues.length} issue(s) must be fixed first.`;

  return (
    <div>
      <h1>Publish</h1>

      <section className="publish-summary">
        <div>
          <strong>{report.published_show_count}</strong> shows /{" "}
          <strong>{report.published_episode_count}</strong> episodes currently published
        </div>
      </section>

      <section className="validation-report">
        <h2>Validation Report</h2>
        {report.issues.length === 0 && report.informational.length === 0 && (
          <p className="success-text">No issues found. Ready to publish.</p>
        )}

        {report.issues.length > 0 && (
          <div className="issue-group issue-group-blocking">
            <h3>Blocking ({report.issues.length})</h3>
            <ul>
              {report.issues.map((issue, i) => (
                <li key={i}>{issue.message}</li>
              ))}
            </ul>
          </div>
        )}

        {report.informational.length > 0 && (
          <div className="issue-group issue-group-info">
            <h3>Worth fixing ({report.informational.length})</h3>
            <ul>
              {report.informational.map((issue, i) => (
                <li key={i}>{issue.message}</li>
              ))}
            </ul>
          </div>
        )}
      </section>

      <section className="publish-action">
        <button
          className="button button-primary"
          disabled={!!disabledReason || publishMutation.isPending}
          onClick={() => publishMutation.mutate()}
          title={disabledReason ?? undefined}
        >
          {publishMutation.isPending ? "Publishing..." : "Publish catalogue"}
        </button>
        {disabledReason && <span className="disabled-reason">{disabledReason}</span>}
      </section>

      {lastResult && (
        <section className={`publish-result ${lastResult.outcome === "success" ? "success" : "failed"}`}>
          {lastResult.outcome === "success" ? (
            <p>
              Published {lastResult.shows_count} shows / {lastResult.episodes_count} episodes.
            </p>
          ) : (
            <div>
              <p>Publish blocked:</p>
              <ul>
                {lastResult.issues?.map((issue, i) => <li key={i}>{issue.message}</li>)}
              </ul>
            </div>
          )}
        </section>
      )}

      <section className="publish-history">
        <h2>Run History</h2>
        {runsQuery.data && runsQuery.data.length === 0 && <p className="muted">No publish runs yet.</p>}
        {runsQuery.data && runsQuery.data.length > 0 && (
          <table className="data-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Triggered by</th>
                <th>Outcome</th>
                <th>Shows</th>
                <th>Episodes</th>
                <th>Started</th>
              </tr>
            </thead>
            <tbody>
              {runsQuery.data.map((run) => (
                <tr key={run.id}>
                  <td>{run.id}</td>
                  <td>{run.triggered_by}</td>
                  <td>
                    <span className={`badge badge-${run.outcome}`}>{run.outcome}</span>
                  </td>
                  <td>{run.shows_count}</td>
                  <td>{run.episodes_count}</td>
                  <td>{run.started_at ? new Date(run.started_at).toLocaleString() : "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}