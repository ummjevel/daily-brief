# 데일리 모닝 브리핑 시스템 — 설계 문서

> 매일 아침 7시 전, 세 가지 학습 콘텐츠(경제 뉴스 / BBC 영어 / 중국어 회화)를 Google Calendar 알림과 GitHub Pages 아카이브로 받아보는 자동화 시스템.

## 1. 프로젝트 개요

### 목적
매일 아침 정해진 시간에 학습 콘텐츠 3개를 자동 생성하고 받아본다. 중복 없이 누적되며, 과거 콘텐츠는 웹에서 검색·열람 가능.

### 콘텐츠 3종
1. **경제 뉴스 브리핑** — 한국 경제 뉴스 헤드라인 + 관련 경제 개념 풀이
2. **BBC Learning English 표현** — BBC "Learning English from the News" 기반, 매일 다른 표현 + 관련/유사 표현
3. **중국어 회화 (초급)** — 일상 기초 회화 한 문장 + 단어별 자세한 풀이 + 한자

### 핵심 요구사항
- 매일 KST 7시 전 알림 도착
- 영어/중국어는 매일 다른 표현 (중복 방지)
- 무료로 운영
- Repo public, GitHub Pages로 아카이브

## 2. 시스템 아키텍처

```
┌─────────────────────────────────────────────────────┐
│ GitHub Actions (cron, KST 06:00 트리거)             │
│                                                     │
│   [Economy] RSS → 필터 → 본문 fetch → Gemini       │
│   [English] BBC 페이지 fetch → Gemini로 변주       │
│   [Chinese] 카테고리 순회 → Gemini 생성            │
│         ↓                                           │
│   Calendar API: 이벤트 3개 생성 (06:50/55/07:00)   │
│   Markdown: docs/posts/YYYY-MM-DD.md commit        │
│   state.json: 갱신 후 commit                        │
└─────────────────────────────────────────────────────┘
         ↓                    ↓
   📅 Google Calendar    🌐 GitHub Pages
```

## 3. 기술 스택

| 레이어 | 선택 |
|---|---|
| 스케줄러 | GitHub Actions cron (`0 21 * * *` UTC = 06:00 KST) |
| LLM | Gemini Flash (무료 티어) |
| 경제 뉴스 소스 | 한국경제 RSS (`https://www.hankyung.com/feed/economy`) — V1, 단일 소스 |
| 영어 소스 | BBC Learning English from the News (주간 우려먹기) |
| 전달 #1 | Google Calendar API (OAuth refresh token) |
| 전달 #2 | GitHub Pages (Jekyll, `/docs`) |
| 상태 관리 | `state.json` (repo commit) |
| 시크릿 | GitHub Secrets |

## 4. 콘텐츠 사양

### 4.1 경제 뉴스

**처리 흐름 (2단계)**
1. RSS fetch → 50개 헤드라인
2. Gemini 호출 #1: 학습 가치 높은 1개 선택 (백업 1개 포함)
3. 선택된 기사 URL → web fetch → 본문 추출
4. Gemini 호출 #2: 본문 → 개념 풀이 생성

### 4.2 BBC Learning English 표현

**처리 흐름**
- BBC 페이지(이번 주 에피소드) fetch — 일주일에 1회만 갱신
- `state.json`에 `current_episode` 저장
- 매일: 같은 에피소드에서 아직 안 다룬 표현 1개 + 관련 표현 3~5개 변주
- 일주일 안 되도 새 에피소드 발행되면 자동 전환

### 4.3 중국어 회화 (초급)

**8주 카테고리 커리큘럼**

| 주차 | 카테고리 | 예시 |
|---|---|---|
| 1 | 인사 | 你好, 早上好, 谢谢, 不客气, 再见 |
| 2 | 자기소개 | 我叫..., 你叫什么, 我是韩国人 |
| 3 | 숫자·나이 | 一二三, 几岁, 我...岁 |
| 4 | 가족 | 爸爸, 妈妈, 哥哥, 姐姐 |
| 5 | 음식·식당 | 吃饭, 好吃, 服务员, 这个 |
| 6 | 시간·날짜 | 几点, 今天, 明天, 星期 |
| 7 | 위치·방향 | 在哪儿, 这里, 那里, 左·右 |
| 8 | 쇼핑·돈 | 多少钱, 太贵, 便宜点 |

각 카테고리당 5~7일 → 8주 한 바퀴. 이후 더 어려운 표현으로 V2 진입.
카테고리 결정: `start_date`로부터 `days_since_start // 7 % 8` → 카테고리 인덱스.

## 5. 전달 방식

### 5.1 Google Calendar
- **별도 캘린더** "Morning Brief" 신규 생성
- 매일 이벤트 3개:
  - 06:50 KST — 경제 뉴스
  - 06:55 KST — 영어 표현
  - 07:00 KST — 중국어 회화
- 알림: 시작 시점 팝업
- 본문에 마크다운 콘텐츠 그대로

### 5.2 GitHub Pages 아카이브
- `/docs/posts/YYYY-MM-DD.md` (3개 콘텐츠 합본)
- `/docs/index.md`에 날짜 링크 자동 추가
- Jekyll 기본 테마 (minima)

## 6. 레포 구조

```
morning-brief/
├── .github/workflows/
│   └── daily.yml
├── scripts/
│   ├── main.py
│   ├── content_economy.py
│   ├── content_english.py
│   ├── content_chinese.py
│   ├── gcal.py
│   ├── archive.py
│   └── state.py
├── auth/
│   └── get_refresh_token.py
├── docs/
│   ├── _config.yml
│   ├── index.md
│   └── posts/
│       └── YYYY-MM-DD.md
├── state.json
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## 7. state.json 스키마

```json
{
  "version": 1,
  "last_run": "2026-05-05T06:00:12+09:00",
  "english": {
    "current_episode": {
      "url": "https://www.bbc.co.uk/learningenglish/...",
      "title": "...",
      "date": "2026-03-04",
      "fetched_at": "2026-05-05T06:00:12+09:00"
    },
    "covered_phrases": [
      {"phrase": "turned out to vote", "date": "2026-05-05"}
    ]
  },
  "chinese": {
    "start_date": "2026-05-05",
    "covered_sentences": [
      {"sentence": "你好", "pinyin": "Nǐ hǎo", "category": "인사", "date": "2026-05-05"}
    ],
    "covered_hanzi": [
      {"char": "好", "date": "2026-05-05"}
    ]
  },
  "economy": {
    "covered_articles": [
      {"url": "https://...", "title": "...", "date": "2026-05-05"}
    ]
  }
}
```

## 8. 스케줄링

| 항목 | 값 |
|---|---|
| GitHub Actions cron | `0 21 * * *` (UTC 21:00 = KST 06:00) |
| 캘린더 이벤트 시각 | 06:50 / 06:55 / 07:00 KST |
| 캘린더 알림 | 시작 시점 팝업 |
| 타임존 | `Asia/Seoul` |

## 9. 비용

| 항목 | 비용 |
|---|---|
| GitHub Actions (public repo) | $0 |
| GitHub Pages (public repo) | $0 |
| Gemini Flash API (무료 티어) | $0 |
| Google Calendar API | $0 |
| **합계** | **$0** |

## 10. 사전 수동 작업 (브라우저, 1회)

1. GCP 프로젝트 생성
2. Calendar API enable
3. OAuth 2.0 클라이언트 ID 생성 (Desktop app)
4. Gemini API key 발급 (Google AI Studio)
5. Google Calendar에 새 캘린더 "Morning Brief" 생성, `calendarId` 복사
6. 로컬에서 `auth/get_refresh_token.py` 실행 → 브라우저 동의 → refresh token 획득
7. GitHub repo 생성 (public)
8. GitHub Secrets 등록:
   - `GEMINI_API_KEY`
   - `GOOGLE_CLIENT_ID`
   - `GOOGLE_CLIENT_SECRET`
   - `GOOGLE_REFRESH_TOKEN`
   - `GOOGLE_CALENDAR_ID`
9. GitHub Pages 활성화 (Settings → Pages → `main` 브랜치 `/docs`)

## 11. 결정 사항

### 결정됨
- 전달: Google Calendar + GitHub Pages
- 스케줄러: GitHub Actions
- LLM: Gemini Flash
- 영어: BBC Learning English from the News (주간 우려먹기)
- 중국어: 8주 카테고리 커리큘럼 순환
- 경제: 2단계 처리 (RSS 필터 → 본문 fetch → 풀이)
- 경제 소스 V1: 한국경제 RSS 단일
- Repo 가시성: public

### V2 후보
- 다중 매체 (매경/연합뉴스 추가)
- 텔레그램 보조 채널
- TTS 음성 버전
- 콘텐츠 카테고리 토글
- 중국어 V2 (중급 카테고리)
