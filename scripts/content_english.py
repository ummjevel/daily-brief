"""BBC Learning English 표현 생성: 에피소드 fetch → Gemini 변주."""

import json
import os
import re
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

KST = ZoneInfo("Asia/Seoul")
BBC_INDEX_URL = "https://www.bbc.co.uk/learningenglish"

PROMPT = """You are creating a daily English learning card for a Korean learner \
with intermediate English. The learner already understands basic \
grammar and vocabulary but wants to expand their range with phrases \
used in real news.

# Source material
Episode: {episode_title}
Date: {episode_date}
Source URL: {episode_url}

Story summary:
{story_summary}

Featured phrases from this episode:
{featured_phrases_json}

# Already covered (DO NOT pick these)
{already_covered_list}

# Your task
1. Pick ONE phrase from the featured phrases that is NOT in the \
   already-covered list. Prefer phrases that are useful in everyday \
   English, not just news.
2. Explain it in Korean.
3. Provide 3-5 RELATED or SIMILAR phrases (synonyms, alternatives \
   with different nuance, or phrases used in similar contexts).
4. Provide 2 short example sentences using the chosen phrase, \
   showing varied contexts (not just news).

# Output format (Markdown)
## 오늘의 영어 표현

**표현**: "<phrase>"
**출처**: BBC Learning English — {episode_title} ({episode_date})

**뜻**: <한국어 풀이 1-2문장>

**핵심 단어 분해**:
- **<word1>** — <설명>
- **<word2>** — <설명>

**원문 문장** (BBC 에피소드에서):
> "<exact quote from story summary or featured phrase context>"

**관련/유사 표현**:
- **<phrase>** — <뜻 + 뉘앙스 차이>
- (3-5개)

**미니 예문**:
1. <example sentence 1>
   → <한국어 번역>
2. <example sentence 2>
   → <한국어 번역>

# Strict rules
- Output ONLY the markdown above, no preamble.
- All explanations in Korean except the English phrases themselves.
- Pick phrases useful beyond the news context.
- The chosen phrase MUST NOT appear in the already-covered list.
"""


def fetch_latest_episode() -> dict:
    """BBC Learning English에서 최신 에피소드 정보 가져오기."""
    headers = {"User-Agent": "Mozilla/5.0"}

    # 메인 페이지에서 "learning-english-from-the-news" 에피소드 링크 찾기
    resp = requests.get(BBC_INDEX_URL, timeout=15, headers=headers)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    episode_url = None
    for link in soup.find_all("a", href=True):
        href = link["href"]
        if "learning-english-from-the-news" in href:
            if not href.startswith("http"):
                href = "https://www.bbc.co.uk" + href
            episode_url = href
            break

    if not episode_url:
        return None

    # 에피소드 페이지 fetch
    ep_resp = requests.get(episode_url, timeout=15, headers=headers)
    ep_resp.raise_for_status()
    ep_soup = BeautifulSoup(ep_resp.text, "html.parser")

    # 제목 추출
    title_el = ep_soup.find("title")
    title = title_el.get_text(strip=True) if title_el else "BBC Learning English"
    # "BBC Learning English - Learning English from the News / " 접두사 제거
    if "/" in title:
        title = title.split("/")[-1].strip()

    # 본문/요약 추출
    summary_el = ep_soup.select_one(".widget-richtext") or ep_soup.select_one("article")
    summary = summary_el.get_text(separator="\n", strip=True)[:2000] if summary_el else ""

    # 표현 추출 (볼드 텍스트에서 2단어 이상 구문)
    phrases = []
    for strong in ep_soup.find_all("strong"):
        text = strong.get_text(strip=True)
        # "The story", "Key words" 같은 섹션 헤더 제외
        skip = ["The story", "Key words and phrases", "BBC News", "The Guardian"]
        if len(text.split()) >= 2 and len(text) < 60 and text not in skip:
            phrases.append(text)

    # 중복 제거
    phrases = list(dict.fromkeys(phrases))

    return {
        "url": episode_url,
        "title": title,
        "date": datetime.now(KST).strftime("%Y-%m-%d"),
        "summary": summary,
        "phrases": phrases,
    }


def should_refresh_episode(state: dict) -> bool:
    """에피소드를 새로 fetch해야 하는지 판단."""
    current = state["english"].get("current_episode")
    if not current:
        return True

    # 7일 이상 지났으면 갱신 시도
    fetched_at = current.get("fetched_at", "")
    if not fetched_at:
        return True

    from datetime import date
    fetched_date = date.fromisoformat(fetched_at[:10])
    today = datetime.now(KST).date()
    return (today - fetched_date).days >= 7


def generate(state: dict, dry_run: bool = False) -> str:
    """영어 표현 콘텐츠 생성. 반환: 마크다운 문자열."""
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    model = genai.GenerativeModel("gemini-2.0-flash-001")

    episode = None

    # 에피소드 fetch (필요 시)
    if should_refresh_episode(state):
        episode = fetch_latest_episode()
        if episode and not dry_run:
            state["english"]["current_episode"] = {
                "url": episode["url"],
                "title": episode["title"],
                "date": episode["date"],
                "fetched_at": datetime.now(KST).isoformat(),
            }
            # 새 에피소드면 covered_phrases 리셋
            state["english"]["covered_phrases"] = []

    # episode가 없으면 (refresh 불필요 또는 fetch 실패) 다시 fetch
    if not episode:
        episode = fetch_latest_episode()

    if not episode:
        current_ep = state["english"].get("current_episode")
        if not current_ep:
            raise RuntimeError("BBC 에피소드를 가져올 수 없습니다.")
        # fallback: state 정보로 Gemini에게 자유 생성 요청
        episode = {
            "url": current_ep["url"],
            "title": current_ep["title"],
            "date": current_ep["date"],
            "summary": "N/A",
            "phrases": [],
        }

    # 이미 다룬 표현 목록
    covered = [p["phrase"] for p in state["english"]["covered_phrases"]]
    covered_list = "\n".join(f"- {p}" for p in covered) if covered else "(none yet)"

    # Gemini 호출
    resp = model.generate_content(PROMPT.format(
        episode_title=episode["title"],
        episode_date=episode["date"],
        episode_url=episode["url"],
        story_summary=episode.get("summary", "N/A"),
        featured_phrases_json=json.dumps(episode.get("phrases", []), ensure_ascii=False),
        already_covered_list=covered_list,
    ))
    content = resp.text.strip()

    # 사용된 표현 추출 (출력에서 "표현": 뒤의 값)
    phrase_match = re.search(r'\*\*표현\*\*:\s*"([^"]+)"', content)
    if phrase_match and not dry_run:
        state["english"]["covered_phrases"].append({
            "phrase": phrase_match.group(1),
            "date": datetime.now(KST).strftime("%Y-%m-%d"),
        })

    return content


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from state import load
    state = load()
    result = generate(state, dry_run=True)
    print(result)
