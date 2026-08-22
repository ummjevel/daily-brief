# Morning Brief

매일 아침 7시 전, 세 가지 학습 콘텐츠를 자동으로 생성하여 Google Calendar 알림과 GitHub Pages 아카이브로 전달하는 시스템.

## 콘텐츠

1. **경제 뉴스 브리핑** — 한국경제 RSS → Claude 개념 풀이
2. **BBC Learning English 표현** — 주간 에피소드에서 매일 다른 표현 변주
3. **중국어 회화 (초급)** — 8주 카테고리 커리큘럼 순환

## LLM

Anthropic API 키 대신 **Claude 구독 계정 인증**을 쓴다 (`claude -p` 헤드리스 호출).
호출 로직은 `scripts/llm.py` 한 곳에 모여 있고, 용도별로 모델을 나눈다:

| 환경변수 | 기본값 | 쓰임 |
|---|---|---|
| `CLAUDE_MODEL_SELECT` | `claude-haiku-4-5` | 헤드라인 1개 고르기 (단순 판별) |
| `CLAUDE_MODEL_EXPLAIN` | `claude-opus-5` | 경제 개념 풀이 (품질 우선) |
| `CLAUDE_MODEL_CARD` | `claude-sonnet-5` | 영어/중국어 학습 카드 |
| `CLAUDE_TIMEOUT_SEC` | `300` | 호출당 타임아웃 |

## 사전 수동 작업 (1회)

### GCP 설정
- [ ] GCP 프로젝트 생성
- [ ] Calendar API enable
- [ ] OAuth 2.0 클라이언트 ID 생성 (Desktop app 타입)

### Claude 인증
```bash
npm install -g @anthropic-ai/claude-code
claude auth login          # 로컬 실행용 (구독 계정 로그인)
claude setup-token         # CI용 장기 토큰 발급 → 출력값을 GitHub Secret에 등록
```

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
  - `CLAUDE_CODE_OAUTH_TOKEN`
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
