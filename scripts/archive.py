"""마크다운 아카이브 작성 + index 갱신."""

import os
from datetime import datetime
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")
DOCS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs")
POSTS_DIR = os.path.join(DOCS_DIR, "posts")
INDEX_PATH = os.path.join(DOCS_DIR, "index.md")


def write_daily_post(economy: str, english: str, chinese: str) -> str:
    """오늘의 포스트 작성. 반환: 파일 경로."""
    today = datetime.now(KST).strftime("%Y-%m-%d")
    filename = f"{today}.md"
    filepath = os.path.join(POSTS_DIR, filename)

    content = f"""---
layout: page
title: "Morning Brief — {today}"
date: {today}
---

{economy}

---

{english}

---

{chinese}
"""

    os.makedirs(POSTS_DIR, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    return filepath


def update_index() -> None:
    """index.md에 오늘 날짜 링크 추가."""
    today = datetime.now(KST).strftime("%Y-%m-%d")
    link_line = f"- [{today}](posts/{today}.md)"

    with open(INDEX_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # 이미 있으면 스킵
    if today in content:
        return

    # "<!-- 새 포스트는 이 아래에 자동 추가됩니다 -->" 아래에 삽입
    marker = "<!-- 새 포스트는 이 아래에 자동 추가됩니다 -->"
    if marker in content:
        content = content.replace(marker, f"{marker}\n{link_line}")
    else:
        content += f"\n{link_line}"

    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        f.write(content)
