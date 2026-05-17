const API = process.env.DJANGO_API_URL ?? "http://127.0.0.1:8000/api";

export async function fireWebhook(orderId: string): Promise<void> {
  const body = JSON.stringify({ transaction_details: { order_id: orderId } });
  const resp = await fetch(`${API}/webhooks/payment/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body,
  });
  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(`Webhook returned ${resp.status}: ${text}`);
  }
}

export async function fetchTransactionOrderId(
  txnId: string,
  access: string,
): Promise<string> {
  const resp = await fetch(`${API}/transactions/${txnId}/`, {
    headers: { Authorization: `Bearer ${access}` },
  });
  if (!resp.ok) {
    throw new Error(`GET /transactions/${txnId}/ → ${resp.status}`);
  }
  const data = (await resp.json()) as { provider_reference: string };
  return data.provider_reference;
}
