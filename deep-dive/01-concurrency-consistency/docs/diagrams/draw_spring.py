#!/usr/bin/env python3
"""05-spring-jpa-mapping 그림 — SQLSTATE 가 Spring 예외로 번역되는 길. 실행: python3 -I docs/diagrams/draw_spring.py (트랙 폴더에서)"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "tools"))
from diagram import Diagram, P, finish  # noqa: E402

OUT = pathlib.Path(__file__).parent

ROWS = [
    ("23505 유니크 위반", "DuplicateKeyException", "DataIntegrityViolationException", "NonTransient (재시도 대상 아님)", P["note_bg"], P["muted"]),
    ("40001 직렬화 실패", "CannotAcquireLockException", "CannotAcquireLockException", "Pessimistic < Concurrency < Transient", P["rs_bg"], P["orange"]),
    ("40P01 데드락", "PessimisticLockingFailureException", "CannotAcquireLockException", "Pessimistic < Concurrency < Transient", P["rs_bg"], P["orange"]),
    ("55P03 락 대기 실패", "UncategorizedSQLException", "PessimisticLockingFailureException", "JDBC 는 NonTransient / JPA 는 Transient", P["as_bg"], P["front"]),
    ("@Version 충돌", "(해당 없음)", "ObjectOptimisticLockingFailureException", "Optimistic < Concurrency < Transient", P["ok_bg"], P["green"]),
]


def mapping():
    d = Diagram("spring-exception-map", 1500, 620, "SQLSTATE 가 Spring 예외가 되는 길 (Spring 6.2.19 · Hibernate 6.6.53 · PostgreSQL 16.14 실측)",
                "같은 SQLSTATE 라도 JdbcTemplate 경로와 JPA 경로의 예외 클래스가 다르다 — 그래서 SQLState 를 cause 에서 읽는 편이 안전하다", out=OUT)
    d.text(40, 96, "DB 가 보낸 것", 15, P["muted"], weight=700)
    d.text(300, 96, "JdbcTemplate 경로", 15, P["muted"], weight=700)
    d.text(700, 96, "JPA · Spring Data 경로", 15, P["muted"], weight=700)
    d.text(1100, 96, "상위 갈래 (JPA 경로 기준)", 15, P["muted"], weight=700)
    y = 122
    for i, (sq, jd, jp, grp, bg, st) in enumerate(ROWS):
        d.pill(f"q{i}", 40, y, 230, 80, sq, bg, st, size=15)
        d.pill(f"j{i}", 300, y, 370, 80, jd, P["white"], P["line"], size=13)
        d.pill(f"p{i}", 700, y, 370, 80, jp, P["white"], P["line"], size=13)
        d.pill(f"g{i}", 1100, y, 360, 80, grp, P["note_bg"], P["muted"], size=13)
        d.arrow([d.anchor(f"q{i}", "e"), d.anchor(f"j{i}", "w")], P["muted"], start=f"q{i}", end=f"j{i}")
        d.arrow([d.anchor(f"j{i}", "e"), d.anchor(f"p{i}", "w")], P["muted"], dashed=True, start=f"j{i}", end=f"p{i}")
        d.arrow([d.anchor(f"p{i}", "e"), d.anchor(f"g{i}", "w")], P["muted"], dashed=True, start=f"p{i}", end=f"g{i}")
        y += 100
    d.save()


if __name__ == "__main__":
    mapping()
    finish()
