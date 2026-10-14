#!/usr/bin/env bash
set -euo pipefail

# 목적: 스테이지별로 남은 예측(todo())과 IdleDrainLifecycle 구현 여부를 센다. 전부 0 이면 끝.
#
# 사용: ./scripts/03-progress.sh
# [앱 필요] 없음

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEST_DIR="${ROOT_DIR}/app/src/test/java/playground/shutdown"
DRAIN_FILE="${ROOT_DIR}/app/src/main/java/playground/shutdown/drain/IdleDrainLifecycle.java"

printf "%-8s %6s %8s  %s\n" "STAGE" "TESTS" "todo()" "상태"
printf "%s\n" "──────────────────────────────────────"
total=0
for n in 2 3 4; do
    dir="${TEST_DIR}/stage${n}"
    tests=$(grep -rhc '@Test' "${dir}" | awk '{s+=$1} END{print s+0}')
    todos=$(grep -rho 'isEqualTo(todo())' "${dir}" | wc -l | tr -d ' ')
    total=$((total + todos))
    if [ "${todos}" -eq 0 ]; then state="✅ 완료"; else state="⏳ 진행"; fi
    printf "%-8s %6s %8s  %s\n" "s${n}" "${tests}" "${todos}" "${state}"
done
printf "%s\n" "──────────────────────────────────────"
echo "남은 예측: ${total}"

if grep -q 'TODO 직접 구현한다' "${DRAIN_FILE}"; then
    echo "IdleDrainLifecycle: ⏳ 아직 뼈대 (통과 기준: T-07e · T-08c · T-09b)"
else
    echo "IdleDrainLifecycle: ✅ 구현됨"
fi
echo
echo "  테스트 하나:  ./gradlew s2 --tests '*waitsForRunningTaskInLifecycle'"
echo "  정답 보기:    git diff HEAD~1 -- app/src   (막혔을 때만)"
