from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class GenerateMeta:
    scene_title: str = ""
    tags: List[str] | None = None
    tone: Optional[str] = None
    pacing: Optional[str] = None
    dungeon_progress_hint: Optional[str] = None
    dungeon_name: Optional[str] = None
    dungeon_node_name: Optional[str] = None
    main_character: Optional[Dict[str, Any]] = None
    word_count: Optional[int] = None
    duration_ms: Optional[int] = None


OUTPUT_FORMAT_CONSTRAINT_PATH = Path(__file__).resolve().parents[3] / "core" / "output_format_constraint.txt"
CONTENT_TAGS = ["思考过程", "正文部分", "内容总结", "行动选项"]
