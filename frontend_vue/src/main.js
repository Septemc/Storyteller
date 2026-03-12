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
authStore.bootstrap();

async function bootstrapApp() {
  if (authStore.token) {
    await authStore.fetchMe();
  }
  app.mount('#app');
}

bootstrapApp();
