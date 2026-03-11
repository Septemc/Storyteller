<template>
  <RouterView v-slot="{ Component }">
    <component :is="Component" v-if="$route.meta.noShell" :key="$route.fullPath" />
    <AppShell v-else :key="$route.fullPath">
      <component :is="Component" />
    </AppShell>
  </RouterView>
</template>

<script setup>
import AppShell from './layouts/AppShell.vue';
</script>
