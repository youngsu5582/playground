#!/usr/bin/env python3
"""01.04 블로그판 03 그림. 실행: python3 -I docs/diagrams/draw_blog03.py (레슨 폴더에서)"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[4] / "tools"))
from diagram import Diagram, P, finish, timeline as _timeline  # noqa: E402

OUT = pathlib.Path(__file__).parent


def timeline(*a, **k):
    return _timeline(*a, out=OUT, **k)


def intro():
    timeline("blog03-intro", "도입: 읽는 순간 잠그면 B 는 줄을 선다",
             "재고 5, A 는 2 개를 산다. B 도 같은 행을 FOR UPDATE 로 읽으려 한다",
             [("A", "1  BEGIN; SELECT qty ... FOR UPDATE", "본 값: 5  · 행 락을 잡는다", None),
              ("B", "2  BEGIN; SELECT qty ... FOR UPDATE", "같은 행이라 A 가 끝나기를 기다린다", None),
              ("A", "3  UPDATE qty = 3  → COMMIT", "앱이 계산한 새 값 · 커밋에서 락이 풀린다", None),
              ("B", "4  (락을 얻고 갱신된 행을 읽는다)", "본 값: 3  (A 가 커밋한 최신 값)", "ok")],
             [(0, 1, "A 의 행 락이\nB 를 세운다", 0.3), (2, 3, "풀린 뒤 B 는\n최신 값을 읽는다", 0.7)],
             "틈(읽기와 쓰기 사이)은 그대로 있다. 다만 읽는 순간 행을 잠갔기 때문에 그 틈에 남이 끼어들 수 없다.\n"
             "B 는 A 가 커밋한 값 3 을 읽고 나서 자기 계산을 한다.",
             "틈은 두고, 끼어들지 못하게 잠근다", vcolor="ok")


def lock_span():
    d = Diagram("blog03-lock-span", 1460, 470, "락을 쥐는 구간 = 읽기부터 COMMIT 까지",
                "같은 재고 차감을 두 가지로 쓰면 행 락이 유지되는 시간이 달라진다", out=OUT)
    d.text(40, 110, "비관 락", 17, P["ink"], weight=700)
    xs = [(140, 220, "BEGIN"), (360, 300, "SELECT ... FOR UPDATE"), (660, 340, "앱 계산 · 판단"), (1000, 200, "UPDATE"), (1200, 200, "COMMIT")]
    for i, (x, w, t) in enumerate(xs):
        d.pill(f"p{i}", x, 140, w - 10, 56, t, P["rs_bg"] if i not in (2,) else P["bad_bg"], P["orange"] if i != 2 else P["red"], size=14)
    d.arrow([(360, 225), (1390, 225)], P["red"], "행 락 보유", both=True, label_size=14, sw=3)
    d.text(40, 270, "원자 UPDATE", 17, P["ink"], weight=700)
    d.pill("a", 1000, 300, 390, 56, "UPDATE ... qty - n ... qty >= n  → COMMIT", P["ok_bg"], P["green"], size=14)
    d.arrow([(1000, 385), (1390, 385)], P["green"], "행 락 보유", both=True, label_size=14, sw=3)
    d.card("n", 40, 410, 1380, 40, "앱 로직 · 외부 호출이 구간에 끼면 그만큼 뒤의 줄이 길어진다 (이 구간에는 외부 API 를 넣지 않는다)", None,
           bg=P["note_bg"], stroke=P["line"], title_size=14)
    d.save()


def pool():
    d = Diagram("blog03-pool", 1460, 500, "줄 선 사람마다 커넥션을 하나씩 쥔다 (해석)",
                "트랜잭션이 열려 있는 한 커넥션이 반납되지 않는다는 일반 사실에서 이은 그림이다", out=OUT)
    d.card("r", 40, 110, 1380, 80, "같은 행 (재고 SKU 1)",
           "A 가 FOR UPDATE 로 잠근 채 외부 호출 중이고, B · C · D 는 같은 행의 락을 기다린다",
           bg=P["bad_bg"], stroke=P["red"], title_size=17, body_size=15)
    ws = [("A", "락 보유 · 커넥션 1"), ("B", "대기 · 커넥션 2"), ("C", "대기 · 커넥션 3"), ("D", "대기 · 커넥션 4")]
    for i, (n, t) in enumerate(ws):
        d.pill(f"c{i}", 40 + i * 350, 230, 330, 70, f"{n}\n{t}", P["bad_bg"] if i else P["todo_bg"], P["red"] if i else P["orange"], size=15)
    d.card("pool", 40, 340, 1380, 50, "커넥션 풀 (크기 4) — 전부 사용 중", None, bg=P["note_bg"], stroke=P["muted"], title_size=16)
    d.pill("e", 40, 420, 640, 56, "E: 다른 SKU 를 사려는 요청 — 커넥션을 못 얻어 기다린다", P["bad_bg"], P["red"], size=15)
    d.text(720, 432, "풀 크기가 줄 서는 사람 수보다 작으면\n같은 행과 상관없는 요청도 커넥션을 못 얻는다", 15, P["ink"])
    d.save()


def cut_wait():
    d = Diagram("blog03-cut-wait", 1460, 440, "대기를 끊는 세 가지 방법",
                "락을 기다리는 B 가 무한정 서 있지 않게 한다", out=OUT)
    cs = [("FOR UPDATE NOWAIT", "잠긴 행이면 기다리지 않고 에러\nERROR: could not obtain lock\non row in relation \"stock\"", P["bad_bg"], P["red"]),
          ("FOR UPDATE SKIP LOCKED", "잠긴 행은 건너뛴다\n다른 행을 집는다\n(큐 소비자에 쓰는 도구)", P["todo_bg"], P["orange"]),
          ("SET lock_timeout = '500ms'", "그만큼 기다려도 못 얻으면\nERROR: canceling statement\ndue to lock timeout", P["as_bg"], P["front"])]
    for i, (t, b, bg, st) in enumerate(cs):
        d.card(f"c{i}", 40 + i * 470, 110, 440, 180, t, b, bg=bg, stroke=st, title_size=17, body_size=15)
    d.card("n", 40, 330, 1380, 70, "SKIP LOCKED 는 재고 한 행의 정합성에는 쓰지 않는다 — 건너뛰면 재고를 놓친다", None, bg=P["note_bg"], stroke=P["line"], title_size=15)
    d.save()


def what_blocks():
    d = Diagram("blog03-what-blocks", 1460, 440, "A 가 FOR UPDATE 로 행을 잠갔을 때, B 의 문장은",
                "행 락은 같은 행의 쓰는 쪽과 잠그는 쪽만 막는다", out=OUT)
    rows = [("B: SELECT ... FOR UPDATE", "기다린다", True), ("B: UPDATE · DELETE", "기다린다", True),
            ("B: 평범한 SELECT", "기다리지 않는다 (락 없이 스냅샷을 읽는다)", False), ("B: 다른 행에 FOR UPDATE", "기다리지 않는다 (행 단위 락)", False)]
    for i, (a, b, w) in enumerate(rows):
        y = 110 + i * 78
        d.pill(f"a{i}", 40, y, 520, 62, a, P["note_bg"], P["line"], size=16)
        d.pill(f"b{i}", 600, y, 820, 62, b, P["bad_bg"] if w else P["ok_bg"], P["red"] if w else P["green"], size=16)
    d.save()


def rr_paths():
    d = Diagram("blog03-rr-paths", 1460, 470, "REPEATABLE READ 에서 FOR UPDATE — 두 경로",
                "잠그려는 행이 트랜잭션 시작 이후 바뀌었으면 에러다 (문서 13.3.2)", out=OUT)
    d.card("p1", 40, 110, 680, 220, "(가) 이미 바뀐 행",
           "1. B 가 REPEATABLE READ 로 스냅샷을 잡는다\n2. A 가 같은 행을 UPDATE 하고 커밋한다\n3. B 가 FOR UPDATE\n   → 바로 could not serialize access\n      due to concurrent update",
           bg=P["bad_bg"], stroke=P["red"], title_size=17, body_size=15)
    d.card("p2", 760, 110, 660, 220, "(나) 기다리다 바뀐 행",
           "1. A 가 FOR UPDATE 로 잠근 채 있다\n2. B 가 REPEATABLE READ 의 첫 문장으로 FOR UPDATE → 기다린다\n3. A 가 UPDATE 후 커밋\n   → 같은 에러 (스냅샷은 B 의 첫 문장 때 잡히므로\n      기다린 사이의 변경이 이미 시작 이후다)",
           bg=P["bad_bg"], stroke=P["red"], title_size=17, body_size=15)
    d.card("n", 40, 360, 1380, 80, "이 에러는 앱이 트랜잭션 전체를 재시도하라는 신호다 (문서 13.2.2)", None, bg=P["note_bg"], stroke=P["line"], title_size=15)
    d.save()


def deadlock():
    timeline("blog03-deadlock", "여러 상품을 잠글 때의 데드락",
             "주문 하나가 상품 1, 2 를 모두 잠그는데, 다른 주문이 반대 순서로 잠근다 (A = T1, B = T2)",
             [("A", "1  UPDATE 상품 1", "상품 1 의 행 락을 잡는다", None),
              ("B", "2  UPDATE 상품 2", "상품 2 의 행 락을 잡는다", None),
              ("A", "3  UPDATE 상품 2", "B 가 쥔 락 때문에 기다린다", None),
              ("B", "4  UPDATE 상품 1", "A 가 쥔 락 때문에 기다린다", "bad")],
             [(1, 2, "A 가 B 의\n락을 기다린다", 0.45), (0, 3, "B 가 A 의\n락을 기다린다", 0.85)],
             "서로를 기다리는 순환이다. 한쪽이 ERROR: deadlock detected 로 취소되고 다른 쪽은 커밋된다.\n"
             "둘 다 같은 순서(상품 1 → 2)로 잠그면 에러 없이 둘 다 커밋된다. 처방은 잠글 상품 ID 를 정렬하는 것이다.",
             "A 와 B 가 서로의 락을 기다린다")


def hibernate():
    d = Diagram("blog03-hibernate", 1460, 560, "JPA 의 PESSIMISTIC_WRITE 가 PostgreSQL 에서 나가는 SQL",
                "실측: Hibernate 6.4.10 · 6.6.58 · PostgreSQL 방언 (2026-10-13). 호출 방식에 따라 갈린다", out=OUT)
    rows = [("em.find(..., PESSIMISTIC_WRITE)\nJPQL setLockMode", "select ... where s1_0.id=? for no key update", P["as_bg"], P["front"]),
            ("타임아웃 힌트 0", "for no key update nowait", P["rs_bg"], P["orange"]),
            ("타임아웃 힌트 -2", "for no key update ... skip locked", P["rs_bg"], P["orange"]),
            ("타임아웃 힌트 양수 (3000)", "SQL 에 반영되지 않는다", P["note_bg"], P["line"]),
            ("em.lock(entity, PESSIMISTIC_WRITE)\n(이미 읽은 엔티티)", "select id from Stock where id=? and version=? for update", P["bad_bg"], P["red"])]
    for i, (a, b, bg, st) in enumerate(rows):
        y = 110 + i * 84
        d.pill(f"a{i}", 40, y, 520, 68, a, P["white"], P["line"], size=15)
        d.pill(f"b{i}", 620, y, 800, 68, b, bg, st, size=15, mono=True)
        d.arrow([(560, y + 34), (620, y + 34)], P["muted"])
    d.text(40, 540, "FOR UPDATE 가 아니라 FOR NO KEY UPDATE — em.lock 만 for update", 15, P["muted"])
    d.save()


if __name__ == "__main__":
    for f in (intro, lock_span, pool, cut_wait, what_blocks, rr_paths, deadlock, hibernate):
        f()
    finish()
