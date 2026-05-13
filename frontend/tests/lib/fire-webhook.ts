import crypto from "node:crypto";

const API = "http://127.0.0.1:8000/api";
const SECRET = process.env.WEBHOOK_HMAC_SECRET ?? "dev-webhook-secret-change-me";

export async function fireWebhook(controlNumber: string, amount: string): Promise<void> {
  const body = JSON.stringify({
    control_number: controlNumber,
    amount,
    provider_reference: `e2e-${Date.now()}`,
    status: "paid",
  });
  const signature = "sha256=" + crypto.createHmac("sha256", SECRET).update(body).digest("hex");
  const resp = await fetch(`${API}/webhooks/payment/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Signature": signature,
    },
    body,
  });
  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(`Webhook returned ${resp.status}: ${text}`);
  }
}
