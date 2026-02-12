<script setup>
import { computed } from 'vue';
import { RouterLink, RouterView, useRoute } from 'vue-router';

const route = useRoute();

const isHome = computed(() => route.path === '/');
</script>

<template>
  <div class="app-shell">
    <div class="ambient-layer" aria-hidden="true">
      <div class="orb orb-a"></div>
      <div class="orb orb-b"></div>
      <div class="orb orb-c"></div>
    </div>

    <header class="top-nav">
      <RouterLink class="brand" to="/">
        <span class="brand-text">MassCube Web Tools</span>
      </RouterLink>

      <a
        class="header-link"
        href="https://huaxuyu.github.io/masscubedocs/"
        target="_blank"
        rel="noopener noreferrer"
      >
        MassCube Website
      </a>
    </header>

    <main class="page-container" :class="{ compact: !isHome }">
      <RouterView v-slot="{ Component, route: activeRoute }">
        <Transition name="page-fade" mode="out-in">
          <component :is="Component" :key="activeRoute.fullPath" />
        </Transition>
      </RouterView>
    </main>
  </div>
</template>
