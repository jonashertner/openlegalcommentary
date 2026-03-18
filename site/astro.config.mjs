import { defineConfig } from 'astro/config';

export default defineConfig({
  site: 'https://openlegalcommentary.ch',
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
    build: {
      rollupOptions: {
        external: ['/pagefind/pagefind.js'],
      },
    },
  },
});
