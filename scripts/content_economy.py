"""경제 뉴스 브리핑 생성: RSS → Gemini 헤드라인 선택 → 본문 fetch → Gemini 풀이."""

import json
import os
import re
import sys

import feedparser
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

RSS_URL = "https://www.hankyung.com/feed/economy"

PROMPT_SELECT = """You are filtering Korean economic news headlines for a daily \
learning brief. The reader is a working professional who wants \
to understand macroeconomics, policy, and finance — NOT marketing \
news, food product launches, celebrity-adjacent business stories, \
or PR puffery.

# Headlines (JSON array)
{headlines_json}

# Task
Pick ONE headline that best meets these criteria:
1. Contains a meaningful macro / policy / financial / industry \
   concept worth explaining to a learner
2. NOT product launch / marketing / corporate PR / single-company \
   minutiae
3. NOT entertainment / lifestyle adjacent
4. Prefer analytical pieces (op-eds, deep dives) over straight news

# Output (raw JSON, no markdown fence)
{{"selected_title": "<title>", "selected_url": "<url>", "selected_index": <index>, "rationale": "<one sentence in Korean>", "backup_index": <2nd choice index>}}
"""

PROMPT_EXPLAIN = """You are creating a daily economic news brief in Korean for an \
educated working professional who wants to deepen their economic \
literacy. Explain everything in Korean.

# Article
Title: {title}
Source: 한국경제, {date}
URL: {url}
Body:
{body}

# Task
1. Summarize the article in 2-3 sentences
2. Identify 2-3 KEY ECONOMIC CONCEPTS in the article and explain \
   each clearly for a non-expert (no jargon walls, analogies welcome)
3. Explain why this matters today

# Output format (Markdown)
## 오늘의 경제 뉴스

**제목**: <title>
**출처**: 한국경제 ({date})
**원문**: <url>

### 한 줄 요약
<2-3 문장>

### 핵심 개념

- **<개념1 한국어 (영문 표기)>**
  <3-5문장 풀이, 비유 환영>

- **<개념2>**
  <같은 형식>

### 왜 중요한가
<2-3 문장>

# Rules
- All Korean except concept names which include English in parens
- Jargon-light, like teaching a smart friend
- Output ONLY the markdown, no preamble
"""


def fetch_rss() -> list:
    """RSS에서 헤드라인 수집."""
    resp = requests.get(RSS_URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
    resp.raise_for_status()
    feed = feedparser.parse(resp.text)
    headlines = []
    for i, entry in enumerate(feed.entries[:50]):
        headlines.append({
            "index": i,
            "title": entry.get("title", ""),
            "url": entry.get("link", ""),
        })
    return headlines


def fetch_article_body(url: str) -> str:
    """기사 URL에서 본문 텍스트 추출."""
    resp = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # 한경 기사 본문 셀렉터
    article = soup.select_one("div.article-body") or soup.select_one("article") or soup.select_one("#articletxt")
    if article:
        return article.get_text(separator="\n", strip=True)[:3000]

    # fallback: 모든 p 태그
    paragraphs = soup.find_all("p")
    text = "\n".join(p.get_text(strip=True) for p in paragraphs)
    return text[:3000]


def parse_json_response(text: str) -> dict:
    """Gemini 응답에서 JSON 파싱 (마크다운 펜스 제거)."""
    cleaned = re.sub(r"```json\s*", "", text)
    cleaned = re.sub(r"```\s*", "", cleaned)
    return json.loads(cleaned.strip())


def generate(state: dict, dry_run: bool = False) -> str:
    """경제 뉴스 콘텐츠 생성. 반환: 마크다운 문자열."""
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    model = genai.GenerativeModel("gemini-2.0-flash")

    # 1. RSS fetch
    headlines = fetch_rss()
    if not headlines:
        raise RuntimeError("RSS에서 헤드라인을 가져오지 못했습니다.")

    # 2. Gemini: 헤드라인 선택
    headlines_json = json.dumps(headlines, ensure_ascii=False)
    resp = model.generate_content(PROMPT_SELECT.format(headlines_json=headlines_json))
    selection = parse_json_response(resp.text)

    selected_url = selection["selected_url"]
    selected_title = selection["selected_title"]

    # 이미 다룬 기사인지 체크
    covered_urls = [a["url"] for a in state["economy"]["covered_articles"]]
    if selected_url in covered_urls:
        # backup 사용
        backup_idx = selection.get("backup_index", 1)
        if backup_idx < len(headlines):
            selected_url = headlines[backup_idx]["url"]
            selected_title = headlines[backup_idx]["title"]

    # 3. 본문 fetch
    try:
        body = fetch_article_body(selected_url)
    except Exception:
        # backup 시도
        backup_idx = selection.get("backup_index", 1)
        if backup_idx < len(headlines):
            selected_url = headlines[backup_idx]["url"]
            selected_title = headlines[backup_idx]["title"]
            body = fetch_article_body(selected_url)
        else:
            raise

    # 4. Gemini: 본문 → 개념 풀이
    from datetime import datetime
    from zoneinfo import ZoneInfo
    today = datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y-%m-%d")

    resp = model.generate_content(PROMPT_EXPLAIN.format(
        title=selected_title,
        date=today,
        url=selected_url,
        body=body,
    ))
    content = resp.text.strip()

    # state 갱신
    if not dry_run:
        state["economy"]["covered_articles"].append({
            "url": selected_url,
            "title": selected_title,
            "date": today,
        })

    return content


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from state import load
    state = load()
    result = generate(state, dry_run=True)
    print(result)
