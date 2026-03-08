"""
数据库初始化脚本：为Storyteller生成功能创建必要的默认配置

功能：
1. 创建默认的LLM配置（AI服务配置）
2. 创建默认的预设模板
3. 初始化必要的系统设置
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import text, inspect
from backend.db.base import engine, SessionLocal
from backend.db.models import Base, DBLLMConfig, DBPreset, GlobalSetting


def table_exists(table_name: str) -> bool:
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()


def initialize_database():
    print("=" * 60)
    print("开始数据库初始化：创建生成功能所需配置")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # 检查表是否存在
        if not table_exists("llm_configs"):
            print("❌ llm_configs 表不存在，请先运行数据库迁移脚本")
            return False
        
        if not table_exists("presets"):
            print("❌ presets 表不存在，请先运行数据库迁移脚本")
            return False
        
        # 创建默认的LLM配置
        print("\n[步骤1] 创建默认LLM配置...")
        existing_config = db.query(DBLLMConfig).filter(DBLLMConfig.is_active == True).first()
        if not existing_config:
            default_config = DBLLMConfig(
                name="默认AI服务",
                base_url="https://api.openai.com/v1",
                api_key="your-api-key-here",  # 需要用户配置
                stream=True,
                default_model="gpt-3.5-turbo",
                is_active=True
            )
            db.add(default_config)
            print("  ✅ 创建默认LLM配置（请配置API密钥）")
        else:
            print("  ⏭️ 已有激活的LLM配置，跳过")
        
        # 创建默认预设
        print("\n[步骤2] 创建默认预设...")
        existing_preset = db.query(DBPreset).filter(DBPreset.is_default == True).first()
        if not existing_preset:
            default_preset = DBPreset(
                name="默认剧情生成",
                description="标准剧情生成预设",
                system_prompt="""你是一个专业的剧情生成助手。请根据用户输入生成连贯的故事情节。

生成要求：
1. 保持故事连贯性和逻辑性
2. 使用生动的语言描述
3. 适当包含对话和场景描写
4. 每段控制在200-500字之间

请生成下一段剧情。""",
                temperature=0.8,
                max_tokens=1000,
                is_default=True
            )
            db.add(default_preset)
            print("  ✅ 创建默认预设")
        else:
            print("  ⏭️ 已有默认预设，跳过")
        
        # 设置全局配置
        print("\n[步骤3] 设置全局配置...")
        existing_setting = db.query(GlobalSetting).filter(GlobalSetting.key == "active_preset_id").first()
        if not existing_setting:
            # 获取默认预设ID
            default_preset = db.query(DBPreset).filter(DBPreset.is_default == True).first()
            if default_preset:
                setting = GlobalSetting(
                    key="active_preset_id",
                    value_json=str(default_preset.id)
                )
                db.add(setting)
                print("  ✅ 设置激活预设ID")
        else:
            print("  ⏭️ 全局配置已存在，跳过")
        
        db.commit()
        print("\n✅ 数据库初始化完成！")
        print("\n⚠️  重要提醒：")
        print("1. 请配置LLM配置中的API密钥")
        print("2. 确保AI服务可访问")
        print("3. 测试生成功能是否正常")
        
        return True
        
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        db.rollback()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    initialize_database()