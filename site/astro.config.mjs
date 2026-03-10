import { defineConfig } from 'astro/config';

export default defineConfig({
  site: 'https://openlegalcommentary.ch',
  base: '/openlegalcommentary',
  output: 'static',
  build: {
    format: 'directory',
  },
  vite: {
    server: {
      fs: {
        allow: ['..'],
      },
    },
  },
});
