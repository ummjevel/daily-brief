# Morning Brief

매일 아침 7시 전, 세 가지 학습 콘텐츠를 자동으로 생성하여 Google Calendar 알림과 GitHub Pages 아카이브로 전달하는 시스템.

## 콘텐츠

1. **경제 뉴스 브리핑** — 한국경제 RSS → Gemini 개념 풀이
2. **BBC Learning English 표현** — 주간 에피소드에서 매일 다른 표현 변주
3. **중국어 회화 (초급)** — 8주 카테고리 커리큘럼 순환

## 사전 수동 작업 (1회)

### GCP 설정
- [ ] GCP 프로젝트 생성
- [ ] Calendar API enable
- [ ] OAuth 2.0 클라이언트 ID 생성 (Desktop app 타입)
- [ ] Gemini API key 발급 (Google AI Studio)

### Google Calendar
- [ ] 새 캘린더 "Morning Brief" 생성
- [ ] `calendarId` 복사

### OAuth Refresh Token 발급
```bash
# .env에 CLIENT_ID, CLIENT_SECRET 설정 후:
python auth/get_refresh_token.py
# 브라우저 동의 → 터미널에 refresh token 출력
```

### GitHub 설정
- [ ] GitHub repo 생성 (public)
- [ ] GitHub Secrets 등록:
  - `GEMINI_API_KEY`
  - `GOOGLE_CLIENT_ID`
  - `GOOGLE_CLIENT_SECRET`
  - `GOOGLE_REFRESH_TOKEN`
  - `GOOGLE_CALENDAR_ID`
- [ ] GitHub Pages 활성화 (Settings → Pages → `main` 브랜치 `/docs`)

## 로컬 실행

```bash
cp .env.example .env
# .env 파일에 실제 키 입력

pip install -r requirements.txt
python scripts/main.py
```

## 스케줄

- GitHub Actions: 매일 UTC 21:00 (KST 06:00)
- 캘린더 알림: 06:50 (경제) / 06:55 (영어) / 07:00 (중국어)
