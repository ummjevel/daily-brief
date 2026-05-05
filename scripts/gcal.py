"""Google Calendar 이벤트 생성 클라이언트."""

import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

load_dotenv()

KST = ZoneInfo("Asia/Seoul")
TOKEN_URI = "https://oauth2.googleapis.com/token"


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

    description = body
    if pages_url:
        description += f"\n\n---\n전체 보기: {pages_url}"

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
