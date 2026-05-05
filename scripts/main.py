"""Morning Brief 오케스트레이션 진입점."""

import os
import sys
import traceback

from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from state import load, save
from content_economy import generate as gen_economy
from content_english import generate as gen_english
from content_chinese import generate as gen_chinese
from gcal import create_daily_events
from archive import write_daily_post, update_index


def main():
    state = load()
    errors = []

    # 1. 경제 뉴스
    print("[1/3] 경제 뉴스 생성 중...")
    try:
        economy_content = gen_economy(state)
        print("  ✓ 경제 뉴스 완료")
    except Exception as e:
        economy_content = f"## 오늘의 경제 뉴스\n\n(생성 실패: {e})"
        errors.append(f"economy: {e}")
        traceback.print_exc()

    # 2. 영어 표현
    print("[2/3] 영어 표현 생성 중...")
    try:
        english_content = gen_english(state)
        print("  ✓ 영어 표현 완료")
    except Exception as e:
        english_content = f"## 오늘의 영어 표현\n\n(생성 실패: {e})"
        errors.append(f"english: {e}")
        traceback.print_exc()

    # 3. 중국어 회화
    print("[3/3] 중국어 회화 생성 중...")
    try:
        chinese_content = gen_chinese(state)
        print("  ✓ 중국어 회화 완료")
    except Exception as e:
        chinese_content = f"## 오늘의 중국어 회화\n\n(생성 실패: {e})"
        errors.append(f"chinese: {e}")
        traceback.print_exc()

    # 4. Google Calendar 이벤트 생성
    print("[4/5] 캘린더 이벤트 생성 중...")
    try:
        create_daily_events(economy_content, english_content, chinese_content)
        print("  ✓ 캘린더 이벤트 완료")
    except Exception as e:
        errors.append(f"calendar: {e}")
        traceback.print_exc()

    # 5. 아카이브 작성
    print("[5/5] 아카이브 작성 중...")
    try:
        write_daily_post(economy_content, english_content, chinese_content)
        update_index()
        print("  ✓ 아카이브 완료")
    except Exception as e:
        errors.append(f"archive: {e}")
        traceback.print_exc()

    # 6. state 저장
    save(state)
    print("\n✓ state.json 저장 완료")

    if errors:
        print(f"\n⚠ {len(errors)}개 에러 발생:")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)
    else:
        print("\n✓ 모든 작업 완료!")


if __name__ == "__main__":
    main()
