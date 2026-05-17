# Daraja Water

Prepaid water meter top-up platform. Django + DRF + MySQL JSON API.

## Setup (macOS)

```bash
# 1. System deps
brew install mysql pkg-config mysql-client
brew services start mysql
export PKG_CONFIG_PATH="$(brew --prefix mysql-client)/lib/pkgconfig"

# 2. Create databases
mysql -uroot <<'SQL'
CREATE DATABASE IF NOT EXISTS daraja;
CREATE DATABASE IF NOT EXISTS test_daraja;
CREATE USER IF NOT EXISTS 'daraja'@'localhost' IDENTIFIED BY 'daraja';
GRANT ALL PRIVILEGES ON daraja.* TO 'daraja'@'localhost';
GRANT ALL PRIVILEGES ON test_daraja.* TO 'daraja'@'localhost';
FLUSH PRIVILEGES;
SQL

# 3. Python deps via uv
curl -LsSf https://astral.sh/uv/install.sh | sh  # if not installed
uv sync

# 4. App config
cp .env.example .env
# Edit .env: at minimum set SECRET_KEY and WEBHOOK_HMAC_SECRET to real values.

# 5. Migrations + superuser
uv run python manage.py migrate
uv run python manage.py createsuperuser
```

## Run

```bash
uv run python manage.py runserver
```

API is at `http://127.0.0.1:8000/api/`. Admin at `http://127.0.0.1:8000/admin/`.

## Tests

```bash
uv run pytest
```

## End-to-end sanity check

This bash snippet exercises the full happy path against the Swahilies STK-push flow. Start the dev server with the fake payment provider so it doesn't try to hit the real Swahilies API:

```bash
PAYMENT_PROVIDER=fake uv run python manage.py runserver
```

Then in another shell:

```bash
set -e

API=http://127.0.0.1:8000/api
PHONE="+255700000777"
PASSWORD="pw-sanity-1234"

# 1. Register
curl -s -X POST "$API/auth/register/" \
  -H "Content-Type: application/json" \
  -d "{\"phone_number\":\"$PHONE\",\"password\":\"$PASSWORD\"}" > /dev/null

# 2. Login → JWT
ACCESS=$(curl -s -X POST "$API/auth/login/" \
  -H "Content-Type: application/json" \
  -d "{\"phone_number\":\"$PHONE\",\"password\":\"$PASSWORD\"}" \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['access'])")

# 3. Add meter
METER_ID=$(curl -s -X POST "$API/meters/" \
  -H "Authorization: Bearer $ACCESS" -H "Content-Type: application/json" \
  -d '{"meter_number":"0100007777","label":"Sanity"}' \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['id'])")

# 4. Initiate (phone_number is required — the STK push target)
INIT=$(curl -s -X POST "$API/transactions/initiate/" \
  -H "Authorization: Bearer $ACCESS" -H "Content-Type: application/json" \
  -d "{\"meter_id\":\"$METER_ID\",\"amount\":\"5000\",\"phone_number\":\"$PHONE\"}")
TXN_ID=$(echo "$INIT" | python3 -c "import sys,json;print(json.load(sys.stdin)['id'])")
ORDER_ID=$(echo "$INIT" | python3 -c "import sys,json;print(json.load(sys.stdin)['provider_reference'])")
REF=$(echo "$INIT" | python3 -c "import sys,json;print(json.load(sys.stdin)['control_number'])")
echo "Selcom reference: $REF   (provider order_id: $ORDER_ID)"

# 5. Webhook — Swahilies echoes our order_id back. No HMAC, any POST succeeds.
curl -s -X POST "$API/webhooks/payment/" \
  -H "Content-Type: application/json" \
  -d "{\"transaction_details\":{\"order_id\":\"$ORDER_ID\"}}"
echo

# 6. Confirm token visible to owner
curl -s "$API/transactions/$TXN_ID/" -H "Authorization: Bearer $ACCESS"
echo
```

You should see `status: "paid"` and a non-empty `token.value`. The `runserver` console will log the SMS line from `ConsoleSmsProvider`.

## Architecture seams

- `payments/providers/` — `swahilies.py` is the real client; `__init__.py` dispatches on `PAYMENT_PROVIDER` (`swahilies` or `fake`). Add a new provider by writing a module with the same `initiate_push(*, order_id, amount, phone_number) -> SwahiliesResponse` shape and extending the dispatcher.
- `payments/token_logic.py` — `TokenStrategy` interface. `SimpleTokenStrategy` is the reversible Arduino/prototype path; `HmacTokenStrategy` (HOTP-style, set `TOKEN_STRATEGY=hmac`) is production-grade.
- `payments/sms.py` — `SmsProvider` interface. `ConsoleSmsProvider` is the dev default; `MalipoPaySmsProvider` (set `SMS_PROVIDER=malipopay`) does the real send with 3-attempt backoff.
- `payments/views.py:PaymentWebhookView` — accepts any POST shaped as `{transaction_details: {order_id}}`; treats arrival as success per Swahilies' contract.
