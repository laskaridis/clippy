import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./chrome/e2e",
  timeout: 30_000,
  fullyParallel: false,
  workers: 1,
  reporter: "list",
  use: {
    headless: true,
  },
});
