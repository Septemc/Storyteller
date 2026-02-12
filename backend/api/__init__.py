"""FastAPI routers for Storyteller.

保持 main.py 的 `from .api import routes_xxx` 用法：
在这里显式导出各个 routes 模块。
"""

from . import routes_story  # noqa: F401
from . import routes_worldbook  # noqa: F401
from . import routes_characters  # noqa: F401
from . import routes_dungeon  # noqa: F401
from . import routes_settings  # noqa: F401
from . import routes_templates  # noqa: F401

# --- 本次重构新增 ---
from . import routes_llm  # noqa: F401
from . import routes_presets  # noqa: F401