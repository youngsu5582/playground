#!/usr/bin/env python3
"""01 트랙 공통 docs 그림 — 문제 모양에서 도구 고르기. 실행: python3 -I docs/diagrams/draw_decision.py (트랙 폴더에서)"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "tools"))
from diagram import Diagram, P, finish  # noqa: E402

OUT = pathlib.Path(__file__).parent

ROWS = [
    ("같은 행 증감\n(재고 · 잔고)", "원자 조건부 UPDATE", "영향 행 0 = 조건 불충족(품절)", "01.04 문서 02", P["ok_bg"], P["green"]),
    ("읽고 판단해 다른 행 쓰기\n(당직 · 한도)", "SERIALIZABLE + 전체 재시도", "40001", "01.01 문서 05", P["rs_bg"], P["orange"]),
    ("읽고 복잡히 계산해\n같은 행 쓰기", "SELECT FOR UPDATE (비관 락)", "락 대기 · 40P01", "01.04 문서 03", P["as_bg"], P["front"]),
    ("같은 요청 두 번\n(멱등)", "유니크 키 + ON CONFLICT DO NOTHING", "영향 행 0 = 이미 선점", "01.03 문서 04 · 06", P["ok_bg"], P["green"]),
    ("작업 큐에서\n하나씩 집기", "FOR UPDATE SKIP LOCKED", "잠긴 행은 건너뜀", "01.02 문서 03", P["as_bg"], P["front"]),
    ("여러 행을 잠그는\n이체", "id 순서로 잠그기 (예방)", "40P01 (순서 어긋남)", "01.02 문서 05", P["as_bg"], P["front"]),
    ("이벤트 중복 ·\n순서 역전", "inbox PK + version 조건부 upsert", "영향 행 0 = 중복 · STALE", "01.05 문서 03 · 04", P["ok_bg"], P["green"]),
]


def decision():
    d = Diagram("decision-map", 1440, 840, "동시성 문제의 모양에서 도구 고르기 (PostgreSQL 16 기본 READ COMMITTED 기준)",
                "왼쪽이 문제, 가운데가 기본 선택, 오른쪽이 실패했다는 신호. 40001 · 40P01 이 나면 트랜잭션 전체 재시도", out=OUT)
    d.text(40, 96, "문제의 모양", 15, P["muted"], weight=700)
    d.text(470, 96, "기본 선택", 15, P["muted"], weight=700)
    d.text(900, 96, "실패 신호", 15, P["muted"], weight=700)
    d.text(1170, 96, "원리가 있는 곳", 15, P["muted"], weight=700)
    y = 122
    for i, (prob, tool, sig, where, bg, st) in enumerate(ROWS):
        d.pill(f"p{i}", 40, y, 380, 74, prob, P["note_bg"], P["muted"], size=15)
        d.pill(f"t{i}", 470, y, 380, 74, tool, bg, st, size=15)
        d.pill(f"s{i}", 900, y, 240, 74, sig, P["white"], P["line"], size=14)
        d.text(1170, y + 28, where, 14, P["ink"])
        d.arrow([d.anchor(f"p{i}", "e"), d.anchor(f"t{i}", "w")], P["muted"], start=f"p{i}", end=f"t{i}")
        d.arrow([d.anchor(f"t{i}", "e"), d.anchor(f"s{i}", "w")], P["muted"], dashed=True, start=f"t{i}", end=f"s{i}")
        y += 94
    d.save()


if __name__ == "__main__":
    decision()
    finish()
