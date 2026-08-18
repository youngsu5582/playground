#!/usr/bin/env bash
set -euo pipefail

# 목적: 스테이지 하나를 60분 타임박스로 시작한다.
#       구간 알림(질문 마감 / 테스트 착수 / 정리 시작)을 백그라운드로 띄우고,
#       현재 red 상태를 먼저 보여준다.
#
# 사용:
#   ./scripts/01-drill.sh 3            # stage3, 60분
#   MINUTES=45 ./scripts/01-drill.sh 1 # stage1, 45분
#   NOTIFY=0 ./scripts/01-drill.sh 2   # 알림 없이
#
# 환경변수:
#   MINUTES  기본 60   전체 타임박스(분)
#   NOTIFY   기본 1    macOS 알림 사용 여부 (0이면 표준출력만)

STAGE="${1:-}"
MINUTES="${MINUTES:-60}"
NOTIFY="${NOTIFY:-1}"

if [[ ! "$STAGE" =~ ^[1-5]$ ]]; then
    echo "사용: $0 <스테이지 1-5>" >&2
    echo "  예: $0 3" >&2
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="${SCRIPT_DIR}/../app"

declare_topic() {
    case "$1" in
        1) echo "상태 전이 — 규칙을 데이터로" ;;
        2) echo "멱등성 — 같은 요청이 두 번 오면" ;;
        3) echo "동시성 — 초과 예약 0건" ;;
        4) echo "이벤트 — 중복과 순서 역전" ;;
        5) echo "우선순위 — 정렬은 비즈니스 규칙" ;;
    esac
}

notify() {
    local msg="$1"
    echo ""
    echo "⏰ $msg"
    if [[ "$NOTIFY" == "1" ]] && command -v osascript >/dev/null 2>&1; then
        osascript -e "display notification \"${msg}\" with title \"drill stage${STAGE}\"" 2>/dev/null || true
    fi
}

# 구간 알림 (분 단위). 10-timeboxed-drill.md 의 타임박스와 정렬된다.
schedule_marks() {
    local q=$((MINUTES * 10 / 60))    # 질문 마감      = 10/60
    local t=$((MINUTES * 20 / 60))    # 테스트 착수    = 20/60
    local w=$((MINUTES * 50 / 60))    # 정리 시작      = 50/60
    (
        sleep $((q * 60)); notify "질문 마감 — 이제 뼈대를 짠다 (${q}분 경과)"
        sleep $(((t - q) * 60)); notify "테스트 착수 — 정상 케이스 1개 먼저 (${t}분 경과)"
        sleep $(((w - t) * 60)); notify "손 떼고 정리 — 복잡도 + 실서비스 확장을 말로 (${w}분 경과)"
        sleep $(((MINUTES - w) * 60)); notify "종료 (${MINUTES}분)"
    ) &
    echo "$!"
}

cat <<BANNER

┌─────────────────────────────────────────────────────────
│  stage${STAGE} — $(declare_topic "$STAGE")
│  타임박스 ${MINUTES}분
└─────────────────────────────────────────────────────────

  0-5분    요구사항을 내 말로 재진술한다
  5-10분   애매한 조건 2~3개를 질문한다 (중복/순서/동시성/실패/경계)
  10-20분  타입과 정상 경로만. 추상화 금지
  20-35분  테스트: 정상 → 거부 → 경계 → 동시성
  35-50분  중복·동시성·예외 보완
  50-60분  복잡도 + "실서비스라면" 을 소리 내어 말한다

  노트: docs/0${STAGE}-*.md  (구현이 끝난 뒤에 연다)
  검증: ./gradlew s${STAGE}

BANNER

echo "── 현재 상태 ──────────────────────────────────────────"
# -q 를 쓰면 testLogging 이벤트까지 억제되어 "BUILD FAILED" 한 줄만 남는다.
# --console=plain 만 주고 테스트 라인을 직접 걸러낸다.
(cd "$APP_DIR" && ./gradlew "s${STAGE}" --console=plain 2>&1 \
    | grep -E "(PASSED|FAILED|SKIPPED)" \
    | grep -v "^> Task" \
    | sed 's/^/  /' \
    | head -20) || true
echo "───────────────────────────────────────────────────────"
echo ""

TIMER_PID=$(schedule_marks)
trap 'kill "$TIMER_PID" 2>/dev/null || true; echo ""; echo "타이머 종료."' EXIT INT TERM

echo "타이머 시작 (PID $TIMER_PID). 중단하려면 Ctrl-C."
echo "다른 터미널에서 구현하고, 여기서 알림을 받는다."
wait "$TIMER_PID" 2>/dev/null || true
