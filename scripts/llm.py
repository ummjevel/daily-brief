"""Claude Code CLI(`claude -p`)를 통한 LLM 호출.

API 키가 아니라 **구독 계정 인증**을 쓴다:
- 로컬: `claude` 로그인 상태를 그대로 사용 (별도 설정 없음)
- CI: `CLAUDE_CODE_OAUTH_TOKEN` 환경변수 (`claude setup-token`으로 발급)

용도별로 모델을 나눈다 (환경변수로 덮어쓸 수 있음):
- MODEL_SELECT  : 헤드라인 고르기 등 단순 판별 → haiku
- MODEL_EXPLAIN : 경제 개념 풀이 → opus
- MODEL_CARD    : 영어/중국어 학습 카드 → sonnet
"""

import os
import subprocess
import tempfile

MODEL_SELECT = os.getenv("CLAUDE_MODEL_SELECT", "claude-haiku-4-5")
MODEL_EXPLAIN = os.getenv("CLAUDE_MODEL_EXPLAIN", "claude-opus-5")
MODEL_CARD = os.getenv("CLAUDE_MODEL_CARD", "claude-sonnet-5")

TIMEOUT_SEC = int(os.getenv("CLAUDE_TIMEOUT_SEC", "300"))

# 시스템 프롬프트를 통째로 대체한다. Claude Code의 기본 코딩 에이전트 프롬프트와
# CLAUDE.md가 프롬프트에 섞여 들어와 카드 내용을 오염시키는 것을 막는다.
SYSTEM_PROMPT = (
    "You are a content generation engine. Follow the output format specified "
    "in the user message exactly. Output only the requested content — no "
    "preamble, no commentary, no explanation of what you did."
)

# 순수 텍스트 생성이라 파일/쉘/웹 접근이 전혀 필요 없다. 도구를 막아
# 엉뚱한 tool call로 시간과 쿼터를 쓰는 것을 방지한다.
DISALLOWED_TOOLS = (
    "Bash,Read,Write,Edit,Glob,Grep,WebFetch,WebSearch,"
    "Task,NotebookEdit,TodoWrite"
)


def generate(prompt: str, model: str) -> str:
    """`claude -p`로 텍스트를 생성한다. 반환: 응답 텍스트.

    프롬프트는 argv가 아니라 stdin으로 넘긴다 (길이 제한 회피 +
    `--disallowedTools`가 variadic이라 argv 프롬프트를 삼키는 문제 회피).
    """
    cmd = [
        "claude",
        "-p",
        "--model", model,
        "--system-prompt", SYSTEM_PROMPT,
        "--output-format", "text",
        "--disallowedTools", DISALLOWED_TOOLS,
        "--no-session-persistence",  # CI에서 세션 파일을 남기지 않는다
        "--strict-mcp-config",       # 로컬 MCP 서버 설정을 무시
    ]

    # 빈 임시 디렉터리에서 실행: 프로젝트 CLAUDE.md 자동 탐색과
    # 저장소 파일 접근을 원천 차단한다.
    with tempfile.TemporaryDirectory() as workdir:
        try:
            proc = subprocess.run(
                cmd,
                input=prompt,
                capture_output=True,
                text=True,
                timeout=TIMEOUT_SEC,
                cwd=workdir,
            )
        except FileNotFoundError:
            raise RuntimeError(
                "`claude` CLI를 찾을 수 없습니다. "
                "npm i -g @anthropic-ai/claude-code 로 설치하세요."
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"claude 호출 타임아웃 ({TIMEOUT_SEC}s, model={model})")

    if proc.returncode != 0:
        stderr = (proc.stderr or "").strip()[-500:]
        raise RuntimeError(f"claude 호출 실패 (model={model}, exit={proc.returncode}): {stderr}")

    content = (proc.stdout or "").strip()
    if not content:
        raise RuntimeError(f"claude가 빈 응답을 반환했습니다 (model={model})")

    return content
