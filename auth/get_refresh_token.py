"""
Google Calendar API용 OAuth refresh token 발급 스크립트.

사용법:
  1. .env에 GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET 설정
  2. python auth/get_refresh_token.py
  3. 브라우저에서 Google 동의 → 터미널에 refresh token 출력
  4. 출력된 refresh token을 .env의 GOOGLE_REFRESH_TOKEN에 저장
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from google_auth_oauthlib.flow import InstalledAppFlow

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/calendar.events"]


def main():
    client_id = os.environ.get("GOOGLE_CLIENT_ID")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")

    if not client_id or not client_secret:
        print("ERROR: .env에 GOOGLE_CLIENT_ID와 GOOGLE_CLIENT_SECRET을 설정하세요.")
        sys.exit(1)

    client_config = {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost"],
        }
    }

    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
    creds = flow.run_local_server(port=8080, prompt="consent", access_type="offline")

    print("\n" + "=" * 60)
    print("Refresh Token (아래를 .env에 복사하세요):")
    print("=" * 60)
    print(creds.refresh_token)
    print("=" * 60)


if __name__ == "__main__":
    main()
