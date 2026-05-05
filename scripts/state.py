"""state.json 읽기/쓰기 헬퍼."""

import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")
STATE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "state.json")


def load() -> dict:
    with open(STATE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save(state: dict) -> None:
    state["last_run"] = datetime.now(KST).isoformat()
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def get_chinese_category(state: dict) -> str:
    """start_date 기준으로 현재 주차의 카테고리 반환."""
    categories = ["인사", "자기소개", "숫자·나이", "가족", "음식·식당", "시간·날짜", "위치·방향", "쇼핑·돈"]
    start = state["chinese"].get("start_date")
    today = datetime.now(KST).date()

    if not start:
        state["chinese"]["start_date"] = today.isoformat()
        return categories[0]

    from datetime import date
    start_date = date.fromisoformat(start)
    days_since = (today - start_date).days
    index = (days_since // 7) % len(categories)
    return categories[index]
