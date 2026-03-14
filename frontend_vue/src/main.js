import { createApp } from 'vue';
import { createPinia } from 'pinia';
import App from './App.vue';
import router from './router';
import { useAuthStore } from './stores/auth';
import './styles/legacy.css';

const app = createApp(App);
const pinia = createPinia();

app.use(pinia);
app.use(router);

const authStore = useAuthStore();
try {
  authStore.bootstrap();
} catch (error) {
  console.error('[bootstrap] auth bootstrap failed', error);
}

async function bootstrapApp() {
  try {
    if (authStore.token) {
      await authStore.fetchMe();
    }
  } catch (error) {
    console.error('[bootstrap] app prefetch failed', error);
  } finally {
    app.mount('#app');
  }
}

bootstrapApp();
