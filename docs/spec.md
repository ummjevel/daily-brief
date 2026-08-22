# 데일리 모닝 브리핑 시스템 — 설계 문서

> 매일 아침 7시 전, 세 가지 학습 콘텐츠(경제 뉴스 / 비즈니스 영어 / 중국어 회화)를 Google Calendar 알림과 GitHub Pages 아카이브로 받아보는 자동화 시스템.

## 1. 프로젝트 개요

### 목적
매일 아침 정해진 시간에 학습 콘텐츠 3개를 자동 생성하고 받아본다. 중복 없이 누적되며, 과거 콘텐츠는 웹에서 검색·열람 가능.

### 콘텐츠 3종
1. **경제 뉴스 브리핑** — 한국 경제 뉴스 헤드라인 + 관련 경제 개념 풀이
2. **비즈니스 영어 표현** — 엔지니어/AI 트렌드 헤드라인을 소재로, 업무에서 바로 쓰는 표현 1개 + 상황별 예문 + 대체 표현
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
│   [Economy] RSS → 필터 → 본문 fetch → Claude       │
│   [English] 기술 RSS fetch → Claude 표현 추천      │
│   [Chinese] 카테고리 순회 → Claude 생성            │
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
| LLM | Claude (`claude -p` 헤드리스, 구독 계정 인증) — 용도별 모델 분리: haiku(선택) / opus(경제 풀이) / sonnet(학습 카드) |
| 경제 뉴스 소스 | 한국경제 RSS (`https://www.hankyung.com/feed/economy`) — V1, 단일 소스 |
| 영어 소스 | 기술 RSS 3종 (Hacker News / InfoQ AI·ML / TechCrunch AI) — 표현의 소재로만 사용 |
| 전달 #1 | Google Calendar API (OAuth refresh token) |
| 전달 #2 | GitHub Pages (Jekyll, `/docs`) |
| 상태 관리 | `state.json` (repo commit) |
| 시크릿 | GitHub Secrets |

## 4. 콘텐츠 사양

### 4.1 경제 뉴스

**처리 흐름 (2단계)**
1. RSS fetch → 50개 헤드라인
2. Claude 호출 #1 (haiku): 학습 가치 높은 1개 선택 (백업 1개 포함)
3. 선택된 기사 URL → web fetch → 본문 추출
4. Claude 호출 #2 (opus): 본문 → 개념 풀이 생성

### 4.2 비즈니스 영어 표현

**처리 흐름**
- 기술 RSS 3종에서 각 상위 10건 헤드라인 + 요약 수집 (feedparser)
- Claude 호출 1회 (sonnet): 헤드라인을 *상황 소재*로 삼아 업무 표현 1개 추천
- `state.json`의 `covered_phrases`로 중복 회피

**설계 의도**
헤드라인에서 단어를 뽑아 가르치지 않는다. 헤드라인은 "이런 논의를 할 때"라는
상황만 제공하고, 실제로 가르치는 것은 톤과 의도를 담은 표현(반박, 완곡, 우선순위
조정, 유보 등)이다. 순수 기술 용어("rate limit" 등)는 프롬프트에서 금지한다.

**폐기된 방식 (BBC 스크래핑)**
BBC "Learning English from the News" 페이지의 `<strong>` 태그를 긁어 표현을
추출했으나, 페이지 하단 안내 문구가 학습 표현으로 뽑히는 구조적 결함이 있었고
(`"latest programmes"`가 실제로 저장됨) 소재가 업무 맥락과 맞지 않아 폐기.

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
    "covered_phrases": [
      {"phrase": "push back on ~", "date": "2026-05-05"}
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
| Claude (구독 계정 인증, 구독 쿼터 사용) | $0 (별도 과금 없음) |
| Google Calendar API | $0 |
| **합계** | **$0** |

## 10. 사전 수동 작업 (브라우저, 1회)

1. GCP 프로젝트 생성
2. Calendar API enable
3. OAuth 2.0 클라이언트 ID 생성 (Desktop app)
4. `npm i -g @anthropic-ai/claude-code` → `claude auth login` → `claude setup-token` (CI용 장기 토큰 발급)
5. Google Calendar에 새 캘린더 "Morning Brief" 생성, `calendarId` 복사
6. 로컬에서 `auth/get_refresh_token.py` 실행 → 브라우저 동의 → refresh token 획득
7. GitHub repo 생성 (public)
8. GitHub Secrets 등록:
   - `CLAUDE_CODE_OAUTH_TOKEN`
   - `GOOGLE_CLIENT_ID`
   - `GOOGLE_CLIENT_SECRET`
   - `GOOGLE_REFRESH_TOKEN`
   - `GOOGLE_CALENDAR_ID`
9. GitHub Pages 활성화 (Settings → Pages → `main` 브랜치 `/docs`)

## 11. 결정 사항

### 결정됨
- 전달: Google Calendar + GitHub Pages
- 스케줄러: GitHub Actions
- LLM: Claude (구독 계정 인증, `claude -p`)
- 영어: 기술 RSS 3종을 소재로 한 비즈니스 영어 (개인 프로필 없이 `covered_phrases`로만 중복 회피)
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
