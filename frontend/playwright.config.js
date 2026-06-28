import { defineConfig, devices } from '@playwright/test'

/**
 * E2E config for the PharmaGuard dashboard.
 * Boots both the FastAPI backend (port 8000) and the Vite dev server (port 5173)
 * so `npx playwright test` is self-contained. Existing servers are reused if already up.
 */
export default defineConfig({
  testDir: './tests',
  timeout: 30_000,
  expect: { timeout: 15_000 },
  fullyParallel: false,
  reporter: [['list']],
  use: {
    baseURL: 'http://localhost:5173',
    trace: 'on-first-retry',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
  webServer: [
    {
      // Backend streams live CMAPSS predictions over WebSocket.
      command: 'cd ../backend && ../.venv/bin/python -m uvicorn main:app --port 8000',
      url: 'http://localhost:8000/health',
      reuseExistingServer: true,
      timeout: 60_000,
    },
    {
      command: 'npm run dev',
      url: 'http://localhost:5173',
      reuseExistingServer: true,
      timeout: 60_000,
    },
  ],
})
