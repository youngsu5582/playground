#!/usr/bin/env python3
"""01.01 블로그판 01 그림. 실행: python3 -I docs/diagrams/draw_blog01.py (레슨 폴더에서)"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[4] / "tools"))
from diagram import Diagram, P, finish, timeline as _timeline  # noqa: E402

OUT = pathlib.Path(__file__).parent


def timeline(*a, **k):
    return _timeline(*a, out=OUT, **k)



def intro():
    timeline("blog01-intro", "도입: 잔고 100 계좌에 두 트랜잭션이 동시에",
             "A 는 20 을 출금하고, B 는 10 을 입금한다. 한 번에 하나씩 돌리면 어느 순서든 결과는 90 이다",
             [("A", "1  SELECT balance", "본 값: 100", None),
              ("B", "2  SELECT balance", "본 값: 100", None),
              ("A", "3  UPDATE balance = 80  → COMMIT", "100 - 20 = 80", None),
              ("B", "4  UPDATE balance = 110  → COMMIT", "100 + 10 = 110  (A 의 결과를 덮어쓴다)", "bad")],
             [(2, 3, "A 가 쓴 80 을\nB 가 덮어쓴다")],
             "직렬로 돌렸다면 90. 지금은 110 이다 — A 의 출금 20 이 흔적 없이 사라졌다.\n"
             "두 트랜잭션은 각자 규칙대로 읽고 계산하고 썼을 뿐인데, 겹쳐 돌았다는 이유만으로 결과가 틀어졌다.\n"
             "이런 어긋남이 어떤 모양으로 생기는지, 이 글은 그 모양들에 이름을 붙이는 일이다.",
             "동시에 돌면 이런 일이 생긴다")


def dirty_read():
    timeline("blog01-dirty-read", "더티 리드 (dirty read)",
             "남이 쓰고 아직 커밋하지 않은 값을 읽는다 — 재고 20 (표준의 READ UNCOMMITTED 에서 허용되는 모양)",
             [("B", "1  UPDATE stock = 5", "아직 COMMIT 하지 않았다 (원래 20)", None),
              ("A", "2  SELECT stock", "본 값: 5  (커밋 안 된 값)", "bad"),
              ("B", "3  ROLLBACK", "5 는 없던 일이 된다 — 재고는 여전히 20", None)],
             [(0, 1, "커밋 전 값을\nA 가 읽는다")],
             "A 는 세상에 한 번도 존재한 적 없는 값 5 를 보고 판단했다.\n"
             "B 가 롤백하는 순간 A 가 근거로 삼은 값이 통째로 사라진다.",
             "A 가 본 5 는 취소될 값이다", level="READ UNCOMMITTED, 표준")


def nonrepeatable():
    timeline("blog01-nonrepeatable", "반복 불가 읽기 (non-repeatable read)",
             "같은 행을 두 번 읽었는데 값이 다르다 — 재고 10",
             [("A", "1  SELECT stock WHERE id = 1", "본 값: 10", None),
              ("B", "2  UPDATE stock = 7  → COMMIT", "A 가 읽고 난 뒤에 커밋", None),
              ("A", "3  SELECT stock WHERE id = 1", "본 값: 7  (같은 트랜잭션 · 같은 쿼리)", "bad")],
             [(1, 2, "B 의 커밋이\n다시 읽기에 보인다")],
             "더티 리드와 달리 B 는 커밋을 끝냈다 — 읽은 값이 \"취소될 값\" 은 아니다.\n"
             "문제는 A 의 트랜잭션 안에서 같은 질문의 답이 바뀐다는 점이다.",
             "한 트랜잭션 안에서 답이 바뀐다")


def phantom():
    timeline("blog01-phantom", "팬텀 읽기 (phantom read)",
             "같은 조건으로 다시 조회했더니 행의 집합이 달라졌다 — 대기 중인 주문 수",
             [("A", "1  SELECT count(*) WHERE status = '대기'", "본 값: 3", None),
              ("B", "2  INSERT 대기 주문 1건  → COMMIT", "A 가 읽고 난 뒤에 커밋", None),
              ("A", "3  SELECT count(*) WHERE status = '대기'", "본 값: 4  (없던 행이 나타났다)", "bad")],
             [(1, 2, "새 행이\n조건에 끼어든다")],
             "반복 불가 읽기는 \"이미 읽은 행의 값\" 이 바뀐 것이고, 팬텀은 \"조건에 맞는 행의 범위\" 가 바뀐 것이다.\n"
             "읽은 행 하나하나에 보호막을 쳐도, 아직 존재하지 않던 행이 새로 끼어드는 것은 막지 못한다.",
             "행이 아니라 범위가 바뀐다")


def lost_update():
    timeline("blog01-lost-update", "갱신 손실 (lost update)",
             "둘이 같은 값을 읽고 각자 계산해 같은 행에 덮어쓴다 — 재고 200, A 가 40 개 · B 가 70 개 판매",
             [("A", "1  SELECT stock", "본 값: 200", None),
              ("B", "2  SELECT stock", "본 값: 200", None),
              ("A", "3  UPDATE stock = 160  → COMMIT", "200 - 40", None),
              ("B", "4  UPDATE stock = 130  → COMMIT", "200 - 70  (A 의 40 이 사라진다)", "bad")],
             [(2, 3, "A 의 쓰기를\nB 가 덮어쓴다")],
             "직렬로 돌렸다면 200 - 40 - 70 = 90. 결과는 130 이다.\n"
             "읽기는 문제가 없었고, 문제는 \"읽은 값을 근거로 계산한 결과로 같은 행을 덮어썼다\" 는 데 있다.\n"
             "도입의 장면이 바로 이 모양이다.",
             "A 의 쓰기가 B 의 덮어쓰기에 지워진다")


def read_skew():
    timeline("blog01-read-skew", "읽기 왜곡 (read skew)",
             "읽는 도중에 남이 커밋해서, 서로 다른 시점의 행을 섞어 본다 — 계좌 X · Y 가 각각 100 (합 200), X 에서 Y 로 40 이체",
             [("A", "1  SELECT balance WHERE id = X", "본 값: 100  (이체 전)", None),
              ("B", "2  이체: X = 60, Y = 140  → COMMIT", "합은 여전히 200", None),
              ("A", "3  SELECT balance WHERE id = Y", "본 값: 140  (이체 후)", "bad")],
             [(1, 2, "이체 후 값을\n섞어 읽는다")],
             "A 가 본 두 값의 합은 100 + 140 = 240. 세상에 합이 240 이었던 순간은 없다.\n"
             "행 하나만 보면 반복 불가 읽기가 아니다 — 서로 다른 두 행을 한 번씩 읽었는데, 두 행이 서로 다른 시점의 것이다.",
             "A 는 존재한 적 없는 상태를 봤다")


def write_skew():
    timeline("blog01-write-skew", "쓰기 왜곡 (write skew)",
             "둘이 같은 근거를 읽고 서로 다른 행을 고친다 — 두 계좌 X · Y 가 각각 50, 규칙은 \"합은 0 이상\"",
             [("A", "1  SELECT sum(balance)", "본 값: 100  → 80 을 빼도 괜찮다", None),
              ("B", "2  SELECT sum(balance)", "본 값: 100  → 80 을 빼도 괜찮다", None),
              ("A", "3  UPDATE X = X - 80  → COMMIT", "X = -30  (합 20)", None),
              ("B", "4  UPDATE Y = Y - 80  → COMMIT", "Y = -30  (합 -60)", "bad")],
             [(0, 3, "A 가 읽은 근거를\nB 가 바꾼다", 0.83), (1, 2, "B 가 읽은 근거를\nA 가 바꾼다", 0.5)],
             "A 와 B 는 서로 다른 행을 고쳤으니 같은 행을 두고 기다릴 일이 없다. 각자 읽은 근거(합 100)는 상대의 쓰기로 깨졌다.\n"
             "어느 쪽을 먼저 돌려도 두 번째는 거절됐어야 한다 — 직렬 순서가 없는 결과다.",
             "각자는 옳은데 합치면 규칙이 깨진다", level="REPEATABLE READ")


def ladder_standard():
    d = Diagram("blog01-ladder-standard", 1360, 560, "격리수준 = 무엇을 허용하나의 사다리 (SQL 표준)",
                "위에서 아래로 내려갈수록 허용하는 이상 현상이 줄어든다. 아래 한 칸이 위 한 칸의 약속을 모두 포함한다", out=OUT)
    heads = ["더티 리드", "반복 불가\n읽기", "팬텀", "직렬화 이상"]
    for c, t in enumerate(heads):
        d.pill(f"h{c}", 630 + c * 170, 100, 160, 52, t, P["note_bg"], P["line"], size=14)
    d.pill("hl", 40, 100, 230, 52, "격리수준", P["note_bg"], P["line"], size=14)
    d.pill("hp", 280, 100, 340, 52, "이 수준이 하는 약속", P["note_bg"], P["line"], size=14)
    rows = [("READ UNCOMMITTED", "약속 없음 — 커밋 안 된 것도 본다", "AAAA"),
            ("READ COMMITTED", "커밋된 것만 본다", "BAAA"),
            ("REPEATABLE READ", "읽은 행은 다시 읽어도 같다", "BBAA"),
            ("SERIALIZABLE", "한 번에 하나씩 돌린 것과 같다", "BBBB")]
    for r, (lv, promise, cells) in enumerate(rows):
        y = 176 + r * 86
        d.pill(f"l{r}", 40, y, 230, 70, lv, P["as_bg"], P["front"], size=16)
        d.pill(f"p{r}", 280, y, 340, 70, promise, P["white"], P["line"], size=14)
        for c, ch in enumerate(cells):
            if ch == "A":
                d.pill(f"c{r}{c}", 630 + c * 170, y, 160, 70, "허용", P["bad_bg"], P["red"], size=16)
            else:
                d.pill(f"c{r}{c}", 630 + c * 170, y, 160, 70, "막는다", P["ok_bg"], P["green"], size=16)
    d.arrow([(1330, 180), (1330, 500)], P["green"])
    d.text(40, 524, "표 13.1 (PostgreSQL 16 문서 13.2) 의 표준 쪽 읽기. 이 표는 표준이 \"허용해도 된다\" 고 한 범위이고, 엔진이 더 막는 것은 괜찮다",
           14, P["muted"])
    d.save()


def standard_vs_pg():
    d = Diagram("blog01-standard-vs-pg", 1420, 640, "표준과 PostgreSQL 의 차이 — 세 군데",
                "표준은 \"이만큼은 허용해도 된다\" 는 상한이고, PostgreSQL 은 MVCC 구조에 맞춰 그보다 더 막는다", out=OUT)
    panels = [
        ("READ UNCOMMITTED", "표준: 더티 리드를 허용해도 된다",
         "READ COMMITTED 와 똑같이 동작한다\n더티 리드는 생기지 않는다\n(문서: 표준 수준을 MVCC 구조에 대응시키는\n유일하게 합리적인 방법)", "ok"),
        ("REPEATABLE READ", "표준: 팬텀을 허용해도 된다",
         "스냅샷 격리로 구현 — 팬텀까지 막는다\n그러나 직렬화 이상은 남는다\n= write skew 는 여전히 생긴다", "mix"),
        ("SERIALIZABLE", "표준: 직렬 실행과 같은 결과",
         "REPEATABLE READ 에 감시 장치를 얹은 SSI\n위험한 구조를 찾으면 한쪽을 40001 로 실패시킨다\n읽기를 새로 막지는 않는다 (오버헤드는 있다)", "ok")]
    for i, (lv, std, pg, kind) in enumerate(panels):
        x = 40 + i * 460
        d.card(f"s{i}", x, 110, 420, 120, lv, std, bg=P["note_bg"], stroke=P["muted"], title_size=17, body_size=15)
        d.arrow([(x + 210, 230), (x + 210, 290)], P["muted"], "PostgreSQL 에서는")
        stroke = P["orange"] if kind == "mix" else P["green"]
        bg = P["todo_bg"] if kind == "mix" else P["ok_bg"]
        d.card(f"p{i}", x, 290, 420, 190, "PostgreSQL 16", pg, bg=bg, stroke=stroke, title_size=17, body_size=14)
    d.card("sum", 40, 520, 1340, 90, "그래서 실제로는 세 단계다 — READ COMMITTED · REPEATABLE READ · SERIALIZABLE",
           "기본값은 READ COMMITTED. 수준은 트랜잭션의 첫 쿼리 · 데이터 변경 문장 앞에서 BEGIN ISOLATION LEVEL ... 로 지정한다",
           bg=P["as_bg"], stroke=P["front"], title_size=16, body_size=14)
    d.save()


def pg_matrix():
    d = Diagram("blog01-pg-matrix", 1450, 520, "PostgreSQL 16 에서 이상 현상은 어디서 막히나",
                "여섯 가지를 세 수준에 놓았다. 초록 = 막힘, 빨강 = 생김, 노랑 = 40001 로 실패시킨다", out=OUT)
    cols = ["더티 리드", "반복 불가 읽기\n· 읽기 왜곡", "팬텀", "갱신 손실\n(앱에서 계산)", "쓰기 왜곡"]
    d.pill("h", 40, 100, 220, 56, "수준", P["note_bg"], P["line"], size=14)
    for c, t in enumerate(cols):
        d.pill(f"h{c}", 270 + c * 230, 100, 220, 56, t, P["note_bg"], P["line"], size=14)
    rows = [("READ COMMITTED\n(READ UNCOMMITTED 도 같다)", ["막힘", "생김", "생김", "생김", "생김"]),
            ("REPEATABLE READ", ["막힘", "막힘", "막힘", "같은 행이면\n40001", "생김"]),
            ("SERIALIZABLE", ["막힘", "막힘", "막힘", "같은 행이면\n40001", "40001\n(오탐 가능)"])]
    for r, (lv, cells) in enumerate(rows):
        y = 172 + r * 92
        d.pill(f"l{r}", 40, y, 220, 76, lv, P["as_bg"], P["front"], size=14)
        for c, t in enumerate(cells):
            if t == "막힘":
                bg, st = P["ok_bg"], P["green"]
            elif t == "생김":
                bg, st = P["bad_bg"], P["red"]
            else:
                bg, st = P["todo_bg"], P["orange"]
            d.pill(f"c{r}{c}", 270 + c * 230, y, 220, 76, t, bg, st, size=15)
    d.card("note", 40, 460, 1370, 50, "갱신 손실은 앱이 읽고 계산해 쓸 때에 한한 말 — SET balance = balance - x 처럼 DB 안에서 계산하면 다르다 (문서 04)",
           None, bg=P["note_bg"], stroke=P["line"], title_size=14)
    d.save()


if __name__ == "__main__":
    for f in (intro, dirty_read, nonrepeatable, phantom, lost_update, read_skew, write_skew,
              ladder_standard, standard_vs_pg, pg_matrix):
        f()
    finish()
