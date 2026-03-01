"""
测试脚本：读取数据库中的预设和正则配置
"""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.db.base import SessionLocal
from backend.db.models import DBPreset, DBRegexProfile


def test_read_presets():
    print("\n" + "=" * 60)
    print("测试读取预设配置 (presets表)")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        presets = db.query(DBPreset).all()
        
        if not presets:
            print("数据库中没有预设配置")
            return []
        
        print(f"共找到 {len(presets)} 个预设配置:\n")
        
        result = []
        for p in presets:
            config = json.loads(p.config_json) if p.config_json else {}
            
            preset_info = {
                "id": p.id,
                "name": p.name,
                "version": p.version,
                "is_default": p.is_default,
                "is_active": p.is_active,
                "created_at": str(p.created_at) if p.created_at else None,
                "root_children_count": len(config.get("root", {}).get("children", []))
            }
            result.append(preset_info)
            
            status = []
            if p.is_default:
                status.append("默认")
            if p.is_active:
                status.append("激活")
            status_str = " | ".join(status) if status else "普通"
            
            print(f"  [{status_str}] {p.name}")
            print(f"    ID: {p.id}")
            print(f"    版本: {p.version}")
            print(f"    子节点数: {preset_info['root_children_count']}")
            
            root = config.get("root", {})
            children = root.get("children", [])
            if children:
                print(f"    子节点列表:")
                for child in children:
                    kind = child.get("kind", "unknown")
                    title = child.get("title", "未命名")
                    enabled = "启用" if child.get("enabled", True) else "禁用"
                    identifier = child.get("identifier", "无")
                    print(f"      - [{kind}] {title} ({identifier}) - {enabled}")
            print()
        
        return result
    finally:
        db.close()


def test_read_regex_profiles():
    print("\n" + "=" * 60)
    print("测试读取正则配置 (db_regex_profiles表)")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        profiles = db.query(DBRegexProfile).all()
        
        if not profiles:
            print("数据库中没有正则配置")
            return []
        
        print(f"共找到 {len(profiles)} 个正则配置:\n")
        
        result = []
        for p in profiles:
            config = json.loads(p.config_json) if p.config_json else {}
            
            profile_info = {
                "id": p.id,
                "name": p.name,
                "version": p.version,
                "is_default": p.is_default,
                "is_active": p.is_active,
                "created_at": str(p.created_at) if p.created_at else None,
                "root_children_count": len(config.get("root", {}).get("children", []))
            }
            result.append(profile_info)
            
            status = []
            if p.is_default:
                status.append("默认")
            if p.is_active:
                status.append("激活")
            status_str = " | ".join(status) if status else "普通"
            
            print(f"  [{status_str}] {p.name}")
            print(f"    ID: {p.id}")
            print(f"    版本: {p.version}")
            print(f"    子节点数: {profile_info['root_children_count']}")
            
            root = config.get("root", {})
            children = root.get("children", [])
            if children:
                print(f"    规则组列表:")
                for group in children:
                    kind = group.get("kind", "unknown")
                    title = group.get("title", "未命名")
                    enabled = "启用" if group.get("enabled", True) else "禁用"
                    identifier = group.get("identifier", "无")
                    group_children = group.get("children", [])
                    print(f"      - [{kind}] {title} ({identifier}) - {enabled}")
                    for rule in group_children:
                        rule_kind = rule.get("kind", "unknown")
                        rule_title = rule.get("title", "未命名")
                        rule_enabled = "启用" if rule.get("enabled", True) else "禁用"
                        pattern = rule.get("pattern", "")
                        pattern_preview = pattern[:50] + "..." if len(pattern) > 50 else pattern
                        print(f"          * [{rule_kind}] {rule_title} - {rule_enabled}")
                        if pattern:
                            print(f"            模式: {pattern_preview}")
            print()
        
        return result
    finally:
        db.close()


def get_active_preset():
    print("\n" + "=" * 60)
    print("获取当前激活的预设")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        active = db.query(DBPreset).filter(DBPreset.is_active == True).first()
        
        if not active:
            default = db.query(DBPreset).filter(DBPreset.is_default == True).first()
            if default:
                print(f"没有激活的预设，使用默认预设: {default.name}")
                return default
            print("没有找到可用的预设")
            return None
        
        print(f"当前激活的预设: {active.name} (ID: {active.id})")
        
        config = json.loads(active.config_json) if active.config_json else {}
        root = config.get("root", {})
        children = root.get("children", [])
        
        print(f"\n预设内容结构:")
        print(f"  根节点: {root.get('title', '未命名')}")
        print(f"  子节点数: {len(children)}")
        
        for child in children:
            kind = child.get("kind")
            if kind == "prompt":
                title = child.get("title", "未命名")
                identifier = child.get("identifier", "无")
                enabled = child.get("enabled", True)
                content = child.get("content", "")
                content_preview = content[:100] + "..." if len(content) > 100 else content
                print(f"\n  [提示词] {title} ({identifier})")
                print(f"    启用状态: {enabled}")
                print(f"    内容预览: {content_preview}")
        
        return active
    finally:
        db.close()


def get_active_regex():
    print("\n" + "=" * 60)
    print("获取当前激活的正则配置")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        active = db.query(DBRegexProfile).filter(DBRegexProfile.is_active == True).first()
        
        if not active:
            default = db.query(DBRegexProfile).filter(DBRegexProfile.is_default == True).first()
            if default:
                print(f"没有激活的正则配置，使用默认配置: {default.name}")
                return default
            print("没有找到可用的正则配置")
            return None
        
        print(f"当前激活的正则配置: {active.name} (ID: {active.id})")
        
        config = json.loads(active.config_json) if active.config_json else {}
        root = config.get("root", {})
        children = root.get("children", [])
        
        print(f"\n正则配置结构:")
        print(f"  根节点: {root.get('title', '未命名')}")
        print(f"  子节点数: {len(children)}")
        
        enabled_rules = []
        for group in children:
            if group.get("enabled", True):
                group_title = group.get("title", "未命名")
                group_children = group.get("children", [])
                print(f"\n  [规则组] {group_title} (启用)")
                for rule in group_children:
                    if rule.get("enabled", True):
                        rule_title = rule.get("title", "未命名")
                        pattern = rule.get("pattern", "")
                        enabled_rules.append({
                            "group": group_title,
                            "rule": rule_title,
                            "pattern": pattern
                        })
                        print(f"    - {rule_title}")
                        print(f"      模式: {pattern}")
        
        print(f"\n  共 {len(enabled_rules)} 条启用的规则")
        return active
    finally:
        db.close()


def main():
    print("=" * 60)
    print("数据库预设和正则配置测试")
    print("=" * 60)
    
    test_read_presets()
    test_read_regex_profiles()
    get_active_preset()
    get_active_regex()
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
