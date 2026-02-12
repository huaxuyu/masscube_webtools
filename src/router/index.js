import { createRouter, createWebHashHistory } from 'vue-router';

const routes = [
  {
    path: '/',
    name: 'home',
    component: () => import('../views/HomeView.vue'),
  },
  {
    path: '/feature-browser',
    name: 'feature-browser',
    component: () => import('../views/FeatureTableView.vue'),
  },
  {
    path: '/peak-shape',
    name: 'peak-shape',
    component: () => import('../views/PeakViewerView.vue'),
  },
  {
    path: '/msms-viewer',
    name: 'msms-viewer',
    component: () => import('../views/CosineSimilarityView.vue'),
  },
];

const router = createRouter({
  history: createWebHashHistory(import.meta.env.BASE_URL),
  routes,
  scrollBehavior() {
    return { top: 0, left: 0, behavior: 'smooth' };
  },
});

export default router;
