"""중국어 회화 콘텐츠 생성: 카테고리 순회 → Gemini 생성."""

import os
import re
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

KST = ZoneInfo("Asia/Seoul")

PROMPT = """You are creating a daily Mandarin Chinese learning card for an \
absolute beginner Korean learner. The learner has NO prior Chinese \
knowledge — every sentence must be very short (2-4 characters or \
one short clause max ~6 characters), every word must be explained, \
and complex grammar should be avoided.

# Today's category
{category}

# Already covered sentences (DO NOT repeat)
{already_covered_sentences}

# Already covered Hanzi (avoid for "Hanzi of the day")
{already_covered_hanzi}

# Your task
1. Pick ONE very simple sentence appropriate for the category and \
   the beginner level. Must be 2-4 characters, or one short clause \
   max ~6 characters.
2. Break down EVERY single character with pinyin and meaning.
3. Provide 3 related useful phrases (also beginner-level).
4. Pick ONE Hanzi from the sentence as "Hanzi of the day" and \
   explain it visually/etymologically in a memorable way.

# Output format (Markdown)
## 오늘의 중국어 회화 — {category}

**문장**: <Chinese>
**병음**: <pinyin with tone marks>
**뜻**: <Korean translation>

**단어별 풀이**:
- **<char> (<pinyin>)** — <Korean meaning>
  · <한 줄 추가 설명>
- (모든 글자)

**함께 알면 좋은 표현**:
- **<phrase> (<pinyin>)** — <뜻>
- (3개, 모두 초급)

**오늘의 한자**: <single character>
- 구성: <부수/형성, 시각적 설명>
- 직관적 이미지: <기억 도움이 되는 한 줄>
- 다른 단어 예시: <2개>

# Strict rules
- Output ONLY the markdown, no preamble.
- Korean explanations only.
- Sentence MUST be beginner-level (no idioms, no complex grammar).
- The sentence MUST NOT appear in already-covered list.
- Tone marks required on all pinyin.
"""


def generate(state: dict, dry_run: bool = False) -> str:
    """중국어 회화 콘텐츠 생성. 반환: 마크다운 문자열."""
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    model = genai.GenerativeModel("gemini-2.0-flash")

    # state.py에서 카테고리 결정
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from state import get_chinese_category
    category = get_chinese_category(state)

    # 이미 다룬 문장/한자
    covered_sentences = [s["sentence"] for s in state["chinese"]["covered_sentences"]]
    covered_hanzi = [h["char"] for h in state["chinese"]["covered_hanzi"]]

    covered_sentences_str = "\n".join(f"- {s}" for s in covered_sentences) if covered_sentences else "(none yet)"
    covered_hanzi_str = ", ".join(covered_hanzi) if covered_hanzi else "(none yet)"

    # Gemini 호출
    resp = model.generate_content(PROMPT.format(
        category=category,
        already_covered_sentences=covered_sentences_str,
        already_covered_hanzi=covered_hanzi_str,
    ))
    content = resp.text.strip()

    # state 갱신: 문장, 한자 추출
    if not dry_run:
        today = datetime.now(KST).strftime("%Y-%m-%d")

        # 문장 추출
        sentence_match = re.search(r'\*\*문장\*\*:\s*(.+)', content)
        pinyin_match = re.search(r'\*\*병음\*\*:\s*(.+)', content)
        if sentence_match:
            state["chinese"]["covered_sentences"].append({
                "sentence": sentence_match.group(1).strip(),
                "pinyin": pinyin_match.group(1).strip() if pinyin_match else "",
                "category": category,
                "date": today,
            })

        # 한자 추출
        hanzi_match = re.search(r'\*\*오늘의 한자\*\*:\s*(.)', content)
        if hanzi_match:
            state["chinese"]["covered_hanzi"].append({
                "char": hanzi_match.group(1),
                "date": today,
            })

    return content


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from state import load
    state = load()
    result = generate(state, dry_run=True)
    print(result)
