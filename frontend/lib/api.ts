"use client";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") || "http://localhost:8000";
const PREFIX = "/api/v1";
const TOKEN_KEY = "controlmap_token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string) {
  window.localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  window.localStorage.removeItem(TOKEN_KEY);
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function handle(res: Response) {
  if (!res.ok) {
    let detail = `Request failed (${res.status})`;
    try {
      const data = await res.json();
      detail = typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail);
    } catch {
      /* ignore */
    }
    throw new ApiError(res.status, detail);
  }
  return res;
}

function authHeaders(): Record<string, string> {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export const api = {
  async login(email: string, password: string): Promise<string> {
    const body = new URLSearchParams();
    body.set("username", email);
    body.set("password", password);
    const res = await fetch(`${API_URL}${PREFIX}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body,
    });
    await handle(res);
    const data = await res.json();
    setToken(data.access_token);
    return data.access_token;
  },

  async get<T>(path: string): Promise<T> {
    const res = await fetch(`${API_URL}${PREFIX}${path}`, {
      headers: { ...authHeaders() },
      cache: "no-store",
    });
    await handle(res);
    return res.json();
  },

  async post<T>(path: string, payload?: unknown): Promise<T> {
    const res = await fetch(`${API_URL}${PREFIX}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: payload !== undefined ? JSON.stringify(payload) : undefined,
    });
    await handle(res);
    if (res.status === 204) return undefined as T;
    return res.json();
  },

  async patch<T>(path: string, payload: unknown): Promise<T> {
    const res = await fetch(`${API_URL}${PREFIX}${path}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify(payload),
    });
    await handle(res);
    return res.json();
  },

  async del(path: string): Promise<void> {
    const res = await fetch(`${API_URL}${PREFIX}${path}`, {
      method: "DELETE",
      headers: { ...authHeaders() },
    });
    await handle(res);
  },

  async upload<T>(path: string, file: File): Promise<T> {
    const form = new FormData();
    form.append("file", file);
    const res = await fetch(`${API_URL}${PREFIX}${path}`, {
      method: "POST",
      headers: { ...authHeaders() },
      body: form,
    });
    await handle(res);
    return res.json();
  },

  async download(path: string): Promise<Blob> {
    const res = await fetch(`${API_URL}${PREFIX}${path}`, {
      method: "POST",
      headers: { ...authHeaders() },
    });
    await handle(res);
    return res.blob();
  },
};

export { API_URL };
