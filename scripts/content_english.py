"""비즈니스 영어 카드 생성: 엔지니어/AI 트렌드 RSS → Claude 표현 추천."""

import json
import os
import re
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

import feedparser
from bs4 import BeautifulSoup
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import llm

load_dotenv()

KST = ZoneInfo("Asia/Seoul")

# 헤드라인은 표현의 "소재"로만 쓴다. 엔지니어 담론 / 엔터프라이즈 AI 실무 /
# 업계 동향 세 축을 섞어 하루치 맥락을 만든다.
FEEDS = [
    ("Hacker News", "https://news.ycombinator.com/rss"),
    ("InfoQ AI/ML", "https://feed.infoq.com/ai-ml-data-eng/"),
    ("TechCrunch AI", "https://techcrunch.com/category/artificial-intelligence/feed/"),
]
PER_FEED = 10
SUMMARY_CHARS = 240

PROMPT = """You are creating a daily business English card for a Korean software \
engineer who builds AI products (TTS, RAG, OCR, LLM). Their English is \
intermediate: they read technical English fine, but struggle to sound natural \
and appropriately assertive in meetings, code reviews, and written updates.

# Today's engineering / AI headlines (context only)
{headlines_json}

# Already covered (DO NOT pick these or close variants)
{already_covered_list}

# Your task
1. Pick ONE English expression that is genuinely useful in this learner's daily \
   work — standups, code reviews, design discussions, written updates, or \
   negotiating scope with stakeholders. Prefer expressions a native engineer \
   uses constantly but a Korean intermediate speaker would not produce naturally.
2. Ground it in ONE of today's headlines: show why the expression is natural \
   when discussing that topic. The headline is only the SITUATION — do not \
   teach vocabulary lifted from the headline text.
3. Write all explanations in Korean.

# Output format (Markdown)
## 오늘의 비즈니스 영어

**표현**: "<expression>"
**상황**: <어떤 업무 상황에서 쓰는지 한 줄>

**뜻**: <한국어 풀이 1-2문장>

**왜 지금**: <오늘 헤드라인 중 하나와 연결 1-2문장. 기사 제목을 그대로 포함>

**쓰는 법**:
- <격식 수준과 뉘앙스>
- <한국어 화자가 흔히 하는 오용, 또는 어색하게 쓰는 대체 표현>

**업무 예문**:
1. [<상황 라벨>] <English sentence>
   → <한국어 번역>
2. [<상황 라벨>] <English sentence>
   → <한국어 번역>
3. [<상황 라벨>] <English sentence>
   → <한국어 번역>

**바꿔 쓸 수 있는 표현**:
- **<expression>** — <뜻 + 뉘앙스 차이>
- (3개)

# Strict rules
- Output ONLY the markdown above, no preamble.
- Korean for all explanations; English only for the expressions and examples.
- 상황 라벨은 다음 중에서: 스탠드업, 코드리뷰, 디자인 리뷰, 이메일, 1:1, \
스펙 논의, 장애 대응, 고객 미팅
- The chosen expression MUST NOT appear in the already-covered list.
- Do NOT pick bare technical jargon (e.g. "rate limit", "vector database"). \
Pick expressions that carry tone or intent — hedging, pushing back, \
prioritizing, clarifying, committing, deferring.
"""


def _clean_summary(raw: str) -> str:
    """RSS 요약에서 HTML 태그를 제거하고 잘라낸다."""
    if not raw:
        return ""
    text = BeautifulSoup(raw, "html.parser").get_text(separator=" ", strip=True)
    text = re.sub(r"\s+", " ", text)
    return text[:SUMMARY_CHARS]


def fetch_trend_headlines() -> list:
    """엔지니어/AI 피드에서 헤드라인 수집. 일부 피드 실패는 무시한다."""
    headlines = []
    failed = []

    for source, url in FEEDS:
        try:
            feed = feedparser.parse(url)
            entries = feed.entries[:PER_FEED]
            if not entries:
                failed.append(source)
                continue
            for entry in entries:
                title = entry.get("title", "").strip()
                if not title:
                    continue
                headlines.append({
                    "source": source,
                    "title": title,
                    "summary": _clean_summary(entry.get("summary", "")),
                })
        except Exception as e:
            failed.append(f"{source} ({type(e).__name__})")

    if failed:
        print(f"  ⚠ 피드 수집 실패: {', '.join(failed)}", file=sys.stderr)

    return headlines


def generate(state: dict, dry_run: bool = False) -> str:
    """비즈니스 영어 콘텐츠 생성. 반환: 마크다운 문자열."""
    headlines = fetch_trend_headlines()
    if not headlines:
        raise RuntimeError("트렌드 피드에서 헤드라인을 가져오지 못했습니다.")

    # 이미 다룬 표현 목록 (중복 회피)
    covered = [p["phrase"] for p in state["english"]["covered_phrases"]]
    covered_list = "\n".join(f"- {p}" for p in covered) if covered else "(none yet)"

    content = llm.generate(
        PROMPT.format(
            headlines_json=json.dumps(headlines, ensure_ascii=False, indent=2),
            already_covered_list=covered_list,
        ),
        model=llm.MODEL_CARD,
    )

    # 사용된 표현 추출 (출력에서 "표현": 뒤의 값)
    phrase_match = re.search(r'\*\*표현\*\*:\s*"([^"]+)"', content)
    if phrase_match and not dry_run:
        state["english"]["covered_phrases"].append({
            "phrase": phrase_match.group(1),
            "date": datetime.now(KST).strftime("%Y-%m-%d"),
        })

    return content


if __name__ == "__main__":
    from state import load
    state = load()
    result = generate(state, dry_run=True)
    print(result)
