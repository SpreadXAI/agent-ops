import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  timeout: 60000,
  use: {
    baseURL: process.env.E2E_BASE_URL || 'http://118.31.57.25/agent-ops',
    trace: 'on-first-retry',
  },
})
