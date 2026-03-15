from backend.db.base import SessionLocal
from backend.db.models import DBPreset, DBRegexProfile
from backend.scripts.test_db_config_helpers import load_config, print_banner, status_text


def test_read_presets():
    print_banner("测试读取预设配置 (presets表)")
    db = SessionLocal()
    try:
        presets = db.query(DBPreset).all()
        if not presets:
            print("数据库中没有预设配置")
            return []
        print(f"共找到 {len(presets)} 个预设配置:\n")
        return [_print_preset(preset) for preset in presets]
    finally:
        db.close()


def test_read_regex_profiles():
    print_banner("测试读取正则配置 (db_regex_profiles表)")
    db = SessionLocal()
    try:
        profiles = db.query(DBRegexProfile).all()
        if not profiles:
            print("数据库中没有正则配置")
            return []
        print(f"共找到 {len(profiles)} 个正则配置:\n")
        return [_print_regex(profile) for profile in profiles]
    finally:
        db.close()


def _print_preset(preset):
    config = load_config(preset.config_json)
    info = {"id": preset.id, "name": preset.name, "version": preset.version, "is_default": preset.is_default, "is_active": preset.is_active, "created_at": str(preset.created_at) if preset.created_at else None, "root_children_count": len(config.get("root", {}).get("children", []))}
    print(f"  [{status_text('默认' if preset.is_default else '', '激活' if preset.is_active else '')}] {preset.name}")
    print(f"    ID: {preset.id}\n    版本: {preset.version}\n    子节点数: {info['root_children_count']}")
    for child in config.get("root", {}).get("children", []):
        print(f"      - [{child.get('kind', 'unknown')}] {child.get('title', '未命名')} ({child.get('identifier', '无')}) - {'启用' if child.get('enabled', True) else '禁用'}")
    print()
    return info


def _print_regex(profile):
    config = load_config(profile.config_json)
    info = {"id": profile.id, "name": profile.name, "version": profile.version, "is_default": profile.is_default, "is_active": profile.is_active, "created_at": str(profile.created_at) if profile.created_at else None, "root_children_count": len(config.get("root", {}).get("children", []))}
    print(f"  [{status_text('默认' if profile.is_default else '', '激活' if profile.is_active else '')}] {profile.name}")
    print(f"    ID: {profile.id}\n    版本: {profile.version}\n    子节点数: {info['root_children_count']}")
    for group in config.get("root", {}).get("children", []):
        print(f"      - [{group.get('kind', 'unknown')}] {group.get('title', '未命名')} ({group.get('identifier', '无')}) - {'启用' if group.get('enabled', True) else '禁用'}")
    print()
    return info
