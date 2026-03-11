<template>
  <div class="shell">
    <AppTopNav />
    <slot />
  </div>
</template>

<script setup>
import { onMounted } from 'vue';
import AppTopNav from '../components/AppTopNav.vue';
import { useSessionStore } from '../stores/session';
import { useSaveManagerStore } from '../stores/saveManager';

const sessionStore = useSessionStore();
const saveStore = useSaveManagerStore();

onMounted(() => {
  sessionStore.bootstrap();
  saveStore.syncCurrentSession();
});
</script>

<style scoped>
.shell {
  min-height: 100vh;
}
</style>
