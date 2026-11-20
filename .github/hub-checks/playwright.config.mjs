import { defineConfig } from '@playwright/test';

const baseURL = 'http://127.0.0.1:4173';

export default defineConfig({
  testDir: '.',
  use: { baseURL, colorScheme: 'light' },
  webServer: {
    command: 'python3 -m http.server 4173 --bind 127.0.0.1 --directory ../..',
    url: baseURL,
  },
});
