#!/usr/bin/env python3
"""01.03 docs 그림. 실행: python3 -I docs/diagrams/draw.py (레슨 폴더에서)"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[4] / "tools"))
from diagram import Diagram, P, finish  # noqa: E402

OUT = pathlib.Path(__file__).parent


def key_race():
    d = Diagram("key-race", 1400, 760, "같은 키로 두 요청이 부딪힐 때 — 한 트랜잭션 설계, READ COMMITTED",
                "B 의 INSERT 는 A 의 트랜잭션이 끝날 때까지 기다린다. 끝나는 방식이 B 의 운명을 정한다 (PostgreSQL 16 실측)", out=OUT)
    d.text(60, 112, "요청 A", 17, P["front"], weight=700)
    d.text(740, 112, "요청 B  (같은 키)", 17, P["back"], weight=700)
    d.card("a1", 40, 150, 560, 70, "1. BEGIN · INSERT … ON CONFLICT DO NOTHING",
           "영향 행 1 = 선점. 아직 커밋 전", bg=P["as_bg"], stroke=P["front"], title_size=15, body_size=13)
    d.card("a2", 40, 270, 560, 70, "2. 외부 결제 호출 · payments INSERT · 키를 DONE 으로",
           "이 사이 내내 B 는 기다린다", bg=P["as_bg"], stroke=P["front"], title_size=15, body_size=13)
    d.card("b1", 740, 210, 620, 90, "1'. BEGIN · 같은 INSERT … ON CONFLICT DO NOTHING",
           "멈춘다: wait_event = transactionid\nA 의 트랜잭션 ID 를 ShareLock 으로 기다리는 중 (pg_locks)",
           bg=P["todo_bg"], stroke=P["orange"], title_size=15, body_size=13)
    d.arrow([d.anchor("a1", "e", 0.5), d.anchor("b1", "w", 0.3)], P["muted"], "충돌 발견", start="a1", end="b1")
    d.arrow([d.anchor("a1", "s"), d.anchor("a2", "n")], P["muted"], start="a1", end="a2")
    d.pill("end", 150, 400, 340, 50, "A 의 트랜잭션이 끝난다", P["note_bg"], P["muted"], size=15)
    d.arrow([d.anchor("a2", "s"), d.anchor("end", "n")], P["muted"], start="a2", end="end")
    d.card("c", 40, 500, 640, 200, "COMMIT 으로 끝났다",
           "B 의 INSERT 가 풀리며 영향 행 0 (INSERT 0 0)\n-> 선점 실패 -> 저장된 응답을 읽어 돌려준다 (replay)\n"
           "ON CONFLICT 없이 INSERT 했다면 23505",
           bg=P["ok_bg"], stroke=P["green"], title_size=16, body_size=14)
    d.card("r", 720, 500, 640, 200, "ROLLBACK 으로 끝났다",
           "충돌하던 항목이 사라진다 -> B 의 INSERT 가 성공 (영향 행 1)\n-> B 가 선점자가 되어 직접 처리한다\n"
           "이것이 \"실패한 요청은 같은 키로 다시 시도할 수 있다\" 의 정체",
           bg=P["ok_bg"], stroke=P["green"], title_size=16, body_size=14)
    d.arrow([d.anchor("end", "s", 0.3), d.anchor("c", "n", 0.6)], P["green"], "COMMIT", start="end", end="c")
    d.arrow([d.anchor("end", "s", 0.7), d.anchor("r", "n", 0.4)], P["green"], "ROLLBACK", start="end", end="r")
    d.save()


def key_states():
    d = Diagram("key-states", 1400, 800, "멱등 키의 상태 — 키를 먼저 커밋하는 2-트랜잭션 설계",
                "(해석) 한 트랜잭션 설계에서는 '처리 중' 이 커밋되지 않으므로 상태 열이 사실상 DONE 하나뿐이다", out=OUT)
    d.pill("none", 40, 330, 190, 60, "키 없음", P["note_bg"], P["muted"], size=16)
    d.pill("prog", 480, 330, 220, 60, "IN_PROGRESS", P["todo_bg"], P["orange"], size=16)
    d.pill("done", 860, 200, 200, 60, "DONE (응답 저장)", P["ok_bg"], P["green"], size=15)
    d.pill("fail", 860, 460, 200, 60, "FAILED", P["bad_bg"], P["red"], size=16)
    d.pill("exp", 1160, 330, 200, 60, "만료 · 삭제", P["note_bg"], P["muted"], size=16)
    d.arrow([d.anchor("none", "e"), d.anchor("prog", "w")], P["front"], "tx1: INSERT … ON CONFLICT\nDO NOTHING = 1행, 커밋", start="none", end="prog")
    d.arrow([d.anchor("prog", "e", 0.3), d.anchor("done", "w")], P["green"], "tx2: 처리 성공\n응답 저장", start="prog", end="done")
    d.arrow([d.anchor("prog", "e", 0.7), d.anchor("fail", "w")], P["red"], "tx2: 처리 실패\n(저장할지는 계약)", start="prog", end="fail")
    d.arrow([d.anchor("done", "e"), d.anchor("exp", "n", 0.3)], P["muted"], "보존 기간 경과", start="done", end="exp")
    d.arrow([d.anchor("fail", "e"), d.anchor("exp", "s", 0.3)], P["muted"], start="fail", end="exp")
    d.card("lease", 40, 560, 620, 200, "서버가 죽으면 IN_PROGRESS 가 영영 남는다",
           "그래서 만료 시각(lease)이 필요하다. 지나면 다른 요청이 인수한다\n"
           "인수는 한 문장으로 원자적이어야 한다:\n"
           "UPDATE … WHERE status = 'IN_PROGRESS' AND 만료 < now() 의 영향 행 수로 판정",
           bg=P["bad_bg"], stroke=P["red"], title_size=15, body_size=13)
    d.card("same", 700, 560, 660, 200, "IN_PROGRESS 인 키로 또 요청이 오면 (선택)",
           "기다린다: 커넥션을 쥔 채 완료를 폴링 — 구현이 무겁다\n"
           "409 로 돌려보낸다: 클라이언트가 나중에 재시도 (IETF 초안의 권고)\n"
           "요청 해시가 다르면: 처리 중 여부와 무관하게 거절 (초안: 422)",
           bg=P["note_bg"], stroke=P["line"], title_size=15, body_size=13)
    d.save()


if __name__ == "__main__":
    key_race()
    key_states()
    finish()
