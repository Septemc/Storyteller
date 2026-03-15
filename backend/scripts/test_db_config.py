"""
测试脚本：读取数据库中的预设和正则配置
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.scripts.test_db_config_active import get_active_preset, get_active_regex
from backend.scripts.test_db_config_helpers import print_banner
from backend.scripts.test_db_config_readers import test_read_presets, test_read_regex_profiles


def main():
    print_banner("数据库预设和正则配置测试")
    test_read_presets()
    test_read_regex_profiles()
    get_active_preset()
    get_active_regex()
    print_banner("测试完成")


if __name__ == "__main__":
    main()
