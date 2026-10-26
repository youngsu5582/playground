#!/usr/bin/env python3
"""01.04 블로그판 02 그림. 실행: python3 -I docs/diagrams/draw_blog02.py (레슨 폴더에서)"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[4] / "tools"))
from diagram import Diagram, P, finish, timeline as _timeline  # noqa: E402

OUT = pathlib.Path(__file__).parent


def timeline(*a, **k):
    return _timeline(*a, out=OUT, **k)


def intro():
    timeline("blog02-intro", "도입: 같은 행에 두 UPDATE 가 동시에 온다",
             "재고 6, A 는 2 개 · B 는 3 개를 산다. 확인(qty >= n)과 차감이 한 문장 안에 있다",
             [("A", "1  UPDATE qty = qty - 2 WHERE qty >= 2", "행 락을 잡고 qty 를 4 로 바꾼다 (아직 COMMIT 전)", None),
              ("B", "2  UPDATE qty = qty - 3 WHERE qty >= 3", "같은 행이라 A 가 끝나기를 기다린다", None),
              ("A", "3  COMMIT", "행 락이 풀린다", None),
              ("B", "4  (기다림이 끝나고 WHERE 를 다시 평가)", "최신 qty 4 → 4 >= 3 → qty = 1, 영향 행 1", "ok")],
             [(0, 1, "행 락이\nB 를 세운다", 0.3), (2, 3, "커밋된 최신 값으로\nB 가 재평가", 0.7)],
             "B 는 처음 본 값(6)이 아니라 A 가 커밋한 최신 값(4)에서 계산했다. 읽기와 쓰기 사이에 낡은 값이 낄 자리가 없다.\n"
             "A 의 2 개가 B 의 계산에 반영되어, 둘이 합쳐 5 개가 팔리고 재고 1 이 남는다.",
             "먼저 온 쪽이 줄을 세우고, 기다린 쪽은 최신 값으로 다시 본다", vcolor="ok")


def one_statement():
    d = Diagram("blog02-one-statement", 1460, 420, "한 문장이 틈을 없앤다",
                "읽기 - 확인 - 쓰기를 한 문장으로 붙인다", out=OUT)
    d.card("sql", 40, 110, 1380, 80, "UPDATE stock SET qty = qty - :n WHERE sku = :sku AND qty >= :n",
           None, bg=P["as_bg"], stroke=P["front"], title_size=20)
    parts = [("qty = qty - :n", "계산을 DB 가 현재 값으로 한다\n앱이 읽어 둔 값을 쓰지 않는다", P["ok_bg"], P["green"]),
             ("AND qty >= :n", "검사가 같은 문장 안에 있다\n사이에 끼어들 틈이 없다", P["ok_bg"], P["green"]),
             ("영향 행 수", "1 = 성공\n0 = 조건 불일치(품절)\nJDBC 의 executeUpdate() 반환값", P["todo_bg"], P["orange"])]
    for i, (t, b, bg, st) in enumerate(parts):
        x = 40 + i * 470
        d.card(f"p{i}", x, 270, 440, 120, t, b, bg=bg, stroke=st, title_size=18, body_size=15)
        d.arrow([(x + 220 if i != 2 else x + 220, 190), (x + 220, 270)], st)
    d.save()


def three_steps():
    d = Diagram("blog02-three-steps", 1460, 560, "왜 안전한가 — 행 락 → 대기 → 재평가",
                "같은 행에 두 구매자가 이 문장을 동시에 날린다", out=OUT)
    d.pill("s1", 40, 120, 360, 110, "1  행 락\n먼저 행을 잡은 쪽(A)이 갱신한다\n충돌 락을 둘이 가질 수 없다", P["as_bg"], P["front"], size=15)
    d.pill("s2", 500, 120, 360, 110, "2  대기\n늦게 온 쪽(B)은 A 가\n커밋하거나 롤백할 때까지 기다린다", P["bad_bg"], P["red"], size=15)
    d.pill("s3", 960, 120, 460, 110, "3  재평가 (READ COMMITTED)\nA 가 끝난 뒤 B 가 어떻게 진행하나", P["todo_bg"], P["orange"], size=15)
    d.arrow([(400, 175), (500, 175)], P["muted"], start="s1", end="s2")
    d.arrow([(860, 175), (960, 175)], P["muted"], start="s2", end="s3")
    d.card("rb", 760, 320, 300, 130, "A 가 롤백하면", "B 는 원래 찾은 행으로\n그대로 진행한다", bg=P["ok_bg"], stroke=P["green"], title_size=16, body_size=14)
    d.card("cm", 1100, 320, 320, 130, "A 가 커밋하면", "B 는 갱신된 버전에\n자기 연산을 적용하고\nWHERE 를 다시 평가한다", bg=P["note_bg"], stroke=P["line"], title_size=16, body_size=14)
    d.arrow([(1190, 230), (910, 320)], P["green"], "롤백", start="s3", end="rb", label_at=(1020, 262))
    d.arrow([(1190, 230), (1260, 320)], P["orange"], "커밋", start="s3", end="cm", label_at=(1235, 270))
    d.card("ok", 1100, 490, 150, 52, "맞으면 계속", None, bg=P["ok_bg"], stroke=P["green"], title_size=14)
    d.card("no", 1270, 490, 150, 52, "아니면 0행", None, bg=P["bad_bg"], stroke=P["red"], title_size=14)
    d.arrow([(1190, 450), (1175, 490)], P["green"], start="cm", end="ok")
    d.arrow([(1330, 450), (1345, 490)], P["red"], start="cm", end="no")
    d.card("note", 40, 320, 680, 130, "재평가가 핵심이다",
           "B 가 처음 본 값이 아니라 A 가 커밋한 최신 값에 대해\nqty - n 과 qty >= n 이 계산된다.\n(자세한 규칙은 01.01 docs 04)",
           bg=P["note_bg"], stroke=P["line"], title_size=16, body_size=14)
    d.save()


def wait_view():
    d = Diagram("blog02-wait", 1460, 330, "줄을 세우는 모양 — pg_stat_activity 에서 보이는 것",
                "B 가 기다리는 동안 B 의 행을 조회하면", out=OUT)
    d.card("b", 40, 120, 480, 110, "세션 B  (기다리는 쪽)",
           "wait_event_type = Lock\nwait_event = transactionid", bg=P["bff_bg"], stroke=P["back"], title_size=17, body_size=15)
    d.card("a", 940, 120, 480, 110, "세션 A  (행을 먼저 갱신한 쪽)",
           "트랜잭션 ID 를 쥐고 있다\n커밋 · 롤백 전", bg=P["as_bg"], stroke=P["front"], title_size=17, body_size=15)
    d.arrow([(520, 175), (940, 175)], P["red"], "A 의 트랜잭션 ID 를 기다린다", start="b", end="a", label_size=14)
    d.card("n", 40, 260, 1380, 50, "행 락은 pg_locks 에 한 줄로 나오지 않고 튜플에 적힌다 (문서 13.3.2)", None,
           bg=P["note_bg"], stroke=P["line"], title_size=15)
    d.save()


def returning():
    d = Diagram("blog02-returning", 1460, 440, "RETURNING — 성공 여부와 남은 재고를 한 왕복에",
                "UPDATE ... WHERE ... AND qty >= :n RETURNING qty", out=OUT)
    d.pill("u", 40, 150, 420, 110, "UPDATE stock\nSET qty = qty - :n\nWHERE ... AND qty >= :n  RETURNING qty", P["as_bg"], P["front"], size=15)
    d.card("y", 640, 110, 780, 100, "갱신된 행이 있다", "갱신 후 값(qty)을 한 줄로 돌려준다 → 성공 + 남은 재고", bg=P["ok_bg"], stroke=P["green"], title_size=17, body_size=15)
    d.card("n", 640, 250, 780, 100, "갱신된 행이 없다", "결과가 0 행 (UPDATE 0) → 품절 · 조건 불일치", bg=P["bad_bg"], stroke=P["red"], title_size=17, body_size=15)
    d.arrow([(460, 190), (640, 160)], P["green"], start="u", end="y")
    d.arrow([(460, 230), (640, 300)], P["red"], start="u", end="n")
    d.text(40, 390, "읽기 → 쓰기를 두 문장으로 나누는 대신, 쓰기 문장이 값을 돌려주게 한다", 15, P["muted"])
    d.save()


def rc_vs_rr():
    d = Diagram("blog02-rc-vs-rr", 1460, 430, "기다린 뒤 B 는 — READ COMMITTED 와 REPEATABLE READ",
                "A 가 같은 행을 갱신하고 커밋한 경우", out=OUT)
    d.card("rc", 40, 110, 680, 190, "READ COMMITTED (기본값)",
           "B 는 기다린 뒤 갱신된 버전에 WHERE 를 재평가한다\n맞으면 계속, 아니면 0 행\n\n앱의 재시도가 필요 없다",
           bg=P["ok_bg"], stroke=P["green"], title_size=18, body_size=15)
    d.card("rr", 760, 110, 660, 190, "REPEATABLE READ",
           "재평가가 없다\n스냅샷이 고정된 B 가 그 사이 커밋된 행을 고치려 하면\nERROR: could not serialize access due to\nconcurrent update  (40001)",
           bg=P["bad_bg"], stroke=P["red"], title_size=18, body_size=15)
    d.card("n", 40, 330, 1380, 70, "그래서 REPEATABLE READ · SERIALIZABLE 서비스의 원자 UPDATE 는 앱의 재시도(트랜잭션 전체)와 짝을 이룬다", None,
           bg=P["note_bg"], stroke=P["line"], title_size=15)
    d.save()


def check_net():
    d = Diagram("blog02-check", 1460, 430, "안전망 — CHECK 제약이 잡는 것과 못 잡는 것",
                "qty int CHECK (qty >= 0)", out=OUT)
    d.card("a", 40, 110, 680, 160, "잡는다 — 음수",
           "조건 qty >= n 을 빼먹은 UPDATE 가 음수로 만드는 순간\nnew row for relation \"t\" violates\ncheck constraint \"t_qty_check\"",
           bg=P["ok_bg"], stroke=P["green"], title_size=18, body_size=15)
    d.card("b", 760, 110, 660, 160, "못 잡는다 — 갱신 손실",
           "SET qty = ? 로 덮어쓰는 코드는\n음수가 아니어도 틀린다\n(01 의 틈은 CHECK 가 보지 않는다)",
           bg=P["bad_bg"], stroke=P["red"], title_size=18, body_size=15)
    d.card("n", 40, 310, 1380, 70, "CHECK 는 음수 방지 안전망일 뿐, 정합성의 근거는 한 문장 안의 검사다", None,
           bg=P["note_bg"], stroke=P["line"], title_size=15)
    d.save()


if __name__ == "__main__":
    for f in (intro, one_statement, three_steps, wait_view, returning, rc_vs_rr, check_net):
        f()
    finish()
