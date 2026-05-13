const ACCESS_KEY = "daraja.access";
const REFRESH_KEY = "daraja.refresh";

export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(ACCESS_KEY);
}

export function setAccessToken(token: string): void {
  window.localStorage.setItem(ACCESS_KEY, token);
}

export function getRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(REFRESH_KEY);
}

export function setRefreshToken(token: string): void {
  window.localStorage.setItem(REFRESH_KEY, token);
}

export function saveTokenPair(pair: { access: string; refresh: string }): void {
  setAccessToken(pair.access);
  setRefreshToken(pair.refresh);
}

export function clearTokens(): void {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(ACCESS_KEY);
  window.localStorage.removeItem(REFRESH_KEY);
}
