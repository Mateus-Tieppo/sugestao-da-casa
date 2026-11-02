import { defineConfig, devices } from "@playwright/test";

const PORTA = 3100;
const URL_BASE = `http://localhost:${PORTA}`;

// Só o Chromium está instalado: o perfil do iPhone 13 roda nele, não no WebKit.
const { defaultBrowserType: _navegador, ...iphone13 } = devices["iPhone 13"];

export default defineConfig({
  testDir: "./tests/e2e",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: 0,
  reporter: [["list"]],
  use: {
    baseURL: URL_BASE,
    trace: "retain-on-failure",
    locale: "pt-BR",
  },
  projects: [
    {
      name: "desktop",
      use: { ...devices["Desktop Chrome"], viewport: { width: 1440, height: 900 } },
    },
    {
      name: "mobile",
      use: { ...iphone13 },
    },
  ],
  webServer: {
    command: `npm run build && npx next start -p ${PORTA}`,
    url: URL_BASE,
    reuseExistingServer: true,
    timeout: 240_000,
  },
});
