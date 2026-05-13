import { expect, test } from "@playwright/test";

import { fireWebhook } from "./lib/fire-webhook";

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
  await page.getByLabel("Amount (TZS)").fill("5000");
  await page.getByRole("button", { name: "Pay" }).click();

  // 5. Land on /transactions/{id} with pending state
  await page.waitForURL(/\/transactions\/[0-9a-f-]{36}/);
  await expect(page.getByText("Waiting for payment...")).toBeVisible();

  // Capture the control number from the page (12-digit, 99-prefixed)
  const controlNumber = await page
    .locator("p.font-mono")
    .filter({ hasText: /^99\d{10}$/ })
    .first()
    .innerText();
  expect(controlNumber).toMatch(/^99\d{10}$/);

  // 6. Fire the webhook side-channel
  await fireWebhook(controlNumber, "5000");

  // 7. Page should swap to paid within polling interval (2s) + a bit of slack
  await expect(page.getByText("✓ Payment received")).toBeVisible({ timeout: 10_000 });
  const tokenValue = await page.locator("p.text-3xl.font-mono").innerText();
  expect(tokenValue).toMatch(/^\d+$/);
  expect(tokenValue.length).toBeGreaterThanOrEqual(7);
});
