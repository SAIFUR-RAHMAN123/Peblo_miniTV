export function Loading() {
  return <div className="state-view">Loading...</div>;
}

export function ErrorState({ message }: { message: string }) {
  return <div className="state-view state-error">{message}</div>;
}

export function EmptyState({ children }: { children: React.ReactNode }) {
  return <div className="state-view state-empty">{children}</div>;
}