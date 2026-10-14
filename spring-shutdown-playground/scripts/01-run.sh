#!/usr/bin/env bash
set -euo pipefail

# 목적: 스테이지 하나를 돌리고 타임라인을 콘솔에 그대로 보여 준다.
#
# 사용:
#   ./scripts/01-run.sh s1     # 종료 3단계 (T-01 ~ T-03)
#   ./scripts/01-run.sh s2     # 풀 2개의 설정별 동작 (T-04 ~ T-06)
#   ./scripts/01-run.sh s3     # 의존 자원 (T-07)
#   ./scripts/01-run.sh s4     # 비동기 체인 (T-08)
#   ./scripts/01-run.sh s5     # 진짜 Lettuce + Redis 컨테이너 (T-09, Docker 필요)
#   ./scripts/01-run.sh test   # 전체
#
# 타임라인 줄은 "timeline [경과ms] [스레드] 이벤트", Spring 자신의 로그는 "spring [스레드] …" 로 시작한다.
# [앱 필요] 없음

STAGE="${1:-s1}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}/app"
exec ./gradlew "${STAGE}" --console=plain
