#!/usr/bin/env python3
"""
修改所有表的 user_id 字段类型，从 INTEGER 改为 VARCHAR(32)
并更新数据，使用 users.user_id 而不是 users.id
"""

import sqlite3

def fix_user_id_fields():
    """修改所有表的 user_id 字段"""
    db_path = "data/db.sqlite"
    
    print("🔧 修改所有表的 user_id 字段")
    print("=" * 60)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 1. 获取 users 表的 id 和 user_id 映射
        print("\n1. 获取用户 ID 映射...")
        cursor.execute("SELECT id, user_id FROM users")
        user_mapping = {row[0]: row[1] for row in cursor.fetchall()}
        print(f"   找到 {len(user_mapping)} 个用户")
        
        # 2. 获取所有包含 user_id 字段的表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = cursor.fetchall()
        
        tables_to_fix = []
        
        for (table_name,) in tables:
            if table_name.startswith("sqlite_") or table_name == "users":
                continue
            
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            for col in columns:
                if col[1] == 'user_id' and col[2] == 'INTEGER':
                    tables_to_fix.append(table_name)
                    break
        
        print(f"\n2. 需要修改的表（共 {len(tables_to_fix)} 个）：")
        for table in tables_to_fix:
            print(f"   - {table}")
        
        # 3. 修改每个表
        for table_name in tables_to_fix:
            print(f"\n3. 修改表 {table_name}...")
            
            # 获取表结构
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            # 获取外键信息
            cursor.execute(f"PRAGMA foreign_key_list({table_name})")
            foreign_keys = cursor.fetchall()
            
            # 获取索引信息
            cursor.execute(f"PRAGMA index_list({table_name})")
            indexes = cursor.fetchall()
            
            # 构建新的列定义
            column_defs = []
            primary_keys = []
            
            for col in columns:
                col_name = col[1]
                col_type = col[2]
                col_notnull = col[3]
                col_default = col[4]
                col_pk = col[5]
                
                # 修改 user_id 字段类型
                if col_name == 'user_id':
                    col_type = 'VARCHAR(32)'
                
                col_def = f"{col_name} {col_type}"
                
                if col_notnull:
                    col_def += " NOT NULL"
                
                if col_default:
                    col_def += f" DEFAULT {col_default}"
                
                if col_pk:
                    primary_keys.append(col_name)
                
                column_defs.append(col_def)
            
            # 创建临时表
            temp_table_name = f"{table_name}_temp"
            create_sql = f"CREATE TABLE {temp_table_name} (\n  " + ",\n  ".join(column_defs)
            
            if primary_keys:
                create_sql += f",\n  PRIMARY KEY ({', '.join(primary_keys)})"
            
            # 添加外键约束（需要修改为引用 users.user_id）
            for fk in foreign_keys:
                if fk[2] == 'users' and fk[3] == 'user_id':
                    # 修改外键引用
                    create_sql += f",\n  FOREIGN KEY ({fk[3]}) REFERENCES users(user_id)"
                else:
                    create_sql += f",\n  FOREIGN KEY ({fk[3]}) REFERENCES {fk[2]}({fk[4]})"
            
            create_sql += "\n)"
            
            print(f"   创建临时表...")
            cursor.execute(create_sql)
            
            # 复制数据，将 INTEGER user_id 转换为 VARCHAR user_id
            col_names = [col[1] for col in columns]
            print(f"   复制数据...")
            
            # 获取原表数据
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()
            
            for row in rows:
                # 构建 INSERT 语句
                values = []
                for i, col in enumerate(columns):
                    col_name = col[1]
                    if col_name == 'user_id' and row[i] is not None:
                        # 转换 user_id
                        if row[i] in user_mapping:
                            values.append(user_mapping[row[i]])
                        else:
                            values.append(row[i])
                    else:
                        values.append(row[i])
                
                placeholders = ', '.join(['?' for _ in values])
                cursor.execute(f"INSERT INTO {temp_table_name} ({', '.join(col_names)}) VALUES ({placeholders})", values)
            
            # 删除原表
            print(f"   删除原表...")
            cursor.execute(f"DROP TABLE {table_name}")
            
            # 重命名临时表
            print(f"   重命名临时表...")
            cursor.execute(f"ALTER TABLE {temp_table_name} RENAME TO {table_name}")
            
            # 重建索引
            print(f"   重建索引...")
            for idx in indexes:
                cursor.execute(f"PRAGMA index_info({idx[1]})")
                idx_cols = cursor.fetchall()
                idx_col_names = [ic[2] for ic in idx_cols]
                try:
                    cursor.execute(f"CREATE INDEX {idx[1]} ON {table_name} ({', '.join(idx_col_names)})")
                except Exception as e:
                    print(f"     警告: 索引 {idx[1]} 创建失败: {e}")
            
            print(f"   ✅ 已修改")
        
        conn.commit()
        print(f"\n✅ 共修改 {len(tables_to_fix)} 个表")
        return True
        
    except Exception as e:
        print(f"\n❌ 修改失败: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    fix_user_id_fields()
