#!/usr/bin/env python3
"""
检查并修改所有路由文件中的 user.id 使用
"""

import os
import re

def fix_routes():
    """修改所有路由文件中的 user.id 使用"""
    
    print("🔧 检查并修改所有路由文件中的 user.id 使用")
    print("=" * 60)
    
    routes_dir = "backend/api"
    route_files = [
        "routes_story.py",
        "routes_presets.py",
        "routes_llm.py",
        "routes_regex.py",
        "routes_characters.py",
        "routes_worldbook.py",
        "routes_settings.py",
        "routes_dungeon.py",
        "routes_auth.py",
        "routes_templates.py"
    ]
    
    for route_file in route_files:
        file_path = os.path.join(routes_dir, route_file)
        
        if not os.path.exists(file_path):
            print(f"\n⚠️  文件不存在: {file_path}")
            continue
        
        print(f"\n检查文件: {route_file}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 查找所有使用 user.id 或 current_user.id 的地方
        matches = re.findall(r'(current_user|user)\.id', content)
        
        if matches:
            print(f"  找到 {len(matches)} 处使用 .id 的地方")
            
            # 替换为 .user_id
            new_content = re.sub(r'(current_user|user)\.id', r'\1.user_id', content)
            
            # 保存修改
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print(f"  ✅ 已修改")
        else:
            print(f"  ℹ️  未找到需要修改的地方")

if __name__ == "__main__":
    fix_routes()
