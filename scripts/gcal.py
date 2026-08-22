"""Google Calendar 이벤트 생성 클라이언트."""

import os
import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

load_dotenv()

KST = ZoneInfo("Asia/Seoul")
TOKEN_URI = "https://oauth2.googleapis.com/token"


# 캘린더 이벤트 본문은 마크다운을 렌더링하지 않아 `**`, `##` 같은 기호가 그대로
# 노출된다. 아카이브(GitHub Pages)는 마크다운을 그대로 쓰므로, 변환은 캘린더로
# 나가는 이 경계에서만 한다.
def markdown_to_plain(md: str) -> str:
    """마크다운을 캘린더에서 읽기 좋은 평문으로 변환."""
    lines = []
    for line in md.splitlines():
        # 수평선
        if re.fullmatch(r"\s*([-*_])\1{2,}\s*", line):
            lines.append("─" * 24)
            continue
        # 헤더 → 기호 접두사 (##까지 대제목, ### 이하 소제목)
        header = re.match(r"\s*(#{1,6})\s+(.*)", line)
        if header:
            prefix = "■ " if len(header.group(1)) <= 2 else "▸ "
            lines.append(prefix + header.group(2).strip())
            continue
        line = re.sub(r"^(\s*)>\s?", r"\1", line)          # 인용 기호 제거
        line = re.sub(r"^(\s*)[-*+]\s+", r"\1• ", line)    # 불릿 (들여쓰기 유지)
        lines.append(line)

    text = "\n".join(lines)
    text = re.sub(r"\[([^\]]+)\]\((https?://[^\s)]+)\)", r"\1 (\2)", text)  # 링크
    text = re.sub(r"(\*\*|__)(.+?)\1", r"\2", text, flags=re.S)                 # 볼드
    # 이탤릭은 `*`만 처리한다. `_`는 snake_case 식별자를 망가뜨릴 위험이 크다.
    text = re.sub(r"(?<![\w*])\*(?!\s)([^*\n]+?)(?<!\s)\*(?![\w*])", r"\1", text)
    text = re.sub(r"`([^`\n]+)`", r"\1", text)                                    # 인라인 코드
    text = re.sub(r"\n{3,}", "\n\n", text)                                       # 빈 줄 정리
    return text.strip()


def get_calendar_service():
    """Calendar API 서비스 객체 반환."""
    creds = Credentials(
        token=None,
        refresh_token=os.environ["GOOGLE_REFRESH_TOKEN"],
        token_uri=TOKEN_URI,
        client_id=os.environ["GOOGLE_CLIENT_ID"],
        client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
    )
    creds.refresh(Request())
    return build("calendar", "v3", credentials=creds)


def create_event(service, calendar_id: str, title: str, body: str, start_hour: int, start_minute: int, pages_url: str = "") -> dict:
    """캘린더 이벤트 1개 생성."""
    today = datetime.now(KST).date()
    start_dt = datetime(today.year, today.month, today.day, start_hour, start_minute, tzinfo=KST)
    end_dt = start_dt + timedelta(minutes=5)

    description = markdown_to_plain(body)
    if pages_url:
        description += f"\n\n{'─' * 24}\n전체 보기: {pages_url}"

    event = {
        "summary": title,
        "description": description,
        "start": {
            "dateTime": start_dt.isoformat(),
            "timeZone": "Asia/Seoul",
        },
        "end": {
            "dateTime": end_dt.isoformat(),
            "timeZone": "Asia/Seoul",
        },
        "reminders": {
            "useDefault": False,
            "overrides": [
                {"method": "popup", "minutes": 0},
            ],
        },
    }

    return service.events().insert(calendarId=calendar_id, body=event).execute()


def create_daily_events(economy: str, english: str, chinese: str, pages_url: str = "") -> None:
    """오늘의 이벤트 3개 생성."""
    service = get_calendar_service()
    calendar_id = os.environ["GOOGLE_CALENDAR_ID"]

    create_event(service, calendar_id, "📰 경제 뉴스 브리핑", economy, 6, 50, pages_url)
    create_event(service, calendar_id, "🇬🇧 영어 표현", english, 6, 55, pages_url)
    create_event(service, calendar_id, "🇨🇳 중국어 회화", chinese, 7, 0, pages_url)
