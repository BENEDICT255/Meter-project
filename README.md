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

This bash snippet exercises the full happy path. Run with the dev server on port 8000.

```bash
set -e

API=http://127.0.0.1:8000/api
PHONE="+255700000777"
PASSWORD="pw-sanity-1234"
WEBHOOK_SECRET="dev-webhook-secret-change-me"  # match your .env

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

# 4. Initiate
INIT=$(curl -s -X POST "$API/transactions/initiate/" \
  -H "Authorization: Bearer $ACCESS" -H "Content-Type: application/json" \
  -d "{\"meter_id\":\"$METER_ID\",\"amount\":\"5000\"}")
CN=$(echo "$INIT" | python3 -c "import sys,json;print(json.load(sys.stdin)['control_number'])")
TXN_ID=$(echo "$INIT" | python3 -c "import sys,json;print(json.load(sys.stdin)['id'])")
echo "Control number: $CN"

# 5. Webhook with HMAC
BODY=$(printf '{"control_number":"%s","amount":"5000","provider_reference":"sanity-ref","status":"paid"}' "$CN")
SIG=$(python3 -c "import hmac,hashlib,sys;print('sha256='+hmac.new(b'$WEBHOOK_SECRET', b'''$BODY''', hashlib.sha256).hexdigest())")

curl -s -X POST "$API/webhooks/payment/" \
  -H "Content-Type: application/json" -H "X-Signature: $SIG" \
  -d "$BODY"
echo

# 6. Confirm token visible to owner
curl -s "$API/transactions/$TXN_ID/" -H "Authorization: Bearer $ACCESS"
echo
```

You should see `status: "paid"` and a non-empty `token.value`. The `runserver` console will log the SMS line from `ConsoleSmsProvider`.

## Architecture seams (for upcoming work)

- `payments/token_logic.py` — `TokenStrategy` interface. Task 3 adds `HmacTokenStrategy`.
- `payments/sms.py` — `SmsProvider` interface. Task 4 adds Beem / Twilio / Africa's Talking.
- `payments/views.py:PaymentWebhookView` — task 2 updates the payload schema parsing to match the real provider.
