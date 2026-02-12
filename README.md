# MassCube Web Tools (Vue)

A Vue 3 + Vite rebuild of MassCube companion web utilities with a unified UI:

- Aligned Feature Table Viewer
- Peak Shape Viewer
- MS/MS Mirror Plot + Cosine Similarity Viewer

## Development

```bash
npm install
npm run dev
```

## Production build

```bash
npm run build
npm run preview
```

## Deployment notes

- This project is configured with `base: './'` in `vite.config.js`.
- Routing uses hash history, so it works on GitHub Pages without server-side rewrites.
