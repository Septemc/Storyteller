"""
测试 get_current_user_sync 函数
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from backend.db.base import SessionLocal
from backend.db import models
from backend.core.auth import create_access_token, decode_token, get_user_by_id, get_user_by_user_id, get_current_user_sync
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

# 模拟 OAuth2PasswordBearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

def test_get_current_user_sync():
    """测试 get_current_user_sync 函数"""
    print("=" * 60)
    print("测试 get_current_user_sync 函数")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        # 1. 获取测试用户
        user = db.query(models.User).first()
        if not user:
            print("❌ 数据库中没有用户")
            return
        
        print(f"\n测试用户: {user.username}")
        print(f"  - id (主键): {user.id}")
        print(f"  - user_id (字符串): {user.user_id}")
        
        # 2. 创建 token - 使用 user.user_id (字符串)
        token = create_access_token({"sub": user.user_id})
        print(f"\n创建的 token (sub=user.user_id): {token[:50]}...")
        
        # 3. 测试 decode_token
        payload = decode_token(token)
        print(f"\n1. decode_token 结果: {payload}")
        
        if payload:
            user_id = payload.get("sub")
            print(f"2. 从 payload 获取 user_id: {user_id} (type: {type(user_id).__name__})")
            
            # 4. 测试 get_user_by_user_id (字符串)
            found_user = get_user_by_user_id(db, user_id)
            print(f"3. get_user_by_user_id 结果: {found_user}")
            
            if found_user:
                print(f"\n✅ 用户查找成功!")
                print(f"   - 用户 ID: {found_user.id}")
                print(f"   - 用户名: {found_user.username}")
                print(f"   - user_id: {found_user.user_id}")
                
                # 5. 模拟 get_current_user_sync 的逻辑
                print("\n" + "-" * 40)
                print("模拟 get_current_user_sync 逻辑:")
                print("-" * 40)
                
                # 直接调用函数（不通过 Depends）
                result = simulate_get_current_user_sync(token, db)
                print(f"\n模拟调用结果: {result}")
                
                if result:
                    print(f"✅ 成功获取用户: {result.username}, user_id: {result.user_id}")
                else:
                    print("❌ 模拟调用失败")
            else:
                print(f"❌ 未找到用户 user_id={user_id}")
        else:
            print("❌ Token 解码失败")
            
    finally:
        db.close()

def simulate_get_current_user_sync(token, db):
    """模拟 get_current_user_sync 函数逻辑"""
    print(f"  - 输入 token: {token[:30]}...")
    
    if not token:
        print("  - No token provided")
        return None
    
    payload = decode_token(token)
    print(f"  - decode_token: {payload}")
    
    if not payload:
        print("  - Token decode failed")
        return None
    
    user_id = payload.get("sub")
    print(f"  - user_id from token: {user_id} (type: {type(user_id).__name__})")
    
    if user_id is None:
        print("  - No user_id in payload")
        return None
    
    # 根据类型选择查找方式
    if isinstance(user_id, str):
        user = get_user_by_user_id(db, user_id)
        print(f"  - lookup by user_id (string): {user_id}")
    else:
        user = get_user_by_id(db, user_id)
        print(f"  - lookup by id (int): {user_id}")
    
    print(f"  - user from DB: {user.username if user else 'None'}")
    
    return user

def test_with_mock_request():
    """模拟完整的请求流程"""
    print("\n" + "=" * 60)
    print("模拟完整请求流程")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        user = db.query(models.User).first()
        if not user:
            print("❌ 数据库中没有用户")
            return
        
        # 创建 token - 使用 user.user_id (字符串)
        token = create_access_token({"sub": user.user_id})
        
        # 模拟请求头
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        print(f"\n模拟请求:")
        print(f"  - Headers: Authorization: Bearer {token[:30]}...")
        
        # 提取 token（模拟 OAuth2PasswordBearer）
        auth_header = headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            extracted_token = auth_header[7:]  # 移除 "Bearer " 前缀
            print(f"  - 提取的 token: {extracted_token[:30]}...")
            
            # 调用模拟函数
            result = simulate_get_current_user_sync(extracted_token, db)
            
            if result:
                print(f"\n✅ 认证成功!")
                print(f"   - 用户: {result.username}")
                print(f"   - user_id: {result.user_id}")
            else:
                print("\n❌ 认证失败")
        else:
            print("❌ 无效的 Authorization header")
            
    finally:
        db.close()

if __name__ == "__main__":
    test_get_current_user_sync()
    test_with_mock_request()
    print("\n" + "=" * 60)
    print("测试完成")
