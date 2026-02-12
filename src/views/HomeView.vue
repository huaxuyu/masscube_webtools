<script setup>
import { RouterLink } from 'vue-router';

const tools = [
  {
    title: 'Aligned Feature Table Viewer',
    subtitle: 'Explore complete feature tables with filtering, sorting, and per-feature visual diagnostics.',
    route: '/feature-browser',
    accent: 'blue',
  },
  {
    title: 'Peak Shape Viewer',
    subtitle: 'Inspect RT-intensity traces quickly and export publication-ready peak figures.',
    route: '/peak-shape',
    accent: 'sand',
  },
  {
    title: 'MS/MS Viewer',
    subtitle: 'Generate mirror plots and compute tolerance-based cosine similarity in one step.',
    route: '/msms-viewer',
    accent: 'mint',
  },
];
</script>

<template>
  <section class="view-shell home-view">
    <div class="hero">
      <h1 class="page-title">Metabolomics analysis tools for focused, reliable interpretation.</h1>
    </div>

    <div class="tool-grid" role="list" aria-label="Available tools">
      <RouterLink
        v-for="(tool, idx) in tools"
        :key="tool.route"
        :to="tool.route"
        class="tool-card panel"
        :style="{ '--card-delay': `${idx * 80}ms` }"
        :data-accent="tool.accent"
        role="listitem"
        :aria-label="`Open ${tool.title}`"
      >
        <div class="panel-body card-body">
          <div class="card-head">
            <p class="card-index">0{{ idx + 1 }}</p>
            <h2>{{ tool.title }}</h2>
          </div>
          <p>{{ tool.subtitle }}</p>
        </div>
      </RouterLink>
    </div>
  </section>
</template>

<style scoped>
.home-view {
  display: grid;
  gap: 24px;
}

.hero {
  max-width: 860px;
  padding: clamp(18px, 2.8vw, 28px) 6px 4px;
}

.tool-grid {
  display: grid;
  gap: 16px;
  margin-top: 24px;
  grid-template-columns: repeat(12, minmax(0, 1fr));
}

.tool-card {
  display: block;
  grid-column: span 4;
  position: relative;
  cursor: pointer;
  opacity: 0;
  transform: translateY(16px);
  transition: transform var(--ease), box-shadow var(--ease), border-color var(--ease);
  animation: cardIn 640ms cubic-bezier(0.2, 0.85, 0.22, 1) forwards;
  animation-delay: var(--card-delay);
}

.tool-card:hover {
  transform: translateY(-2px);
  border-color: color-mix(in srgb, var(--accent) 30%, #d1d5db);
  box-shadow: 0 20px 30px -24px rgba(15, 23, 42, 0.8);
}

.tool-card::before {
  content: '';
  position: absolute;
  inset: 0;
  opacity: 0.6;
  pointer-events: none;
  border-radius: inherit;
}

.tool-card[data-accent='blue']::before {
  background: linear-gradient(140deg, rgba(0, 113, 227, 0.16), rgba(0, 113, 227, 0.03) 62%);
}

.tool-card[data-accent='sand']::before {
  background: linear-gradient(140deg, rgba(217, 119, 6, 0.16), rgba(217, 119, 6, 0.03) 62%);
}

.tool-card[data-accent='mint']::before {
  background: linear-gradient(140deg, rgba(15, 157, 106, 0.15), rgba(15, 157, 106, 0.03) 62%);
}

.card-body {
  display: grid;
  gap: 14px;
  min-height: 244px;
}

.card-head {
  display: flex;
  align-items: baseline;
  gap: 10px;
}

.card-index {
  margin: 0;
  font-family: Arial, Helvetica, sans-serif;
  font-size: 1.32rem;
  font-weight: 800;
  line-height: 1;
  color: var(--text-primary);
}

h2 {
  margin: 0;
  font-family: Arial, Helvetica, sans-serif;
  font-size: 1.28rem;
  line-height: 1.25;
}

.card-body > p {
  margin: 0;
  color: var(--text-secondary);
  line-height: 1.65;
}

@media (max-width: 1150px) {
  .tool-card {
    grid-column: span 6;
  }
}

@media (max-width: 700px) {
  .tool-grid {
    margin-top: 16px;
  }

  .tool-card {
    grid-column: span 12;
  }

  .card-body {
    min-height: 220px;
  }
}

@keyframes cardIn {
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
