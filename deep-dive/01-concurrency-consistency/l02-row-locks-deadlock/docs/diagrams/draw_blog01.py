#!/usr/bin/env python3
"""01.02 블로그판 01 그림. 실행: python3 -I docs/diagrams/draw_blog01.py (레슨 폴더에서)"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[4] / "tools"))
from diagram import Diagram, P, finish, timeline as _timeline  # noqa: E402

OUT = pathlib.Path(__file__).parent


def timeline(*a, **k):
    return _timeline(*a, out=OUT, **k)


def intro():
    d = Diagram("blog01-intro", 1360, 520, "SELECT ... FOR UPDATE 한 줄이 잡는 락은 두 층이다",
                "읽기 쿼리처럼 보이지만, 테이블 수준과 행 수준에 각각 락 표시를 남긴다", out=OUT)
    d.card("q", 40, 120, 380, 150, "세션 A", "BEGIN;\nSELECT * FROM orders\n WHERE id = 7 FOR UPDATE;",
           bg=P["as_bg"], stroke=P["front"], title_size=17, body_size=15, mono_body=True)
    d.card("t", 560, 100, 760, 160, "층 1 — 테이블 수준: orders 에 ROW SHARE",
           "공유 메모리의 락 테이블에 올라간다\npg_locks 에 relation 락으로 보인다\n같은 테이블의 평범한 SELECT · UPDATE 와는 충돌하지 않는다",
           bg=P["note_bg"], stroke=P["line"], title_size=16, body_size=14)
    d.card("r", 560, 290, 760, 170, "층 2 — 행 수준: id = 7 튜플에 FOR UPDATE",
           "락 정보가 메모리가 아니라 디스크의 튜플 헤더(xmax)에 적힌다\npg_locks 에는 보통 안 나온다\n같은 행을 쓰려는 쪽 · 잠그려는 쪽만 막는다",
           bg=P["todo_bg"], stroke=P["orange"], title_size=16, body_size=14)
    d.arrow([(420, 170), (560, 170)], P["muted"], "한 줄이 두 층을", label_at=(490, 150))
    d.arrow([(420, 230), (490, 230), (490, 370), (560, 370)], P["orange"])
    d.text(40, 480, "이 글은 두 층을 차례로 본다. 테이블 락 8모드, 행 락 4모드, 그리고 행 락이 어디에 저장되는가", 15, P["muted"])
    d.save()


def table_modes():
    d = Diagram("blog01-table-modes", 1420, 700, "테이블 수준 락 8모드 — 약한 것에서 강한 것으로",
                "이름에 ROW 가 있어도 모두 테이블 수준 락이다. 의미는 이름이 아니라 \"어떤 모드와 충돌하나\" 에 있다", out=OUT)
    d.pill("h0", 40, 96, 250, 40, "모드", P["note_bg"], P["line"], size=14)
    d.pill("h1", 300, 96, 480, 40, "흔히 잡는 명령 (문서 13.3.1)", P["note_bg"], P["line"], size=14)
    d.pill("h2", 790, 96, 590, 40, "충돌하는 모드", P["note_bg"], P["line"], size=14)
    rows = [("ACCESS SHARE", "SELECT (읽기만 하는 쿼리)", "ACCESS EXCLUSIVE 뿐", "g"),
            ("ROW SHARE", "SELECT … FOR UPDATE / NO KEY UPDATE / SHARE / KEY SHARE", "EXCLUSIVE · ACCESS EXCLUSIVE", "g"),
            ("ROW EXCLUSIVE", "UPDATE · DELETE · INSERT · MERGE", "SHARE · SHARE ROW EXCLUSIVE · EXCLUSIVE · ACCESS EXCLUSIVE", "g"),
            ("SHARE UPDATE EXCLUSIVE", "VACUUM(FULL 아님) · ANALYZE · CREATE INDEX CONCURRENTLY", "자기 자신 · SHARE 이상", "n"),
            ("SHARE", "CREATE INDEX (CONCURRENTLY 아님)", "ROW EXCLUSIVE · SHARE UPDATE EXCLUSIVE · SHARE ROW EXCLUSIVE ·\nEXCLUSIVE · ACCESS EXCLUSIVE", "n"),
            ("SHARE ROW EXCLUSIVE", "CREATE TRIGGER · 일부 ALTER TABLE", "ROW EXCLUSIVE 이상 (자기 자신 포함)", "n"),
            ("EXCLUSIVE", "REFRESH MATERIALIZED VIEW CONCURRENTLY", "ROW SHARE 이상", "n"),
            ("ACCESS EXCLUSIVE", "DROP TABLE · TRUNCATE · VACUUM FULL ·\n대부분의 ALTER TABLE · LOCK TABLE 기본", "전부", "r")]
    for i, (m, c, x, k) in enumerate(rows):
        y = 148 + i * 66
        bg, st = {"g": (P["ok_bg"], P["green"]), "n": (P["white"], P["line"]), "r": (P["bad_bg"], P["red"])}[k]
        d.pill(f"m{i}", 40, y, 250, 58, m, bg, st, size=14)
        d.pill(f"c{i}", 300, y, 480, 58, c, P["white"], P["line"], size=12)
        d.pill(f"x{i}", 790, y, 590, 58, x, P["white"], P["line"], size=12)
    d.rect(None, 30, 142, 1360, 204, "none", P["green"], dashed=True)
    d.text(1380, 684, "초록 점선 안 세 줄 = 평범한 DML 이 잡는 모드. 서로 충돌하지 않는다", 14, P["green"], align="right")
    d.text(40, 684, "ACCESS EXCLUSIVE 만이 평범한 SELECT 를 막는다 (문서 13.3.1 Tip)", 14, P["red"])
    d.save()


def row_modes():
    d = Diagram("blog01-row-modes", 1420, 470, "행 수준 락 4모드 — 강해질수록 막는 범위가 넓다",
                "락 모드의 의미는 충돌표에 있다. 같은 행에 충돌하는 락을 두 트랜잭션이 가질 수 없다 (문서 13.3.2)", out=OUT)
    cols = [("FOR KEY SHARE", "SELECT … FOR KEY SHARE\n(외래키 검사가 쓴다 — 04 글)", "가장 약하다\nFOR UPDATE 만 막는다", P["ok_bg"], P["green"]),
            ("FOR SHARE", "SELECT … FOR SHARE", "UPDATE · DELETE · FOR UPDATE ·\nFOR NO KEY UPDATE 를 막는다\nFOR SHARE · FOR KEY SHARE 는\n안 막는다", P["as_bg"], P["front"]),
            ("FOR NO KEY UPDATE", "키 열을 안 바꾸는 UPDATE\nSELECT … FOR NO KEY UPDATE", "FOR UPDATE 보다 약하다\nFOR KEY SHARE 와는 충돌하지 않는다", P["todo_bg"], P["orange"]),
            ("FOR UPDATE", "DELETE · 키 열을 바꾸는 UPDATE\nSELECT … FOR UPDATE", "가장 강하다\n다른 모든 행 락과 충돌한다", P["bad_bg"], P["red"])]
    for i, (t, who, blk, bg, st) in enumerate(cols):
        x = 40 + i * 345
        d.card(f"c{i}", x, 110, 325, 250, t, None, bg=bg, stroke=st, title_size=17)
        d.text(x + 16, 160, "누가 잡나", 13, P["muted"])
        d.text(x + 16, 180, who, 14, P["ink"])
        d.text(x + 16, 245, "무엇을 막나", 13, P["muted"])
        d.text(x + 16, 265, blk, 14, P["ink"])
    d.arrow([(60, 395), (1360, 395)], P["muted"], "강해질수록 막는 범위가 넓다", label_at=(710, 395))
    d.text(40, 425, "\"키 열\" = 외래키에 쓸 수 있는 유니크 인덱스가 걸린 열 (부분 · 표현식 인덱스는 제외, 문서는 앞으로 바뀔 수 있다고 적는다)", 13, P["muted"])
    d.save()


def conflict_matrix():
    d = Diagram("blog01-conflict-matrix", 1100, 520, "행 락 충돌표 (문서 표 13.3)",
                "읽는 법은 하나 — 강한 쪽일수록 막는 범위가 넓다. 표는 대칭이다", out=OUT)
    mods = ["FOR KEY SHARE", "FOR SHARE", "FOR NO KEY UPDATE", "FOR UPDATE"]
    d.text(330, 100, "잡혀 있는 락 →", 14, P["muted"])
    d.text(40, 122, "내가 요청하는 락 ↓", 14, P["muted"])
    for c, m in enumerate(mods):
        d.pill(f"h{c}", 330 + c * 180, 150, 170, 50, m, P["note_bg"], P["line"], size=13)
    X = {(0, 3), (1, 2), (1, 3), (2, 1), (2, 2), (2, 3), (3, 0), (3, 1), (3, 2), (3, 3)}
    for r, m in enumerate(mods):
        y = 212 + r * 74
        d.pill(f"l{r}", 40, y, 280, 64, m, P["note_bg"], P["ink"], size=14)
        for c in range(4):
            if (r, c) in X:
                d.pill(f"c{r}{c}", 330 + c * 180, y, 170, 64, "기다림", P["bad_bg"], P["red"], size=15)
            else:
                d.pill(f"c{r}{c}", 330 + c * 180, y, 170, 64, "함께", P["ok_bg"], P["green"], size=15)
    d.save()


def where_stored():
    d = Diagram("blog01-where-stored", 1400, 460, "두 층의 락은 저장되는 곳이 다르다",
                "테이블 락은 공유 메모리, 행 락은 디스크의 튜플", out=OUT)
    d.card("t", 40, 110, 640, 250, "테이블 락 — 공유 메모리의 락 테이블",
           "pg_locks 에 relation 락으로 보인다\n일반(heavyweight) 락 — 완전한 데드락 감지와\n트랜잭션 끝의 자동 해제를 가진다 (lmgr README)\n\n충돌표는 8모드, 평범한 DML 끼리는 충돌하지 않는다",
           bg=P["note_bg"], stroke=P["line"], title_size=17, body_size=15)
    d.card("r", 720, 110, 640, 250, "행 락 — 디스크의 튜플 헤더",
           "한 트랜잭션이 잡으면 xmax 에 그 트랜잭션 ID\n+ \"삭제자가 아니라 잠금자\" 표시 (HEAP_XMAX_LOCK_ONLY)\n둘 이상이 잡으면 xmax 에 MultiXact ID,\n멤버는 pg_multixact 에 따로 저장\n\n메모리에 기억하지 않는다 → 잠글 수 있는 행 수에 제한이 없다\n대신 잠그면 디스크 쓰기가 생길 수 있다 (문서 13.3.2)\npg_locks 에는 보통 안 나온다",
           bg=P["todo_bg"], stroke=P["orange"], title_size=17, body_size=15)
    d.card("n", 40, 385, 1320, 56, "그래서 100만 행에 FOR UPDATE 를 걸어도 락 테이블이 터지지 않는다 — 공짜는 아니다, 튜플을 고쳐 표시하므로",
           None, bg=P["as_bg"], stroke=P["front"], title_size=15)
    d.save()


def savepoint():
    timeline("blog01-lock-lifetime", "락은 문장이 아니라 트랜잭션이 끝날 때 풀린다",
             "예외: 세이브포인트 뒤에 얻은 락은 그 세이브포인트로 ROLLBACK 하면 즉시 풀린다 (문서 13.3.1)",
             [("A", "1  BEGIN; SAVEPOINT s;", "트랜잭션 시작 — 세이브포인트 표시", None),
              ("A", "2  UPDATE coupons SET used = true WHERE id = 5", "문장은 끝났지만 행 락은 그대로 쥐고 있다", None),
              ("B", "3  UPDATE coupons SET used = true WHERE id = 5", "같은 행 — 기다린다", "bad"),
              ("A", "4  ROLLBACK TO s", "세이브포인트 뒤에 얻은 락이 즉시 풀린다", "ok"),
              ("B", "5  (대기가 풀린다)", "행 락이 풀렸으니 이어서 진행", "ok")],
             [(1, 2, "A 의 행 락이\nB 를 세운다", 0.5), (3, 4, "락이 풀려\nB 가 깬다", 0.5)],
             "문장이 끝나도 락은 풀리지 않는다. 락은 트랜잭션이 끝나거나(커밋 · 롤백) 세이브포인트로 ROLLBACK 할 때 풀린다.\n"
             "그래서 오래 열려 있는 트랜잭션이 위험하다. 락을 기다리는 쪽은 데드락이 아닌 한 무한정 기다린다 (문서 13.3.4).",
             "락의 수명 = 트랜잭션의 수명", vcolor="note")


if __name__ == "__main__":
    for f in (intro, table_modes, row_modes, conflict_matrix, where_stored, savepoint):
        f()
    finish()
