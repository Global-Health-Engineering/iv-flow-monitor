import { defineConfig } from 'astro/config';

// Adjust `site` and `base` for your deployment target.
// GitHub Pages defaults: site = `https://<user>.github.io`, base = `/<repo>`.
// For a custom domain or root deploy, set base: '/' and site to the canonical URL.
export default defineConfig({
  site: 'https://gluflex.github.io',
  base: '/iv-flow-monitor-v2',
  build: {
    assets: '_astro',
  },
});
