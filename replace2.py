import re
with open(r'frontend_vue\src\styles\legacy.css', 'r', encoding='utf-8') as f:
    css = f.read()

pattern = r'(\.story-panel, \.side-panel, \.settings-panel, \.left-panel, \.right-panel,\s*\n\s*\.modal-window, \.settings-sidebar, \.settings-content-area \{)(.*?)(\s*\})'

def repl(m):
    # m.group(2) contains the inner styles. Let's make sure we don't duplicate if already there
    inner = m.group(2)
    if 'backdrop-filter' in inner:
        return m.group(0)
    return m.group(1) + inner + "\n  backdrop-filter: blur(16px);\n  -webkit-backdrop-filter: blur(16px);\n  transition: border-color 0.3s ease, box-shadow 0.3s ease, background-color 0.3s ease;" + m.group(3)

new_css = re.sub(pattern, repl, css, flags=re.DOTALL)
if new_css != css:
    with open(r'frontend_vue\src\styles\legacy.css', 'w', encoding='utf-8') as f:
        f.write(new_css)
    print("Updated panel styles")
else:
    print("Pattern not found or already modified")
