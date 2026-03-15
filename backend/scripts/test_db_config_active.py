from backend.db.base import SessionLocal
from backend.db.models import DBPreset, DBRegexProfile
from backend.scripts.test_db_config_helpers import load_config, print_banner


def get_active_preset():
    print_banner("获取当前激活的预设")
    return _print_active(DBPreset, "预设", "children")


def get_active_regex():
    print_banner("获取当前激活的正则配置")
    return _print_active(DBRegexProfile, "正则配置", "children")


def _print_active(model, label: str, children_key: str):
    db = SessionLocal()
    try:
        active = db.query(model).filter(model.is_active == True).first() or db.query(model).filter(model.is_default == True).first()
        if not active:
            print(f"没有找到可用的{label}")
            return None
        print(f"当前激活的{label}: {active.name} (ID: {active.id})")
        config = load_config(active.config_json)
        root = config.get("root", {})
        children = root.get(children_key, [])
        print(f"\n{label}结构:\n  根节点: {root.get('title', '未命名')}\n  子节点数: {len(children)}")
        for child in children:
            print(f"  - {child.get('title', '未命名')}")
        return active
    finally:
        db.close()
