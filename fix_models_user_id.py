#!/usr/bin/env python3
"""
批量修改 models.py 中的 user_id 字段定义
"""

import re

def fix_models():
    """修改 models.py 中的 user_id 字段定义"""
    
    print("🔧 修改 models.py 中的 user_id 字段定义")
    print("=" * 60)
    
    file_path = "backend/db/models.py"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 替换所有 user_id 字段定义
    # 从: user_id = Column(Integer, ForeignKey("users.id"), ...)
    # 到: user_id = Column(String(32), ForeignKey("users.user_id"), ...)
    
    pattern = r'user_id = Column\(Integer, ForeignKey\("users\.id"\)'
    replacement = r'user_id = Column(String(32), ForeignKey("users.user_id")'
    
    new_content = re.sub(pattern, replacement, content)
    
    # 保存修改
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ 修改完成")
    
    # 显示修改的内容
    print("\n修改的字段：")
    matches = re.findall(r'user_id = Column\(String\(32\), ForeignKey\("users\.user_id"\).*?\)', new_content)
    for match in matches:
        print(f"  {match}")

if __name__ == "__main__":
    fix_models()
