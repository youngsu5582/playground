#!/usr/bin/env bash
# 목적: 관찰용 PostgreSQL 16 을 띄운다 (localhost:55432, lab/lab). seed.sql 이 테이블을 만든다.
# 사용: observe/up.sh   →   터미널 두 개에서 observe/psql.sh A · observe/psql.sh B
set -euo pipefail
cd "$(dirname "$0")"
docker compose up -d
for i in $(seq 1 30); do
  docker exec deepdive-01.01-pg pg_isready -h 127.0.0.1 -U lab -d lab >/dev/null 2>&1 && { echo "ready — 다음: SCRIPT.md"; exit 0; }
  sleep 1
done
echo "30초 안에 준비되지 않았다: docker compose logs" >&2; exit 1
