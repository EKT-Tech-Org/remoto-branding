import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "tests/e2e",
  timeout: 60_000,
  retries: 1,
  reporter: [["list"], ["html", { open: "never" }]],
  use: {
    baseURL: process.env.HA_URL || "http://localhost:8123",
    screenshot: "on",
    trace: "retain-on-failure",
  },
});
