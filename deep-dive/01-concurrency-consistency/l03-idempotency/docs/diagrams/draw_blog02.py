#!/usr/bin/env python3
"""01.03 블로그판 02 그림. 실행: python3 -I docs/diagrams/draw_blog02.py (레슨 폴더에서)"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[4] / "tools"))
from diagram import Diagram, P, finish, timeline as _timeline  # noqa: E402

OUT = pathlib.Path(__file__).parent


def timeline(*a, **k):
    return _timeline(*a, out=OUT, **k)


def race():
    timeline("blog02-race", "확인하고 넣기(check-then-act)의 틈",
             "같은 키로 거의 동시에 온 두 요청 — 먼저 있나 SELECT 로 확인하고, 없으면 INSERT 한다",
             [("A", "1  SELECT … WHERE key = 'ord-7'", "본 값: 0행 — 없네, 내가 넣자", None),
              ("B", "2  SELECT … WHERE key = 'ord-7'", "본 값: 0행 — 없네, 내가 넣자", None),
              ("A", "3  INSERT key = 'ord-7'", "A 는 \"없다\" 를 근거로 넣는다", None),
              ("B", "4  INSERT key = 'ord-7'", "B 도 \"없다\" 를 근거로 넣는다", "bad")],
             [(2, 3, "A 의 INSERT 를 모른 채\nB 가 넣는다")],
             "확인(SELECT)과 쓰기(INSERT) 사이에 틈이 있다. 두 요청 모두 틈 이전의 \"없다\" 를 근거로 움직였다.\n"
             "트래픽이 낮을 때는 영원히 안 터지고, 재시도가 몰리는 순간에만 터진다.",
             "둘 다 \"없다\" 를 보고 넣는다")


def why_blind():
    d = Diagram("blog02-why-blind", 1360, 480, "왜 둘 다 \"없다\" 를 보나 — READ COMMITTED 의 SELECT",
                "틈에서 두 요청이 서로를 보지 못하는 이유는 두 가지다", out=OUT)
    d.card("r1", 40, 100, 620, 150, "1  커밋 안 된 남의 INSERT 는 보이지 않는다",
           "READ COMMITTED 에서 SELECT 는 커밋된 것만 본다\n(더티 리드 금지 — 01.01 문서 01)",
           bg=P["as_bg"], stroke=P["front"], title_size=16, body_size=14)
    d.card("r2", 700, 100, 620, 150, "2  읽기는 락을 잡지 않는다",
           "읽기는 쓰기를 막지 않고, 서로를 막지도 않는다\n(PostgreSQL 문서 13.1)",
           bg=P["as_bg"], stroke=P["front"], title_size=16, body_size=14)
    d.pill("res", 40, 310, 1280, 56, "그래서 둘 다 \"없다\" 를 본다 — 이름이 \"확인하고 행동하기(check-then-act)\" 경쟁이다", P["bad_bg"], P["red"], size=16)
    d.arrow([(350, 250), (350, 310)], P["muted"], "서로를 못 본다", start="r1", end="res")
    d.arrow([(1010, 250), (1010, 310)], P["muted"], "서로를 안 막는다", start="r2", end="res")
    d.card("v", 40, 390, 1280, 70, "트랜잭션으로 감싸도 READ COMMITTED · REPEATABLE READ 에서는 같다", None,
           bg=P["note_bg"], stroke=P["line"], title_size=15)
    d.save()


def rr_blind():
    timeline("blog02-rr-blind", "격리수준을 올려도 SELECT 가 INSERT 를 막아 주지는 않는다",
             "REPEATABLE READ 는 스냅샷 하나를 보여 줄 뿐이다 — 처음에 없던 것은 계속 없다고 본다",
             [("A", "1  SELECT … WHERE key = 'ord-7'", "본 값: 0행 (이 시점에 스냅샷이 정해진다)", None),
              ("B", "2  INSERT 'ord-7'  → COMMIT", "A 가 읽고 난 뒤에 커밋", None),
              ("A", "3  SELECT … WHERE key = 'ord-7'", "본 값: 0행 — 스냅샷에는 아직 없다", "bad")],
             [(1, 2, "B 의 커밋은\nA 의 스냅샷에 없다")],
             "스냅샷은 읽기를 일관되게 만들 뿐, 쓰기를 가로막는 장치가 아니다.\n"
             "그래서 이 레슨은 READ COMMITTED 로 돌리고, 중복은 격리수준이 아니라 제약으로 막는다.",
             "계속 \"없다\" 로 보인다", level="REPEATABLE READ")


def app_lock():
    d = Diagram("blog02-app-lock", 1360, 640, "앱 락은 그 JVM 안의 스레드만 조정한다",
                "같은 키 요청이 로드밸런서를 거쳐 서로 다른 서버에 닿으면, 각자 \"처음 보는 키\" 라고 판단한다", out=OUT)
    d.pill("lb", 440, 100, 480, 50, "같은 키 pay-1 의 요청 둘 (재시도)", P["note_bg"], P["line"], size=15)
    d.card("s1", 40, 220, 560, 150, "서버 1  (JVM)", "synchronized / ConcurrentHashMap 의 락\n이 JVM 안에서는 \"처음 보는 키\"", bg=P["as_bg"], stroke=P["front"], title_size=17)
    d.card("s2", 760, 220, 560, 150, "서버 2  (JVM)", "자기만의 락 · 자기만의 맵\n여기서도 \"처음 보는 키\"", bg=P["bff_bg"], stroke=P["back"], title_size=17)
    d.arrow([(560, 150), (320, 220)], P["muted"], "요청 1", start="lb", end="s1")
    d.arrow([(800, 150), (1040, 220)], P["muted"], "요청 2", start="lb", end="s2")
    d.card("db", 440, 470, 480, 110, "DB — 둘이 공유하는 곳", "JVM 락은 여기까지 닿지 않는다", bg=P["bad_bg"], stroke=P["red"], title_size=17, sw=3)
    d.arrow([(320, 370), (560, 470)], P["red"], "각자 INSERT", start="s1", end="db")
    d.arrow([(1040, 370), (800, 470)], P["red"], "각자 INSERT", start="s2", end="db")
    d.text(40, 396, "타임아웃된 연결과 새 연결은 다른 서버에 닿을 수 있다 (해석)", 13, P["muted"])
    d.save()


def methods():
    d = Diagram("blog02-methods", 1360, 540, "중복을 막는 방법별로 서버 1대 · N대에서 통하나",
                "심판이 데이터와 같은 곳에 있어야 서버가 늘어도 통한다", out=OUT)
    d.pill("h0", 40, 100, 400, 50, "방법", P["note_bg"], P["line"], size=14)
    d.pill("h1", 450, 100, 190, 50, "서버 1대", P["note_bg"], P["line"], size=14)
    d.pill("h2", 650, 100, 190, 50, "서버 N대", P["note_bg"], P["line"], size=14)
    d.pill("h3", 850, 100, 470, 50, "비고", P["note_bg"], P["line"], size=14)
    rows = [("앱 안 SELECT → INSERT", "깨짐", "깨짐", "틈이 있다"),
            ("JVM 락 · 메모리 맵", "통함", "깨짐", "이 레슨 방법 검사가 거른다"),
            ("분산 락 (Redis 등)", "통함", "통함", "락 서비스 장애 · 만료 · 락과 커밋 사이의 틈을 따로 다뤄야 한다 (해석)"),
            ("DB 유니크 제약 + 한 문장 선점", "통함", "통함", "심판이 데이터와 같은 곳에 있다 — 03 · 04")]
    for i, (m, a, b, n) in enumerate(rows):
        y = 164 + i * 84
        d.pill(f"m{i}", 40, y, 400, 72, m, P["as_bg"], P["front"], size=15)
        for j, (t, x) in enumerate(((a, 450), (b, 650))):
            ok = t == "통함"
            d.pill(f"v{i}{j}", x, y, 190, 72, t, P["ok_bg"] if ok else P["bad_bg"], P["green"] if ok else P["red"], size=16)
        d.pill(f"n{i}", 850, y, 470, 72, n, P["white"], P["line"], size=13)
    d.save()


def distributed_lock():
    d = Diagram("blog02-dist-lock", 1400, 600, "분산 락을 써도 락과 DB 사이에 틈이 남는다",
                "락에는 만료 시간이 있다 — 락을 쥔 프로세스가 멈췄다 깨어나면 (해석)", out=OUT)
    xs = [40, 400, 760, 1120]
    d.card("p1", xs[0], 110, 250, 100, "1  프로세스 P", "락을 얻는다", bg=P["as_bg"], stroke=P["front"], title_size=15)
    d.card("p2", xs[1], 110, 250, 100, "2  P 가 멈춘다", "락 만료 시간이 흐른다", bg=P["todo_bg"], stroke=P["orange"], title_size=15)
    d.card("q1", xs[2], 110, 250, 100, "3  프로세스 Q", "만료된 락을 얻고 쓴다", bg=P["bff_bg"], stroke=P["back"], title_size=15)
    d.card("p3", xs[3], 110, 250, 100, "4  P 가 깨어난다", "락이 넘어간 줄 모르고\n쓰기를 시도한다", bg=P["bad_bg"], stroke=P["red"], title_size=15, sw=3)
    for k, (a, b, lab, col) in enumerate((("p1", "p2", "시간이 흐른다", P["muted"]), ("p2", "q1", "락 만료", P["muted"]), ("q1", "p3", "그 뒤", P["red"]))):
        d.arrow([(xs[k] + 250, 160), (xs[k + 1], 160)], col, lab, label_size=11, start=a, end=b)
    d.card("db", 40, 300, 1320, 120, "락 서비스와 DB 는 서로 다른 곳이다",
           "락이 이미 다른 쪽으로 넘어갔는데도 쓰기를 시도할 수 있다 — 락 서비스와 DB 사이의 틈\n"
           "DB 의 유니크 제약을 마지막 방어선으로 남겨 두는 이유",
           bg=P["note_bg"], stroke=P["line"], title_size=17, body_size=15)
    d.card("v", 40, 450, 1320, 100, "그래서 분산 락을 써도 DB 제약은 필요하다", "심판이 하나가 아니면 틈이 생기고, 마지막에 데이터와 같은 곳의 제약이 남는다",
           bg=P["ok_bg"], stroke=P["green"], title_size=17, body_size=14, title_color=P["green"])
    d.save()


def for_update():
    d = Diagram("blog02-for-update", 1360, 560, "없는 행은 잠글 수 없다 — SELECT … FOR UPDATE 의 한계",
                "첫 요청에서는 잠글 키 행이 아직 없다. INSERT 는 인덱스에 \"내가 넣는 중\" 이라는 흔적을 남긴다", out=OUT)
    d.card("fu", 40, 110, 600, 150, "SELECT … FOR UPDATE", "키 행이 아직 없다 -> 잠글 것이 없다\n아무것도 잠그지 못한다",
           bg=P["bad_bg"], stroke=P["red"], title_size=17, body_size=15, title_color=P["red"])
    d.card("ins", 720, 110, 600, 150, "INSERT 로 선점한다", "유니크 인덱스에 \"내가 넣는 중\" 이라는 항목이 남는다\n"
           "뒤따르는 INSERT 가 그 항목에 부딪힌다 (문서 03)",
           bg=P["ok_bg"], stroke=P["green"], title_size=17, body_size=15, title_color=P["green"])
    d.arrow([(640, 185), (720, 185)], P["muted"], "대신", start="fu", end="ins")
    d.card("after", 40, 320, 1280, 100, "행이 이미 있는 뒤의 갱신에는 FOR UPDATE 가 유효하다",
           "(01.01 문서 04) — 문제는 \"잠글 행이 없는 첫 요청\" 이다", bg=P["note_bg"], stroke=P["line"], title_size=16, body_size=14)
    d.card("v", 40, 450, 1280, 90, "그래서 키 행을 INSERT 로 선점한다", "행이 아니라 인덱스 항목이 부딪히는 지점이 된다",
           bg=P["as_bg"], stroke=P["front"], title_size=16, body_size=14)
    d.save()


def unique_guard():
    d = Diagram("blog02-unique-guard", 1360, 560, "유니크 제약이 있으면 무엇이 달라지나",
                "제약은 틈 자체를 없애지 못한다 — 대신 중복 행이 만들어지는 것을 끝까지 막는다", out=OUT)
    d.card("a", 40, 110, 440, 90, "요청 A: INSERT 'ord-7'", "틈에서 시도한다", bg=P["as_bg"], stroke=P["front"], title_size=16)
    d.card("b", 40, 230, 440, 90, "요청 B: INSERT 'ord-7'", "틈에서 시도한다", bg=P["bff_bg"], stroke=P["back"], title_size=16)
    d.card("db", 600, 150, 340, 130, "DB 유니크 제약", "같은 키를 가진 행은\n하나만 통과시킨다", bg=P["ok_bg"], stroke=P["green"], title_size=17, body_size=15, title_color=P["green"])
    d.arrow([(480, 155), (600, 190)], P["muted"], "시도", start="a", end="db")
    d.arrow([(480, 275), (600, 245)], P["muted"], "시도", start="b", end="db")
    d.card("one", 1020, 110, 300, 90, "하나는 통과", "행이 만들어진다", bg=P["ok_bg"], stroke=P["green"], title_size=16)
    d.card("two", 1020, 230, 300, 90, "다른 하나는 거절", "거절 방식은 문서 03", bg=P["todo_bg"], stroke=P["orange"], title_size=16)
    d.arrow([(940, 190), (1020, 155)], P["green"], "통과", label_size=11, start="db", end="one")
    d.arrow([(940, 240), (1020, 275)], P["orange"], "거절", label_size=11, start="db", end="two")
    d.card("v", 40, 380, 1280, 150, "남는 일은 앱의 몫이다",
           "그 거절을 \"이미 처리됨\" 으로 해석해 기존 결과를 돌려주는 흐름은 앱이 짠다 (문서 03 · 05 · 06).\n"
           "제약은 중복 행을 막을 뿐이다 — 외부 결제 API 호출 같은 부수효과는 제약과 무관하게 이미 일어났을 수 있다 (문서 06).",
           bg=P["note_bg"], stroke=P["line"], title_size=17, body_size=14)
    d.save()


if __name__ == "__main__":
    for f in (race, why_blind, rr_blind, app_lock, methods, distributed_lock, for_update, unique_guard):
        f()
    finish()
