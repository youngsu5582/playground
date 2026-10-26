#!/usr/bin/env bash
# 목적: 관찰용 컨테이너를 지운다 (볼륨 포함 — 다시 up 하면 seed 부터 새로).
set -euo pipefail
cd "$(dirname "$0")"
docker compose down -v
