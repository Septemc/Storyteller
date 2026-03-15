import json


def print_banner(title: str) -> None:
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def load_config(value):
    return json.loads(value) if value else {}


def status_text(*flags: str) -> str:
    values = [flag for flag in flags if flag]
    return " | ".join(values) if values else "普通"
