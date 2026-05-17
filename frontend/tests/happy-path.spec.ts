import { expect, test } from "@playwright/test";

import { fetchTransactionOrderId, fireWebhook } from "./lib/fire-webhook";

// NOTE: requires the Django dev server running with PAYMENT_PROVIDER=fake.
// Without that, InitiatePaymentView will try to reach the real Swahilies API.

function randomSuffix(n: number): string {
  return Math.floor(Math.random() * 10 ** n)
    .toString()
    .padStart(n, "0");
}

test("happy path: register → add meter → buy → webhook → paid", async ({ page }) => {
  const phone = `+25570009${randomSuffix(4)}`;
  const password = "test-pw-12345";
  const meterNumber = `01000${randomSuffix(5)}`;

  // 1. Register
  await page.goto("/register");
  await page.getByLabel("Phone number").fill(phone);
  await page.getByLabel("Password").fill(password);
  await page.getByRole("button", { name: "Register" }).click();

  // 2. Land on /buy (no meters yet)
  await page.waitForURL("/buy");
  await expect(page.getByText("No meters yet")).toBeVisible();

  // 3. Add a meter
  await page.getByRole("link", { name: "Add a meter first" }).click();
  await page.waitForURL("/meters");
  await page.getByLabel("Meter number").fill(meterNumber);
  await page.getByLabel("Label (optional)").fill("E2E test meter");
  await page.getByRole("button", { name: "Add meter" }).click();
  await expect(page.getByText(meterNumber)).toBeVisible();

  // 4. Initiate a transaction
  await page.getByRole("link", { name: "Buy" }).first().click();
  await page.waitForURL("/buy");
  await page.getByRole("combobox").click();
  await page.getByRole("option", { name: new RegExp(meterNumber) }).click();
  await page.getByLabel("Amount").fill("5000");
  // Phone field is prefilled from the logged-in user, but type it explicitly to be safe.
  await page.getByLabel("Phone for payment").fill(phone);
  await page.getByRole("button", { name: "Pay" }).click();

  // 5. Land on /transactions/{id} with the pending state ("check your phone")
  await page.waitForURL(/\/transactions\/[0-9a-f-]{36}/);
  await expect(page.getByText("Check your phone")).toBeVisible();

  // Pull the txn id from the URL, then fetch its provider_reference (order_id) via the API.
  const url = new URL(page.url());
  const txnId = url.pathname.split("/").filter(Boolean).pop()!;
  const access = await page.evaluate(() => localStorage.getItem("daraja.access") ?? "");
  expect(access).not.toBe("");
  const orderId = await fetchTransactionOrderId(txnId, access);

  // 6. Fire the webhook side-channel keyed on the order_id Swahilies would echo back.
  await fireWebhook(orderId);

  // 7. Page should swap to paid within polling interval (2s) + a bit of slack
  await expect(page.getByText("Payment received")).toBeVisible({ timeout: 10_000 });
  const tokenValue = await page.locator("p.font-mono.text-4xl").innerText();
  expect(tokenValue).toMatch(/^\d+$/);
  expect(tokenValue.length).toBeGreaterThanOrEqual(7);
});
