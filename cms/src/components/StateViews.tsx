import type { ReactNode } from "react";

export function Loading({ label = "Loading..." }: { label?: string }) {
  return <div className="state-view state-loading">{label}</div>;
}

export function ErrorView({ messages }: { messages: string[] }) {
  return (
    <div className="state-view state-error">
      <strong>Something went wrong:</strong>
      <ul>
        {messages.map((m, i) => (
          <li key={i}>{m}</li>
        ))}
      </ul>
    </div>
  );
}

export function PermissionDenied() {
  return (
    <div className="state-view state-error">
      You don't have permission to do this. Ask an admin if you believe this is a mistake.
    </div>
  );
}

export function EmptyState({ children }: { children: ReactNode }) {
  return <div className="state-view state-empty">{children}</div>;
}