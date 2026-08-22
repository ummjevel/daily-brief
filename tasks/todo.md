# 영어 모듈 전환: BBC 스크래핑 → 엔지니어/AI 트렌드 기반 비즈니스 영어

## 배경
BBC Learning English 스크래핑을 폐기한다. `<strong>` 태그를 전부 긁는 방식이라
하단 안내 문구가 학습 표현으로 뽑히는 구조적 문제가 있었고(state.json에
`"latest programmes"`가 실제로 저장됨), 소스 자체가 원하는 방향(업무/AI 맥락의
비즈니스 영어)과 맞지 않는다.

## 결정 사항
- 트렌드 소스: Python이 RSS를 수집해 프롬프트로 전달 (llm.py의 도구 차단 유지)
- 개인화: 프로필 파일 없이 `covered_phrases` 이력만으로 중복 회피
- 범위: BBC 코드/데이터/출력 포맷 전부 정리

## 작업
- [x] `scripts/content_english.py` 재작성
  - [x] BBC fetch + BeautifulSoup 표현 추출 코드 삭제
  - [x] `fetch_trend_headlines()` 신설 — feedparser로 3개 피드 수집
  - [x] 비즈니스 영어 프롬프트 작성 (업무 상황 중심)
  - [x] Claude 호출 1회 (MODEL_CARD), 응답에서 표현 추출해 state 갱신
- [x] `state.json` english 섹션 교체
  - [x] `current_episode` 제거 (주간 에피소드 개념 소멸)
  - [x] 오염된 `covered_phrases` 항목 제거
- [x] `README.md` / `docs/spec.md` 갱신 (BBC 언급 제거)
- [x] dry-run 검증: `python scripts/content_english.py`
- [x] 캘린더 평문 변환 (`gcal.markdown_to_plain()`) — 경제·중국어 카드에도 함께 적용
- [x] 커밋

## 검증
- 검증: `python scripts/content_english.py`
- done-when: 카드가 새 포맷으로 출력되고, 표현이 실제 업무 상황 표현이며
  (boilerplate 아님), state.json은 dry-run이라 변경 없음
