#!/usr/bin/env python3
"""01 트랙 docs 그림 — dual write 실패 두 경우 vs outbox. 실행: python3 -I docs/diagrams/draw_outbox.py (트랙 폴더에서)"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "tools"))
from diagram import Diagram, P, finish  # noqa: E402

OUT = pathlib.Path(__file__).parent


def outbox():
    d = Diagram("outbox-dual-write", 1400, 700, "DB 커밋과 메시지 발행 사이 — dual write 와 outbox",
                "왼쪽: 두 번 쓰면 어느 순서든 한쪽이 샌다. 오른쪽: DB 한 곳에만 쓰고 발행은 따로 한다", out=OUT)
    d.text(40, 96, "dual write — 한 요청이 DB 와 브로커에 따로 쓴다", 16, P["muted"], weight=700)
    d.card("c1", 40, 126, 620, 150, "경우 1  커밋 후 발행 전에 앱이 죽음",
           "1  DB 커밋 성공 (주문 저장됨)\n2  앱 크래시 / 브로커 장애\n3  메시지는 나가지 않는다\n결과: DB 에는 있고 이벤트는 영영 없다 (유실)",
           bg=P["note_bg"], stroke=P["orange"], title_size=16, body_size=14)
    d.card("c2", 40, 306, 620, 150, "경우 2  발행 후 커밋이 실패",
           "1  메시지 발행 성공 (소비자가 받음)\n2  DB 커밋 실패 / 롤백\n3  주문은 없는데 이벤트는 나갔다\n결과: 존재하지 않는 사건이 퍼진다 (유령 이벤트)",
           bg=P["note_bg"], stroke=P["orange"], title_size=16, body_size=14)
    d.card("why", 40, 486, 620, 150, "왜 못 막나",
           "DB 트랜잭션과 브로커 발행은 서로 다른 시스템이라\n하나의 원자적 커밋으로 묶이지 않는다\nKafka 트랜잭션은 Kafka 안(오프셋 · 토픽 쓰기)만 묶는다",
           bg=P["white"], stroke=P["line"], title_size=16, body_size=14)
    d.text(740, 96, "outbox — 발행할 것을 같은 트랜잭션에 DB 행으로 쓴다", 16, P["muted"], weight=700)
    d.card("tx", 740, 126, 620, 150, "DB 한 트랜잭션 (원자적)",
           "INSERT orders ...\nINSERT outbox (id, aggregate_id, type, payload)\nCOMMIT  — 둘 다 남거나 둘 다 없다",
           bg=P["ok_bg"], stroke=P["green"], title_size=16, body_size=14)
    d.card("rl", 740, 336, 290, 140, "릴레이 (별도 프로세스)",
           "폴링: SELECT ... FOR UPDATE\nSKIP LOCKED\nCDC: WAL 논리 디코딩",
           bg=P["as_bg"], stroke=P["front"], title_size=16, body_size=14)
    d.card("kf", 1070, 336, 290, 140, "Kafka",
           "key = aggregate_id\n같은 키는 같은 파티션\n릴레이 중복 → 중복 전달",
           bg=P["bff_bg"], stroke=P["back"], title_size=16, body_size=14)
    d.card("cs", 740, 536, 620, 100, "소비자 — at-least-once 라 멱등 처리 (01.05 inbox · version)",
           "릴레이가 발행 후 표시 전에 죽으면 같은 메시지가 두 번 나간다",
           bg=P["white"], stroke=P["line"], title_size=15, body_size=14)
    d.arrow([d.anchor("tx", "s", 0.25), d.anchor("rl", "n", 0.5)], P["green"], "읽는다", start="tx", end="rl")
    d.arrow([d.anchor("rl", "e"), d.anchor("kf", "w")], P["front"], "발행", start="rl", end="kf")
    d.arrow([d.anchor("kf", "s", 0.5), d.anchor("cs", "n", 0.8)], P["back"], None, start="kf", end="cs")
    d.save()


if __name__ == "__main__":
    outbox()
    finish()
