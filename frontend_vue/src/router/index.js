import { createRouter, createWebHistory } from 'vue-router';
import CharactersView from '../views/CharactersView.vue';
import DungeonView from '../views/DungeonView.vue';
import LoginView from '../views/LoginView.vue';
import SettingsView from '../views/SettingsView.vue';
import StoryView from '../views/StoryView.vue';
import WorldbookView from '../views/WorldbookView.vue';

const routes = [
  {
    path: '/login',
    alias: '/login.html',
    name: 'login',
    component: LoginView,
    meta: { noShell: true },
  },
  {
    path: '/',
    alias: '/index.html',
    name: 'story-root',
    component: StoryView,
  },
  {
    path: '/story',
    name: 'story',
    component: StoryView,
  },
  {
    path: '/characters',
    alias: '/characters.html',
    name: 'characters',
    component: CharactersView,
  },
  {
    path: '/worldbook',
    alias: '/worldbook.html',
    name: 'worldbook',
    component: WorldbookView,
  },
  {
    path: '/dungeon',
    alias: '/dungeon.html',
    name: 'dungeon',
    component: DungeonView,
  },
  {
    path: '/settings',
    alias: '/settings.html',
    name: 'settings',
    component: SettingsView,
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
