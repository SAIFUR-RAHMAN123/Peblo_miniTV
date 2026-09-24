const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const KEY_STORAGE = "peblo_cms_api_key";

export function getApiKey(): string | null {
  return localStorage.getItem(KEY_STORAGE);
}

export function setApiKey(key: string): void {
  localStorage.setItem(KEY_STORAGE, key);
}

export function clearApiKey(): void {
  localStorage.removeItem(KEY_STORAGE);
}

export class ApiError extends Error {
  status: number;
  messages: string[];

  constructor(status: number, messages: string[]) {
    super(messages.join(" "));
    this.status = status;
    this.messages = messages;
  }
}

function extractMessages(detail: unknown): string[] {
  if (typeof detail === "string") return [detail];
  if (Array.isArray(detail)) return detail.map((d) => (typeof d === "string" ? d : JSON.stringify(d)));
  if (detail && typeof detail === "object") return [JSON.stringify(detail)];
  return ["Something went wrong."];
}

type RequestOptions = {
  method?: string;
  body?: unknown;
  isFormData?: boolean;
};

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const apiKey = getApiKey();
  const headers: Record<string, string> = {};
  if (apiKey) headers["Authorization"] = `Bearer ${apiKey}`;

  let body: BodyInit | undefined;
  if (options.body !== undefined) {
    if (options.isFormData) {
      body = options.body as FormData;
    } else {
      headers["Content-Type"] = "application/json";
      body = JSON.stringify(options.body);
    }
  }

  const res = await fetch(`${API_BASE}${path}`, {
    method: options.method || "GET",
    headers,
    body,
  });

  if (res.status === 204) return undefined as T;

  const isJson = res.headers.get("content-type")?.includes("application/json");
  const payload = isJson ? await res.json() : undefined;

  if (!res.ok) {
    const messages = extractMessages(payload?.detail ?? payload);
    throw new ApiError(res.status, messages);
  }

  return payload as T;
}