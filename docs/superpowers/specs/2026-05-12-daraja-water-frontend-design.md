# Daraja Water — frontend design

**Date**: 2026-05-12
**Scope**: A Next.js 15 + TypeScript + Tailwind + shadcn/ui frontend consuming the existing Django JSON API. v1 includes login/register, meter management, the buy-token flow with polling-based success detection, and transaction history. Backend gets one small change (CORS).

## Goals

- A bootable Next.js app that consumes the Django API at `http://127.0.0.1:8000/api/` from `http://localhost:3000`.
- End-to-end happy path: register → add meter → initiate transaction → poll for paid → display token.
- A single Playwright e2e test that locks in that happy path against a real backend + real webhook.

## Non-goals

- Server-side rendering / SEO. The app is authenticated and gated; SSR adds complexity without payoff.
- Realtime updates via WebSockets. Polling the transaction detail every 2 seconds is sufficient and avoids re-adding Channels/Redis to the backend.
- XSS-proof auth storage. We use `localStorage` for the JWT pair; the threat model (consumer water-meter customers) doesn't warrant the httpOnly-cookie proxy complexity.
- Unit/component tests. TypeScript + one e2e test is enough for v1; a maintenance-heavy unit-test suite is over-built.

## Stack

- **Framework**: Next.js 15 (App Router), React 19, TypeScript strict.
- **Styling**: Tailwind 4. Component primitives from shadcn/ui (copy-paste into the codebase; Radix-backed for accessibility).
- **Server state**: TanStack Query 5. Axios for HTTP with a JWT-aware response interceptor.
- **Forms**: react-hook-form + zod for validation.
- **Icons**: lucide-react (shadcn standard).
- **Tests**: Playwright (e2e only).

## Project layout

```
mnyama/
├── (backend at root: config/, accounts/, meters/, payments/, ...)
├── frontend/
│   ├── package.json
│   ├── tsconfig.json
│   ├── next.config.ts
│   ├── tailwind.config.ts
│   ├── postcss.config.mjs
│   ├── components.json              # shadcn/ui config
│   ├── playwright.config.ts
│   ├── .env.local                   # NEXT_PUBLIC_API_URL=http://localhost:8000/api
│   ├── public/
│   ├── tests/
│   │   ├── happy-path.spec.ts       # the one e2e test
│   │   └── lib/
│   │       └── fire-webhook.ts      # HMAC helper for the test
│   └── src/
│       ├── app/
│       │   ├── layout.tsx           # root: html shell, global styles, TanStack Query provider
│       │   ├── page.tsx             # redirects to /login or /buy
│       │   ├── login/page.tsx
│       │   ├── register/page.tsx
│       │   └── (app)/               # route group, auth-guarded
│       │       ├── layout.tsx       # nav + auth guard
│       │       ├── meters/page.tsx
│       │       ├── buy/page.tsx
│       │       └── transactions/
│       │           ├── page.tsx     # history list
│       │           └── [id]/page.tsx
│       ├── components/
│       │   ├── ui/                  # shadcn/ui copies (Button, Input, Card, Select, Label, Form, ...)
│       │   ├── auth-guard.tsx
│       │   └── nav-bar.tsx
│       ├── lib/
│       │   ├── api.ts               # axios instance + interceptors
│       │   ├── auth.ts              # localStorage helpers
│       │   ├── query-client.ts      # TanStack Query client
│       │   └── utils.ts             # cn() etc.
│       ├── hooks/
│       │   ├── use-auth.ts          # login / register / logout / me
│       │   ├── use-meters.ts        # list / create / delete
│       │   └── use-transactions.ts  # initiate / detail (polling) / list
│       └── types/
│           └── api.ts               # response types matching backend serializers
```

`.gitignore` at the repo root gets these appended: `frontend/node_modules/`, `frontend/.next/`, `frontend/out/`, `frontend/playwright-report/`, `frontend/test-results/`.

## Bootstrap

```bash
cd frontend
npx create-next-app@latest . --typescript --tailwind --app --src-dir --eslint --no-import-alias
npx shadcn@latest init
npx shadcn@latest add button input label card select form sonner
npm install @tanstack/react-query axios zod react-hook-form @hookform/resolvers
npm install -D @playwright/test
npx playwright install chromium
```

## Routes

```
/                        public; redirects → /login (if no token) or /buy (if token)
/login                   public; phone_number + password form
/register                public; phone_number + password form

/(app)/meters            guarded; list + add (and delete inline)
/(app)/buy               guarded; meter select + amount; on submit → /transactions/{id}
/(app)/transactions      guarded; history, newest first
/(app)/transactions/[id] guarded; detail page; also where /buy lands; polls when status=pending
```

The `(app)` route group applies a shared layout that includes the nav bar + an auth guard without adding a URL segment.

## Auth flow

### Storage (`lib/auth.ts`)

`localStorage` keys: `daraja.access`, `daraja.refresh`. Five wrappers: `getAccessToken`, `setAccessToken`, `getRefreshToken`, `saveTokenPair({access, refresh})`, `clearTokens`. No JWT parsing; we rely on the 401-refresh-retry path instead of preemptive expiry math.

### Axios interceptor (`lib/api.ts`)

The single `api` instance:

- **Request**: attach `Authorization: Bearer <access>` if a token exists.
- **Response 401**: if a refresh token exists, hit `POST /api/auth/refresh/`, save the new access token, retry the original request once. If refresh fails, `clearTokens()` and redirect to `/login`. Concurrent 401s share one refresh promise (10-line refresh-queue pattern) to avoid two concurrent rotations clobbering each other.
- **Response error helper**: `getApiErrorMessage(err)` normalizes DRF's `{detail: "..."}` and `{field: ["msg"]}` shapes for display.

### Login / register / logout

- **Login**: `POST /api/auth/login/` with `{phone_number, password}` → `{access, refresh}`. Save both, redirect to `/buy`.
- **Register**: `POST /api/auth/register/` with `{phone_number, password}`. On 201, immediately login (chain a second mutation) and redirect.
- **Logout**: `POST /api/auth/logout/` (fire-and-forget; today returns 205 from the stub). Then `clearTokens()` and redirect to `/login`. Future-proofed for when SimpleJWT blacklist lands in the housekeeping task.

### Auth guard (`(app)/layout.tsx`)

Client component. On mount, reads `getAccessToken()`. If missing, `router.replace("/login")` and returns null. Once ready, renders the nav bar + children.

## TanStack Query setup

- Default `staleTime: 30_000`, `gcTime: 5 * 60_000`, `retry: 1`. The axios interceptor already handles refresh-retry, so TanStack's retry sits on top of that as the second-chance safety net.
- The `<QueryClientProvider>` lives in the `(app)/layout.tsx` (so it scopes to the authenticated routes; the login/register pages don't need it).
- Per-endpoint hooks live in `src/hooks/`. Each hook owns its query keys and mutation invalidations.

## Buy-token flow

This is the only page with a non-trivial state machine. The flow is split across two pages, with the polling on the detail page.

### `/buy` (the form)

- `useMeters()` → query → populate a `<Select>`.
- Zod schema: `{ meter_id: uuid, amount: number (positive integer) }`.
- `useMutation` on `initiateTransaction`. On success, `router.push(/transactions/${txn.id})`.
- Empty-state when the user has no meters: "Add a meter first" CTA to `/meters`.

### `/transactions/[id]` (the polling + result)

- `useQuery(["transaction", id], () => api.get("/transactions/{id}/"), { refetchInterval })`.
- `refetchInterval` resolves to `2000` while `data?.status === "pending"`, else `false`. TanStack stops polling automatically when the status changes.
- Hard cutoff: if `expires_at` is in the past AND the latest fetch still shows `pending`, render an "expired" branch and stop polling. (Implemented as derived state inside the component, not a separate query.)
- Three render branches:
  - `pending`: control number, amount, "Pay via M-Pesa to ...", spinner, "Waiting for payment..."
  - `paid`: ✓ "Payment received", the token value prominently displayed, "Copy to clipboard" button, "Enter on meter {meter_number}."
  - `failed | expired`: ✗ message + "Try again" link back to `/buy`.

### Why this split

- The buy form stays dumb (just submit). All the state-machine complexity lives in one component, the detail page, which is also reused for history viewing.
- The customer gets a permalink the moment they hit Pay — they can refresh, share, or come back to it later, and the page picks up where it left off.
- Polling is server-state; TanStack Query handles all the cleanup. No manual `setInterval` / cleanup-on-unmount footguns.

## Form validation

- `react-hook-form` for state.
- `zod` schemas adjacent to each page.
- Server-side errors from DRF map to fields via `react-hook-form`'s `setError(fieldName, { message })`. Non-field errors render in a `<Alert>` at the form top.

## Error UX

- shadcn/ui's `sonner` toast for transient errors (network failures, etc.).
- Per-field validation errors inline in forms.
- Auth-failure / 401 cascade redirects to `/login` (handled in the interceptor; no per-page handling).

## Backend changes

One small backend change to allow the Next.js dev server origin:

1. `pyproject.toml`: add `django-cors-headers` dependency.
2. `config/settings.py`: append `"corsheaders"` to `INSTALLED_APPS`, prepend `"corsheaders.middleware.CorsMiddleware"` to `MIDDLEWARE` (before `CommonMiddleware`).
3. Append to `settings.py`:
   ```python
   CORS_ALLOWED_ORIGINS = [
       o.strip() for o in os.environ.get("CORS_ALLOWED_ORIGINS", "").split(",")
       if o.strip()
   ]
   ```
4. `.env.example` + `.env`: `CORS_ALLOWED_ORIGINS=http://localhost:3000`.

No CSRF concerns — we use `Bearer` tokens, not cookies. corsheaders handles OPTIONS preflight automatically.

No other backend changes are needed. The API is feature-complete.

## Testing

One Playwright happy-path e2e test at `frontend/tests/happy-path.spec.ts`.

### Setup

`playwright.config.ts` uses Playwright's `webServer` to boot `npm run dev` (Next.js on :3000) before the test runs. Django must already be running on :8000 — the test assumes this and the developer (or CI) is responsible for booting it.

**Test data isolation**: the test runs against the same `mnyama` database as `runserver` (it does NOT use pytest-django's `test_mnyama`). To avoid colliding with previous runs, the test generates a per-run unique suffix for the phone number and meter number (e.g., `+25570009${randomDigits(4)}` and `01000${randomDigits(5)}`). The test does not clean up after itself — that's acceptable accumulation in a local dev DB. If this becomes annoying, a follow-up can add a teardown that deletes the user it created (CASCADE would handle the rest).

### The test

```
1. Visit /register
2. Fill phone "+255700099001" + password "test-pw-12345" → submit
3. Land on /buy (auto-login + redirect)
4. Click "Add a meter first" → /meters
5. Fill meter_number "0100099001" + label "Test" → submit
6. Navigate to /buy → select the meter → enter amount "5000" → Pay
7. Land on /transactions/{id} → assert "Waiting for payment..." is visible
8. Side-channel: call fire-webhook helper which POSTs the webhook with valid HMAC
   (computes signature against WEBHOOK_HMAC_SECRET pulled from a test .env or hardcoded)
9. Assert page swaps within 5 seconds: "Payment received" text + a non-empty token value visible
```

### `tests/lib/fire-webhook.ts`

A small helper that:
- Reads `WEBHOOK_HMAC_SECRET` from `process.env` (test runner sets it to match what Django is using).
- Computes `sha256=<hex>` over a JSON body matching `{control_number, amount, provider_reference, status: "paid"}`.
- POSTs to `http://127.0.0.1:8000/api/webhooks/payment/`.

### Out of scope for v1

- Unit/component tests (TypeScript types are the primary safety net).
- Cross-browser testing (Chromium only).
- Visual regression / screenshot diffs.
- CI integration — the test is intended for local pre-commit use; CI wiring is a later task.

## What this design does NOT lock in

- The eventual production deployment shape (static export vs Node server vs Vercel). The app is configured for `npm run dev` and `npm run build`; production deployment is a later concern.
- Real provider integration. The frontend talks to the API surface that exists today; when the user's housekeeping task 2 reshapes the webhook payload, the only frontend change should be `fire-webhook.ts` in the e2e test (to match the new schema).
- Token blacklist on logout. The frontend calls `POST /api/auth/logout/` today (no-op stub); when the housekeeping task wires real blacklisting, the call site doesn't change.
