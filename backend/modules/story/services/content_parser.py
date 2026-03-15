from __future__ import annotations

import re
from typing import Dict, Optional

from .types import CONTENT_TAGS


def is_valid_story_content(text: str) -> bool:
    stripped = (text or "").strip()
    if not stripped:
        return False
    if not any(f"<{tag}>" in stripped for tag in CONTENT_TAGS):
        return len(stripped) >= 10
    body_match = re.search(r"<正文部分>(.*?)</正文部分>", stripped, re.DOTALL)
    if body_match and body_match.group(1).strip():
        return True
    thinking_match = re.search(r"<思考过程>(.*?)</思考过程>", stripped, re.DOTALL)
    return bool(thinking_match and thinking_match.group(1).strip())


def extract_tag_content(text: str, tag_name: str) -> Optional[str]:
    match = re.search(rf"<{tag_name}>(.*?)</{tag_name}>", text, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else None


def extract_story_parts(text: str) -> Dict[str, Optional[str]]:
    tags = list(CONTENT_TAGS)
    return {
        "thinking": extract_tag_content(text, tags[0]),
        "story": extract_tag_content(text, tags[1]),
        "summary": extract_tag_content(text, tags[2]),
        "actions": extract_tag_content(text, tags[3]),
    }
