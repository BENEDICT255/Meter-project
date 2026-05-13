import axios, { AxiosError, AxiosResponse, InternalAxiosRequestConfig } from "axios";

import { clearTokens, getAccessToken, getRefreshToken, setAccessToken } from "./auth";

const baseURL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";

export const api = axios.create({ baseURL });

api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = getAccessToken();
  if (token) {
    config.headers.set("Authorization", `Bearer ${token}`);
  }
  return config;
});

// Refresh queue: serialize concurrent 401-retries behind a single refresh call.
let refreshPromise: Promise<string> | null = null;

async function refreshAccess(): Promise<string> {
  const refresh = getRefreshToken();
  if (!refresh) throw new Error("no refresh token");
  const resp = await axios.post<{ access: string }>(`${baseURL}/auth/refresh/`, { refresh });
  setAccessToken(resp.data.access);
  return resp.data.access;
}

type RetriableRequest = InternalAxiosRequestConfig & { _retry?: boolean };

api.interceptors.response.use(
  (r: AxiosResponse) => r,
  async (err: AxiosError) => {
    const original = err.config as RetriableRequest | undefined;
    if (!original || err.response?.status !== 401 || original._retry) {
      return Promise.reject(err);
    }
    if (!getRefreshToken()) {
      return Promise.reject(err);
    }
    original._retry = true;
    try {
      refreshPromise ??= refreshAccess().finally(() => {
        refreshPromise = null;
      });
      const newAccess = await refreshPromise;
      original.headers.set("Authorization", `Bearer ${newAccess}`);
      return api(original);
    } catch (refreshErr) {
      clearTokens();
      if (typeof window !== "undefined") {
        window.location.href = "/login";
      }
      return Promise.reject(refreshErr);
    }
  },
);

// Helper to extract user-friendly error messages from DRF error shapes.
export function getApiErrorMessage(err: unknown): string {
  if (axios.isAxiosError(err)) {
    const data = err.response?.data as Record<string, unknown> | undefined;
    if (data) {
      if (typeof data.detail === "string") return data.detail;
      // Pick the first field error
      for (const [field, messages] of Object.entries(data)) {
        if (Array.isArray(messages) && messages.length > 0) {
          return `${field}: ${messages[0]}`;
        }
      }
    }
    if (err.message) return err.message;
  }
  if (err instanceof Error) return err.message;
  return "Something went wrong";
}
