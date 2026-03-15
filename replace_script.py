import re
with open(r'frontend_vue\src\styles\legacy.css', 'r', encoding='utf-8') as f:
    css = f.read()

pattern = r'\[data-theme="cyberpunk"\].*?\[data-theme="royal"\] \{.*?\n\}'
replacement = '''[data-theme="cyber"] {
  --bg-main: #05050A;
  --bg-elevated: rgba(14, 15, 25, 0.8);
  --bg-elevated-alt: rgba(20, 22, 35, 0.85);
  --border-soft: rgba(6, 182, 212, 0.15);
  --text-primary: #E2E8F0;
  --text-secondary: #64748B;
  --accent: #06B6D4;
  --accent-soft: rgba(6, 182, 212, 0.2);
  --danger: #F43F5E;
  --shadow-soft: 0 0 12px rgba(6, 182, 212, 0.2);
  --scrollbar-bg: #05050A;
  --scrollbar-thumb: rgba(6, 182, 212, 0.3);
}

[data-theme="scroll"] {
  --bg-main: #e6dcc3;
  --bg-elevated: #f4ece0;
  --bg-elevated-alt: #ded3b6;
  --border-soft: rgba(139, 115, 85, 0.15);
  --text-primary: #4b3621;
  --text-secondary: #8b7355;
  --accent: #a0522d;
  --accent-soft: rgba(160, 82, 45, 0.15);
  --danger: #800000;
  --shadow-soft: 0 8px 24px rgba(139, 115, 85, 0.15);
}

[data-theme="ink"] {
  --bg-main: #0D1117;
  --bg-elevated: rgba(22, 27, 34, 0.75);
  --bg-elevated-alt: rgba(31, 41, 55, 0.8);
  --border-soft: rgba(255, 255, 255, 0.05);
  --text-primary: #F8FAFC;
  --text-secondary: #94A3B8;
  --accent: #3B82F6;
  --accent-soft: rgba(59, 130, 246, 0.15);
  --danger: #EF4444;
  --shadow-soft: 0 12px 32px rgba(0, 0, 0, 0.4);
  --scrollbar-bg: #0D1117;
  --scrollbar-thumb: #1F2937;
}

[data-theme="snow"] {
  --bg-main: #F8F9FA;
  --bg-elevated: #FFFFFF;
  --bg-elevated-alt: #F1F5F9;
  --border-soft: rgba(15, 23, 42, 0.06);
  --text-primary: #0F172A;
  --text-secondary: #64748B;
  --accent: #2563EB;
  --accent-soft: rgba(37, 99, 235, 0.1);
  --danger: #DC2626;
  --shadow-soft: 0 10px 30px rgba(15, 23, 42, 0.06);
  --scrollbar-bg: #F8F9FA;
  --scrollbar-thumb: #CBD5E1;
}

[data-theme="mist"] {
  --bg-main: #1C1F26;
  --bg-elevated: rgba(40, 44, 52, 0.85);
  --bg-elevated-alt: rgba(55, 65, 81, 0.85);
  --border-soft: rgba(255, 255, 255, 0.06);
  --text-primary: #E2E8F0;
  --text-secondary: #94A3B8;
  --accent: #60A5FA;
  --accent-soft: rgba(96, 165, 250, 0.15);
  --danger: #F87171;
  --shadow-soft: 0 10px 30px rgba(0, 0, 0, 0.3);
  --scrollbar-bg: #1C1F26;
  --scrollbar-thumb: #374151;
}

[data-theme="abyss"] {
  --bg-main: #0A090C;
  --bg-elevated: #151115;
  --bg-elevated-alt: #1A151A;
  --border-soft: rgba(153, 27, 27, 0.2);
  --text-primary: #F3F4F6;
  --text-secondary: #9CA3AF;
  --accent: #991B1B;
  --accent-soft: rgba(153, 27, 27, 0.15);
  --danger: #DC2626;
  --shadow-soft: 0 12px 36px rgba(153, 27, 27, 0.15);
  --scrollbar-bg: #0A090C;
  --scrollbar-thumb: #3F1D1D;
}

[data-theme="forest"] {
  --bg-main: #0A110D;
  --bg-elevated: #111C15;
  --bg-elevated-alt: #16261C;
  --border-soft: rgba(212, 175, 55, 0.15);
  --text-primary: #F3F4F6;
  --text-secondary: #A7F3D0;
  --accent: #D4AF37;
  --accent-soft: rgba(212, 175, 55, 0.15);
  --danger: #F87171;
  --shadow-soft: 0 10px 30px rgba(0, 0, 0, 0.4);
  --scrollbar-bg: #0A110D;
  --scrollbar-thumb: #16261C;
}'''

new_css = re.sub(pattern, replacement, css, flags=re.DOTALL)
with open(r'frontend_vue\src\styles\legacy.css', 'w', encoding='utf-8') as f:
    f.write(new_css)
