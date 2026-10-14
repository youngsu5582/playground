#!/usr/bin/env bash
set -euo pipefail

# 목적: 테스트의 context.close() 가 아니라 진짜 SIGTERM 으로 종료 순서를 본다.
#       SIGTERM → JVM shutdown hook(SpringContextShutdownHook 스레드) → context.close()
#
# 사용:
#   ./scripts/02-sigterm-demo.sh wait      # PR 4341 설정 → Redis 호출이 중간부터 실패
#   ./scripts/02-sigterm-demo.sh default   # 설정 없음 → ② 에서 실행 중 작업을 기다려 줌
#   ./scripts/02-sigterm-demo.sh drain     # PR 플래그 + IdleDrainLifecycle → 끝까지 성공
#
# 환경변수:
#   KILL_AFTER_SEC  시작 후 몇 초 뒤 SIGTERM 을 보낼지 (기본 2)
#
# [앱 필요] 이 스크립트가 직접 빌드(installDist)하고 실행한다.

SCENARIO="${1:-wait}"
KILL_AFTER_SEC="${KILL_AFTER_SEC:-2}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

(cd "${ROOT_DIR}/app" && ./gradlew -q installDist)
BIN="${ROOT_DIR}/app/build/install/spring-shutdown-playground/bin/spring-shutdown-playground"

# 시작 스크립트가 exec java 로 끝나므로 $! 가 곧 JVM 의 PID 다
"${BIN}" "${SCENARIO}" &
PID=$!

sleep "${KILL_AFTER_SEC}"
echo ">>> kill -TERM ${PID}"
kill -TERM "${PID}"

# SIGTERM 으로 끝난 JVM 의 종료 코드는 143 이라 실패로 치지 않는다
wait "${PID}" || true
echo ">>> 종료됨"
