#!/usr/bin/env python3
"""01.03 블로그판 05 그림. 실행: python3 -I docs/diagrams/draw_blog05.py (레슨 폴더에서)"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[4] / "tools"))
from diagram import Diagram, P, finish  # noqa: E402

OUT = pathlib.Path(__file__).parent


def intro():
    d = Diagram("blog05-intro", 1360, 520, "도입: 예외는 잡았는데, 다음 문장이 안 된다",
                "한 트랜잭션 안에서 같은 키를 두 번 INSERT 했다. 자바 쪽과 DB 쪽은 서로 다른 것을 알고 있다", out=OUT)
    d.text(40, 112, "자바 (앱) 가 아는 것", 16, P["front"], weight=700)
    d.text(40, 312, "DB 쪽 트랜잭션의 상태", 16, P["red"], weight=700)
    xs = [40, 480, 920]
    d.card("j1", xs[0], 140, 400, 120, "1  INSERT … ('k1')", "이미 있는 키라서\n유니크 위반 23505 가 난다",
           bg=P["as_bg"], stroke=P["front"], title_size=15, body_size=14)
    d.card("j2", xs[1], 140, 400, 120, "2  catch (중복 키 예외)", "자바의 try/catch 는\n자바의 흐름을 복구했다",
           bg=P["as_bg"], stroke=P["front"], title_size=15, body_size=14)
    d.card("j3", xs[2], 140, 400, 120, "3  SELECT payload WHERE key = 'k1'", "기존 행을 읽어 돌려주려 한다",
           bg=P["as_bg"], stroke=P["front"], title_size=15, body_size=14)
    d.pill("b1", xs[0], 340, 400, 70, "에러가 났다 — 문장 하나 실패", P["bad_bg"], P["red"], size=15)
    d.pill("b2", xs[1], 340, 400, 70, "트랜잭션 전체가 중단 상태 (aborted)", P["bad_bg"], P["red"], size=15)
    d.pill("b3", xs[2], 340, 400, 70, "이 문장은 받아 줄까 ?", P["todo_bg"], P["orange"], size=15)
    d.arrow([d.anchor("j1", "e"), d.anchor("j2", "w")], P["muted"], "예외로\n전달", start="j1", end="j2")
    d.arrow([d.anchor("j2", "e"), d.anchor("j3", "w")], P["muted"], "이어서\n보낸다", start="j2", end="j3")
    d.arrow([d.anchor("b1", "e"), d.anchor("b2", "w")], P["red"], "그대로\n굳는다", start="b1", end="b2")
    d.arrow([d.anchor("b2", "e"), d.anchor("b3", "w")], P["red"], "", start="b2", end="b3")
    d.arrow([d.anchor("j1", "s", 0.85), d.anchor("b1", "n", 0.85)], P["red"], "DB 가 표시", start="j1", end="b1")
    d.card("v", 40, 440, 1280, 50, "자바는 예외를 잡았지만, DB 쪽 트랜잭션은 이미 죽어 있다",
           None, bg=P["note_bg"], stroke=P["line"], title_size=16)
    d.save()


def tx_states():
    d = Diagram("blog05-tx-states", 1360, 600, "트랜잭션의 두 상태 — 정상과 중단",
                "문장 하나가 에러를 내면 트랜잭션 전체가 중단 상태가 되고, 풀어 주는 명령이 나올 때까지 이후 문장은 모두 거절된다", out=OUT)
    d.pill("ok", 40, 200, 230, 70, "정상 (active)", P["ok_bg"], P["green"], size=17)
    d.pill("ab", 520, 200, 260, 70, "중단 상태 (aborted)", P["bad_bg"], P["red"], size=17)
    d.pill("free", 1030, 200, 290, 70, "거절이 풀리는 지점", P["note_bg"], P["muted"], size=16)
    d.arrow([d.anchor("ok", "e"), d.anchor("ab", "w")], P["red"], "문장 하나가 에러\n(어떤 에러든)", start="ok", end="ab")
    d.arrow([d.anchor("ab", "e"), d.anchor("free", "w")], P["muted"],
            "ROLLBACK 또는\nROLLBACK TO SAVEPOINT", start="ab", end="free")
    d.card("rej", 520, 360, 260, 110, "그 사이에 보낸 문장", "SELECT 든 INSERT 든 모두\n거절된다 (전용 SQLSTATE)",
           bg=P["bad_bg"], stroke=P["red"], title_size=15, body_size=14)
    d.arrow([d.anchor("ab", "s"), d.anchor("rej", "n")], P["red"], "무엇을 보내도", start="ab", end="rej")
    d.card("any", 40, 360, 440, 140, "어떤 에러든 중단 상태를 만든다",
           "유니크 위반 (23505) 만이 아니다\nlock_timeout 으로 대기가 취소된 문장 뒤에도\n같은 트랜잭션의 다음 문장이 거절됐다\n(실측: psql 2026-10-13)",
           bg=P["todo_bg"], stroke=P["orange"], title_size=15, body_size=14)
    d.arrow([d.anchor("any", "n", 0.5), d.anchor("ok", "s", 0.5)], P["orange"], "같은 규칙", start="any", end="ok")
    d.save()


def savepoint():
    d = Diagram("blog05-savepoint", 1360, 700, "SAVEPOINT — 실패한 문장 하나만 되돌린다",
                "표시를 만들고, 그 뒤의 명령을 되돌려 표시 시점의 상태로 복원한다. 되돌린 뒤 이어 쓸 수 있는가는 직접 예측해 보자", out=OUT)
    rows = [("BEGIN", "트랜잭션 시작", None),
            ("SAVEPOINT sp", "표시를 만든다", "mark"),
            ("INSERT INTO idem (key, payload) VALUES ('k1', 'second')", "중복 키 에러 — 이 문장은 실패한다", "bad"),
            ("ROLLBACK TO SAVEPOINT sp", "표시 이후의 변경이 되돌려진다", "mark"),
            ("SELECT payload FROM idem WHERE key = 'k1'", "기존 값을 읽을 수 있나?  (Q10 — 예측)", "q"),
            ("COMMIT", "", None)]
    y0, pitch, h = 120, 92, 68
    for i, (sql, note, kind) in enumerate(rows):
        bg, st = {None: (P["note_bg"], P["muted"]), "mark": (P["as_bg"], P["front"]),
                  "bad": (P["bad_bg"], P["red"]), "q": (P["todo_bg"], P["orange"])}[kind]
        d.card(f"r{i}", 40, y0 + i * pitch, 820, h, sql, note or None, bg=bg, stroke=st, title_size=15, body_size=14)
        if i:
            d.arrow([d.anchor(f"r{i-1}", "s", 0.1), d.anchor(f"r{i}", "n", 0.1)], P["muted"], start=f"r{i-1}", end=f"r{i}")
    yb0, yb1 = y0 + 1 * pitch + h / 2, y0 + 3 * pitch + h / 2
    d.line([(890, yb0), (930, yb0), (930, yb1), (890, yb1)], P["front"], dashed=False, sw=3)
    d.card("rng", 960, y0 + 1 * pitch + 60, 360, 90, "되돌려지는 범위",
           "SAVEPOINT 표시 이후에\n실행한 모든 명령",
           bg=P["white"], stroke=P["front"], title_size=15, body_size=13)
    d.save()


def three_ways():
    d = Diagram("blog05-three-ways", 1360, 390, "중복 키를 만난 뒤 기존 행을 읽는 세 가지 길",
                "에러를 내고 수습하느냐, 에러가 나는 경로 자체를 없애느냐", out=OUT)
    specs = [("일반 INSERT → 에러 catch", "에러: 난다\n트랜잭션: Q09 에서 확인\n추가 왕복: 롤백 후 재시작 필요", P["bad_bg"], P["red"]),
             ("SAVEPOINT 로 감싼 INSERT", "에러: 난다 (취소됨)\n트랜잭션: Q10 에서 확인\n추가 왕복: SAVEPOINT · ROLLBACK TO 두 문장", P["todo_bg"], P["orange"]),
             ("INSERT … ON CONFLICT DO NOTHING", "에러: 안 난다\n트랜잭션: 계속 사용\n추가 왕복: 없음\n이 레슨의 PaymentService 가 쓰는 방법", P["ok_bg"], P["green"])]
    for i, (t, b, bg, st) in enumerate(specs):
        d.card(f"c{i}", 40 + i * 440, 120, 410, 130, t, b, bg=bg, stroke=st, title_size=16, body_size=14)
    d.card("n", 40, 290, 1290, 60, "세 번째는 에러가 없으니 트랜잭션이 중단되지 않고 바로 SELECT 를 이어 할 수 있다",
           None, bg=P["note_bg"], stroke=P["line"], title_size=15)
    d.save()


def on_conflict_scope():
    d = Diagram("blog05-on-conflict-scope", 1360, 410, "ON CONFLICT 가 다루는 것은 그 충돌뿐이다",
                "다른 에러는 여전히 에러이고, 난 순간 트랜잭션을 중단시킨다", out=OUT)
    d.card("ok", 40, 130, 380, 130, "ON CONFLICT DO NOTHING", "그 유니크 충돌의 에러 (23505) 만\n나지 않게 한다",
           bg=P["ok_bg"], stroke=P["green"], title_size=16, body_size=14)
    specs = [("다른 제약 위반", ""), ("직렬화 실패  40001", "격리수준 표 (문서 04)"), ("락 타임아웃  55P03", "lock_timeout")]
    for i, (t, b) in enumerate(specs):
        d.card(f"e{i}", 520 + i * 270, 130, 250, 130, t, b or None, bg=P["bad_bg"], stroke=P["red"], title_size=15, body_size=13)
    d.card("n", 520, 290, 790, 90, "여전히 에러이고, 트랜잭션을 중단 상태로 만든다",
           "ON CONFLICT 로 바꾸면 모든 에러가 사라진다는 말은 틀린다 — 그 충돌만 사라진다",
           bg=P["note_bg"], stroke=P["line"], title_size=15, body_size=14)
    d.save()


def app_layers():
    d = Diagram("blog05-app-layers", 1400, 640, "앱 층에서 \"aborted\" 를 만나는 세 걸음과 빠져나가는 길",
                "로그에는 처음의 에러가 아니라 뒤쪽 에러가 남을 수 있어 원인 찾기가 어렵다 (해석)", out=OUT)
    steps = [("1  INSERT 가 23505 를 던진다", "JDBC 는 SQLException, Spring 은\nDuplicateKeyException 등으로 번역한다 (문서 07)", P["as_bg"], P["front"]),
             ("2  앱이 예외를 잡고 같은 커넥션에서 SELECT", "이 SELECT 가 어떻게 되는지는 Q09 로 예측한다\n뒤쪽의 \"aborted\" 에러가 처음의 23505 대신\n로그에 남을 수 있다 (해석)", P["bad_bg"], P["red"]),
             ("3  메서드가 예외로 끝난다", "트랜잭션이 롤백된다 —\n앞서 한 쓰기도 함께 사라진다", P["note_bg"], P["muted"])]
    for i, (t, b, bg, st) in enumerate(steps):
        d.card(f"s{i}", 40, 120 + i * 150, 640, 120, t, b, bg=bg, stroke=st, title_size=15, body_size=14)
        if i:
            d.arrow([d.anchor(f"s{i-1}", "s", 0.2), d.anchor(f"s{i}", "n", 0.2)], P["muted"], start=f"s{i-1}", end=f"s{i}")
    d.text(760, 112, "빠져나가는 길", 16, P["green"], weight=700)
    outs = [("에러가 안 나는 문장으로 바꾼다", "ON CONFLICT DO NOTHING"),
            ("실패한 문장만 SAVEPOINT 로 격리한다", "ROLLBACK TO SAVEPOINT 후 이어 간다"),
            ("예외를 트랜잭션 밖에서 잡는다", "새 트랜잭션으로 다시 시도한다")]
    for i, (t, b) in enumerate(outs):
        d.card(f"o{i}", 760, 140 + i * 130, 600, 100, t, b, bg=P["ok_bg"], stroke=P["green"], title_size=15, body_size=14)
    d.save()


if __name__ == "__main__":
    for f in (intro, tx_states, savepoint, three_ways, on_conflict_scope, app_layers):
        f()
    finish()
