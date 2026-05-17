I'm building Daraja Water — a prepaid water meter top-up platform for Tanzanian customers. The scaffold is already in this repo (Django backend + Next.js frontend + MySQL + Redis/Channels for WebSockets). Read the README.md first to understand the architecture, then help me get it running and extend it.

## Stack
- Backend: Django 5 + DRF + Channels + SimpleJWT, MySQL, Redis
- Frontend: Next.js 15 (App Router) + TypeScript + Tailwind
- Auth: JWT (access + refresh)
- Realtime: WebSockets via Channels, JWT in query string, per-user groups
- Token formula: (amount × 1357) + meter_id, isolated in payments/token_logic.py

## Core flow
1. Customer logs in, adds a meter (meter_number linked to their account)
2. Customer picks meter + amount → backend creates a Transaction with a 12-digit control number (99-prefixed) and returns it
3. Customer pays via mobile money / bank using that control number
4. Payment provider POSTs to /api/webhooks/payment/ with HMAC-SHA256 signature in X-Signature header
5. Webhook verifies signature, marks Transaction paid (idempotent), generates Token, sends SMS, pushes payment.succeeded event over WebSocket to the user's group
6. Frontend buy-token page swaps to success view automatically when WS event arrives

## Tasks (in order)

### 1. Local setup
- Walk me through getting MySQL and Redis running locally (I'm on macOS / Ubuntu — ask which)
- Run migrations, create superuser, start Daphne and Next.js dev server
- Sanity check: register a user, add a meter, initiate a transaction, hit the webhook with a curl command including a valid HMAC signature, confirm token appears in the UI in real time

### 2. Wire my actual payment API
- I'll paste the payment provider's docs in a follow-up message. Ask me for them.
- Update payments/views.py:InitiatePaymentView to call the provider's API after creating the Transaction (if the provider needs to be notified of new control numbers)
- Update PaymentWebhookView to match the provider's actual callback schema (field names, signature header name, signing algorithm). Keep the verification step.
- Add tests for the webhook: valid signature succeeds, invalid signature returns 401, replay is idempotent, unknown control number returns 404

### 3. Production-hardening the token formula
- The current SimpleTokenStrategy is reversible — anyone with the multiplier can mint tokens
- Add an HmacTokenStrategy in payments/token_logic.py that signs (amount, meter_id, nonce) with a server secret and produces a numeric token short enough to enter on a keypad (target ~10–14 digits)
- Make the strategy selectable via a TOKEN_STRATEGY env var
- Keep the simple strategy working for backward compatibility / Arduino prototypes
- Add unit tests for both strategies (round-trip, tamper detection, wrong meter)

### 4. SMS provider
- I'll tell you which provider (Beem, Twilio, or Africa's Talking). Ask.
- Implement the provider class in payments/sms.py and register it in _get_provider()
- Add retry-with-backoff (3 attempts) since SMS gateways flake
- Mark Token.delivered_via_sms only after successful delivery

### 5. Housekeeping
- Add a Django management command `expire_transactions` that marks pending transactions past their expires_at as expired
- Add basic rate limiting on /api/auth/login/ and /api/transactions/initiate/ (django-ratelimit or DRF throttling)
- Add a logout endpoint that blacklists the refresh token (SimpleJWT token_blacklist app)

## Working style
- Before changing code, read the relevant file(s) so you understand what's there
- For each task, propose the change in plain English first, wait for me to say "go", then implement
- After implementing, run the tests and confirm they pass before moving on
- If you hit something ambiguous, ask one focused question rather than guessing
- Don't refactor files you weren't asked to touch
- Commit after each task with a clear message

Start with task 1. Ask me whether which payment provider I'll be using.