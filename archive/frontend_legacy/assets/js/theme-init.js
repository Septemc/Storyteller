/**
 * assets/js/theme-init.js
 * 负责在页面加载最早期读取 LocalStorage 并应用主题、背景、字体配置。
 * 必须放在 <head> 中引用。
 */
(function() {
  // === 1. 定义字体映射配置 (与 settings.js 保持一致) ===
  // Key: LocalStorage Key, Var: CSS Variable Name
  const FONT_CONFIG = [
    { storage: 'app_font_ui_family',      css: '--font-ui-family' },
    { storage: 'app_font_ui_size',        css: '--font-ui-size' },
    { storage: 'app_font_story_family',   css: '--font-story-family' },
    { storage: 'app_font_story_size',     css: '--font-story-size' },
    { storage: 'app_font_console_family', css: '--font-console-family' },
    { storage: 'app_font_console_size',   css: '--font-console-size' },
    { storage: 'app_font_char_family',    css: '--font-char-family' },
    { storage: 'app_font_char_size',      css: '--font-char-size' },
    { storage: 'app_font_world_family',   css: '--font-world-family' },
    { storage: 'app_font_world_size',     css: '--font-world-size' },
    { storage: 'app_font_dungeon_family', css: '--font-dungeon-family' },
    { storage: 'app_font_dungeon_size',   css: '--font-dungeon-size' }
  ];

  // === 2. 读取并应用主题 (Theme) ===
  const savedTheme = localStorage.getItem('app_theme') || 'dark';
  document.documentElement.setAttribute('data-theme', savedTheme);

  // === 3. 读取并应用字体 (Typography) ===
  const rootStyle = document.documentElement.style;
  FONT_CONFIG.forEach(item => {
    const savedVal = localStorage.getItem(item.storage);
    if (savedVal) {
      rootStyle.setProperty(item.css, savedVal);
    }
  });

  // === 4. 读取并应用背景纹理 (Background) ===
  // 注意：背景类加在 body 上，必须等待 DOM 解析或使用 DOMContentLoaded
  // 为防闪烁，这里建议保留监听逻辑
  const savedBg = localStorage.getItem('app_bg') || 'grid';

  function applyBg() {
    // 移除旧的 bg- 类
    document.body.className = document.body.className.replace(/\bbg-\S+/g, '').trim();
    // 添加新的 bg- 类
    document.body.classList.add('bg-' + savedBg);
  }

  if (document.body) {
    applyBg();
  } else {
    document.addEventListener('DOMContentLoaded', applyBg);
  }
})();