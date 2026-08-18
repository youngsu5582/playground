#!/usr/bin/env bash
set -euo pipefail

# 목적: 스테이지별 진행률을 한 화면에 보여준다.
#       남은 TODO 개수(구현), @Disabled 개수(직접 쓸 테스트), 테스트 통과 여부.
#
# 사용:
#   ./scripts/02-progress.sh               # 정적 카운트만 (빠름)
#   RUN_TESTS=1 ./scripts/02-progress.sh   # 테스트까지 실행 (느림)
#
# 환경변수:
#   RUN_TESTS  기본 0   1이면 gradle 테스트를 실제로 돌려 통과 여부를 표시
#
# 표 정렬은 ASCII 컬럼으로만 맞춘다 — 한글은 표시폭(2)과 바이트(3)가 달라
# printf 의 폭 지정이 어긋나므로, 한글 '주제' 는 항상 마지막 컬럼에 둔다.

RUN_TESTS="${RUN_TESTS:-0}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="${SCRIPT_DIR}/../app"
MAIN="${APP_DIR}/src/main/java/playground/orderflow"
TEST="${APP_DIR}/src/test/java/playground/orderflow"

# $1 = 디렉토리, $2 = 고정 문자열 패턴.
# 매치가 없으면 grep 이 1을 반환하고 pipefail 이 스크립트를 죽이므로 || true 로 흡수한다.
count_in() {
    local n
    n=$(grep -RhoF "$2" "$1" 2>/dev/null | wc -l | tr -d ' ') || true
    echo "${n:-0}"
}

topics=("상태 전이" "멱등성" "동시성·재고" "이벤트 순서" "우선순위 배분")

echo ""
if [[ "$RUN_TESTS" == "1" ]]; then
    printf "%-8s %6s %10s %8s  %s\n" "STAGE" "TODO" "TEST-TODO" "RESULT" "주제"
else
    printf "%-8s %6s %10s  %s\n" "STAGE" "TODO" "TEST-TODO" "주제"
fi
printf -- "─%.0s" {1..58}; echo ""

for n in 1 2 3 4 5; do
    todo=$(count_in "${MAIN}/stage${n}" 'UnsupportedOperationException("TODO')
    # '@Disabled(' 로 좁힌다 — Javadoc 안의 {@code @Disabled} 언급을 세지 않기 위해
    disabled=$(count_in "${TEST}/stage${n}" '@Disabled(')
    topic="${topics[$((n-1))]}"

    if [[ "$RUN_TESTS" == "1" ]]; then
        if (cd "$APP_DIR" && ./gradlew "s${n}" --console=plain -q >/dev/null 2>&1); then
            result="초록"
        else
            result="빨강"
        fi
        printf "%-8s %6s %10s %8s  %s\n" "stage${n}" "$todo" "$disabled" "$result" "$topic"
    else
        printf "%-8s %6s %10s  %s\n" "stage${n}" "$todo" "$disabled" "$topic"
    fi
done

printf -- "─%.0s" {1..58}; echo ""

total_todo=$(count_in "$MAIN" 'UnsupportedOperationException("TODO')
total_disabled=$(count_in "$TEST" '@Disabled(')
echo "남은 구현 ${total_todo}건 · 직접 쓸 테스트 ${total_disabled}건"
echo ""
echo "  드릴 시작:  ./scripts/01-drill.sh <1-5>"
echo "  회차 기록:  TESTING.md"
echo ""
