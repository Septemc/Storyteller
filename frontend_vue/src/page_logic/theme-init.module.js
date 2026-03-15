export const DEFAULT_THEME = 'scroll';
export const DEFAULT_BACKGROUND = 'paper';

const FONT_CONFIG = [
  { storage: 'app_font_ui_family', css: '--font-ui-family' },
  { storage: 'app_font_ui_size', css: '--font-ui-size' },
  { storage: 'app_font_story_family', css: '--font-story-family' },
  { storage: 'app_font_story_size', css: '--font-story-size' },
  { storage: 'app_font_console_family', css: '--font-console-family' },
  { storage: 'app_font_console_size', css: '--font-console-size' },
  { storage: 'app_font_char_family', css: '--font-char-family' },
  { storage: 'app_font_char_size', css: '--font-char-size' },
  { storage: 'app_font_world_family', css: '--font-world-family' },
  { storage: 'app_font_world_size', css: '--font-world-size' },
  { storage: 'app_font_dungeon_family', css: '--font-dungeon-family' },
  { storage: 'app_font_dungeon_size', css: '--font-dungeon-size' },
];

export const THEME_OPTIONS = [
  { value: 'scroll', label: '羊皮卷轴', description: '暖米色与棕色描边，保持古典叙事的沉浸感。', preview: 'linear-gradient(135deg, #f4ece0 0%, #e6dcc3 58%, #ded3b6 100%)', chips: ['#f4ece0', '#c2b280', '#a0522d'] },
  { value: 'ink', label: '墨夜黑蓝', description: '沉静通透的深空蓝灰，富有太空控制台的现代感。', preview: 'linear-gradient(135deg, #0D1117 0%, #161B22 62%, #1F2937 100%)', chips: ['#0D1117', '#161B22', '#3B82F6'] },
  { value: 'snow', label: '雪纸白蓝', description: '纯净微悬浮白，极简现代的北欧风格。', preview: 'linear-gradient(135deg, #F8F9FA 0%, #FFFFFF 58%, #E2E8F0 100%)', chips: ['#F8F9FA', '#FFFFFF', '#2563EB'] },
  { value: 'mist', label: '雾灰蓝影', description: '被浓雾包裹的阴冷灰底，适合悬疑与电影感叙事。', preview: 'linear-gradient(135deg, #1C1F26 0%, #282C34 52%, #3F4A5E 100%)', chips: ['#1C1F26', '#282C34', '#60A5FA'] },
  { value: 'abyss', label: '深渊暗红', description: '暗黑系紫红交织，适合克苏鲁与诡秘剧本。', preview: 'linear-gradient(135deg, #0A090C 0%, #151115 58%, #2B1818 100%)', chips: ['#0A090C', '#151115', '#991B1B'] },
  { value: 'cyber', label: '霓虹赛博', description: '极客青蓝搭配午夜黑，低光污染废土未来感。', preview: 'linear-gradient(135deg, #05050A 0%, #0E0F19 62%, #192534 100%)', chips: ['#05050A', '#0E0F19', '#06B6D4'] },
  { value: 'forest', label: '秘林幽影', description: '深邃的苔藓黑绿配以暗金高光，适配西幻设定。', preview: 'linear-gradient(135deg, #0A110D 0%, #111C15 58%, #1D3124 100%)', chips: ['#0A110D', '#111C15', '#D4AF37'] },
];

export const BACKGROUND_OPTIONS = [
  { value: 'paper', label: '羊皮纸纹', description: '保留纸张纤维感，适配卷轴主题。', preview: 'linear-gradient(180deg, rgba(255,255,255,0.32), rgba(0,0,0,0.04)), repeating-linear-gradient(90deg, rgba(120,92,56,0.10) 0 1px, transparent 1px 24px)' },
  { value: 'plain', label: '纯净留白', description: '完全简洁，没有附加纹理。', preview: 'linear-gradient(135deg, rgba(255,255,255,0.28), rgba(255,255,255,0.06))' },
  { value: 'grid-soft', label: '细线网格', description: '轻量规整的阅读辅助线。', preview: 'linear-gradient(rgba(110,130,160,0.14) 1px, transparent 1px), linear-gradient(90deg, rgba(110,130,160,0.14) 1px, transparent 1px)' },
  { value: 'dots-soft', label: '微点肌理', description: '柔和颗粒点阵，减少单调感。', preview: 'radial-gradient(circle at 1px 1px, rgba(100,120,150,0.22) 1px, transparent 1.2px)' },
  { value: 'blueprint', label: '蓝线图纸', description: '很淡的蓝线与角标感。', preview: 'linear-gradient(rgba(96,140,210,0.12) 1px, transparent 1px), linear-gradient(90deg, rgba(96,140,210,0.12) 1px, transparent 1px), linear-gradient(135deg, rgba(96,140,210,0.08), transparent 70%)' },
];

function safeLocalStorageGet(key, fallback) {
  try { return localStorage.getItem(key) || fallback; } catch { return fallback; }
}

function safeLocalStorageSet(key, value) {
  try { localStorage.setItem(key, value); } catch {}
}

function applyFonts() {
  const rootStyle = document.documentElement.style;
  FONT_CONFIG.forEach((item) => {
    const savedVal = safeLocalStorageGet(item.storage, '');
    if (savedVal) rootStyle.setProperty(item.css, savedVal);
  });
}

export function applyThemeSettings({ theme, background } = {}) {
  const nextTheme = theme || safeLocalStorageGet('app_theme', DEFAULT_THEME);
  const nextBackground = background || safeLocalStorageGet('app_bg', DEFAULT_BACKGROUND);
  safeLocalStorageSet('app_theme', nextTheme);
  safeLocalStorageSet('app_bg', nextBackground);
  document.documentElement.setAttribute('data-theme', nextTheme);
  if (document.body) {
    document.body.className = document.body.className.replace(/\bbg-\S+/g, '').trim();
    document.body.classList.add(`bg-${nextBackground}`);
  }
}

export function initThemePage() {
  applyFonts();
  applyThemeSettings();
}
