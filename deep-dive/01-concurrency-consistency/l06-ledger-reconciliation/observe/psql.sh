#!/usr/bin/env bash
# 목적: 이름 붙은 psql 세션을 연다. 프롬프트에 세션 이름 · 트랜잭션 상태가 보인다.
# 사용: observe/psql.sh A     (다른 터미널에서 observe/psql.sh B)
# 로컬 psql 이 없어도 된다 — 컨테이너 안의 psql 을 쓴다.
set -euo pipefail
NAME="${1:-A}"
exec docker exec -it deepdive-01.06-pg psql -U lab -d lab \
  -v "PROMPT1=${NAME} %x%# " -v "PROMPT2=${NAME} %x%# " -v ON_ERROR_ROLLBACK=off
