import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.core.orchestrator import _build_dev_log_info, _load_output_format_constraint

def test_dev_log_info():
    print("=" * 60)
    print("测试 dev_log_info 构建功能")
    print("=" * 60)
    
    user_input = "测试用户输入"
    system_prompt = "这是一个测试系统提示词"
    
    context = {
        "main_character": {
            "character_id": "char_001",
            "name": "测试主角",
            "ability_tier": "筑基期",
            "economy_summary": "灵石: 1000"
        },
        "worldbook": [
            {
                "category": "地理",
                "title": "测试地点",
                "content": "这是一个测试地点的描述"
            }
        ],
        "characters": [
            {
                "character_id": "char_002",
                "name": "测试NPC",
                "ability_tier": "金丹期"
            }
        ],
        "dungeon": {
            "name": "测试副本",
            "node_name": "第一节点",
            "progress_hint": "进度提示"
        }
    }
    
    history = [
        "这是第一条历史记录",
        "这是第二条历史记录",
        "这是第三条历史记录"
    ]
    
    format_constraint = _load_output_format_constraint()
    
    dev_log_info = _build_dev_log_info(
        user_input=user_input,
        system_prompt=system_prompt,
        context=context,
        history=history,
        format_constraint=format_constraint
    )
    
    print("\n✅ dev_log_info 构建成功！\n")
    
    print("dev_log_info 结构：")
    print("-" * 60)
    for key in dev_log_info.keys():
        if key == "fullPrompt":
            print(f"{key}: [长度: {len(dev_log_info[key])} 字符]")
        elif isinstance(dev_log_info[key], dict):
            print(f"{key}: {list(dev_log_info[key].keys())}")
        elif isinstance(dev_log_info[key], list):
            print(f"{key}: [列表长度: {len(dev_log_info[key])}]")
        else:
            print(f"{key}: {dev_log_info[key]}")
    print("-" * 60)
    
    print("\n验证内容：")
    
    if "userInput" in dev_log_info:
        print("✅ 包含 userInput")
    else:
        print("❌ 缺少 userInput")
    
    if "systemPrompt" in dev_log_info:
        print("✅ 包含 systemPrompt")
    else:
        print("❌ 缺少 systemPrompt")
    
    if "formatConstraint" in dev_log_info:
        print("✅ 包含 formatConstraint")
    else:
        print("❌ 缺少 formatConstraint")
    
    if "contextInfo" in dev_log_info:
        print("✅ 包含 contextInfo")
        context_info = dev_log_info["contextInfo"]
        
        if "mainCharacter" in context_info:
            print("  ✅ 包含 mainCharacter")
        else:
            print("  ❌ 缺少 mainCharacter")
        
        if "worldbook" in context_info:
            print("  ✅ 包含 worldbook")
        else:
            print("  ❌ 缺少 worldbook")
        
        if "characters" in context_info:
            print("  ✅ 包含 characters")
        else:
            print("  ❌ 缺少 characters")
        
        if "dungeon" in context_info:
            print("  ✅ 包含 dungeon")
        else:
            print("  ❌ 缺少 dungeon")
    else:
        print("❌ 缺少 contextInfo")
    
    if "historyInfo" in dev_log_info:
        print("✅ 包含 historyInfo")
    else:
        print("❌ 缺少 historyInfo")
    
    if "fullPrompt" in dev_log_info:
        print("✅ 包含 fullPrompt")
        
        if "[System Prompt]" in dev_log_info["fullPrompt"]:
            print("  ✅ fullPrompt 包含系统提示词")
        else:
            print("  ❌ fullPrompt 缺少系统提示词")
        
        if "[Context]" in dev_log_info["fullPrompt"]:
            print("  ✅ fullPrompt 包含上下文")
        else:
            print("  ❌ fullPrompt 缺少上下文")
        
        if "[Format Constraint - 最高优先级]" in dev_log_info["fullPrompt"]:
            print("  ✅ fullPrompt 包含格式约束")
        else:
            print("  ❌ fullPrompt 缺少格式约束")
        
        if "[User Input]" in dev_log_info["fullPrompt"]:
            print("  ✅ fullPrompt 包含用户输入")
        else:
            print("  ❌ fullPrompt 缺少用户输入")
    else:
        print("❌ 缺少 fullPrompt")
    
    print("\n" + "=" * 60)
    print("测试完成！dev_log_info 已正确构建。")
    print("=" * 60)
    
    print("\n完整提示词预览（前500字符）：")
    print("-" * 60)
    print(dev_log_info["fullPrompt"][:500])
    print("...")
    print("-" * 60)

if __name__ == "__main__":
    test_dev_log_info()
