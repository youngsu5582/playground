#!/usr/bin/env python3
"""01.02 블로그판 05 그림. 실행: python3 -I docs/diagrams/draw_blog05.py (레슨 폴더에서)"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[4] / "tools"))
from diagram import Diagram, P, finish, timeline as _timeline  # noqa: E402

OUT = pathlib.Path(__file__).parent


def timeline(*a, **k):
    return _timeline(*a, out=OUT, **k)


def intro():
    timeline("blog05-intro", "도입: 서로 상대의 행을 기다린다",
             "계좌 11111 · 22222 를 두 트랜잭션이 반대 순서로 UPDATE 한다 (문서 13.3.4 의 예)",
             [("A", "1  UPDATE accounts SET … WHERE acctnum = 11111", "A 가 11111 행의 락을 쥔다", None),
              ("B", "2  UPDATE accounts SET … WHERE acctnum = 22222", "B 가 22222 행의 락을 쥔다", None),
              ("A", "3  UPDATE accounts SET … WHERE acctnum = 22222", "B 가 쥔 행 — 기다린다", "bad"),
              ("B", "4  UPDATE accounts SET … WHERE acctnum = 11111", "A 가 쥔 행 — 기다린다. 원이 닫힌다", "bad")],
             [(2, 1, "A 는 B 의\n행을 기다린다", 0.5), (3, 0, "B 는 A 의\n행을 기다린다", 0.88)],
             "A 는 B 를, B 는 A 를 기다린다. 둘 중 누구도 먼저 끝날 수 없으니 이 기다림은 영원히 풀리지 않는다.\n"
             "락 대기는 보통 무한정이지만, 이렇게 원이 생기면 엔진이 개입한다 — 데드락만이 엔진이 개입하는 유일한 대기다.",
             "서로의 락을 기다리는 원 = 데드락", lane=84)


def wfg():
    d = Diagram("blog05-wait-graph", 1400, 560, "대기 그래프에서 사이클이 있을 때, 그때만 데드락이다",
                "lmgr README — 사이클이 soft 간선(큐 순서만 바꾸면 풀리는 대기)으로만 이뤄졌는가에 따라 다르다", out=OUT)
    d.rect(None, 30, 100, 670, 440, P["white"], P["line"], dashed=True)
    d.text(50, 112, "hard deadlock", 18, P["red"], weight=700)
    d.ellipse("a", 200, 270, 60, "트랜잭션\nA", P["as_bg"], P["front"], size=15)
    d.ellipse("b", 520, 270, 60, "트랜잭션\nB", P["bff_bg"], P["back"], size=15)
    d.arrow([(255, 235), (350, 205), (465, 235)], P["red"], "A 가 B 를 기다린다", label_at=(360, 190))
    d.arrow([(465, 305), (360, 345), (255, 305)], P["red"], "B 가 A 를 기다린다", label_at=(360, 360))
    d.card("hn", 60, 410, 610, 110, "큐를 재배열해도 안 풀린다",
           "시작점의 락 요청을 취소하고\n그 트랜잭션에 에러를 보고하는 것으로 해소한다",
           bg=P["bad_bg"], stroke=P["red"], title_size=15, body_size=14)
    d.rect(None, 720, 100, 650, 440, P["white"], P["line"], dashed=True)
    d.text(740, 112, "soft 간선으로만 된 사이클", 18, P["orange"], weight=700)
    d.ellipse("c", 880, 270, 60, "프로세스\nC", P["as_bg"], P["front"], size=15)
    d.ellipse("e", 1200, 270, 60, "프로세스\nD", P["bff_bg"], P["back"], size=15)
    d.arrow([(935, 235), (1030, 205), (1145, 235)], P["orange"], "큐 순서 대기", label_at=(1040, 190))
    d.arrow([(1145, 305), (1040, 345), (935, 305)], P["orange"], "큐 순서 대기", label_at=(1040, 360))
    d.card("sn", 740, 410, 610, 110, "대기 큐의 순서를 바꾸면 풀린다",
           "아무도 abort 하지 않고 풀 수 있다\n(대기 우선순위 때문에 생긴 대기)",
           bg=P["ok_bg"], stroke=P["green"], title_size=15, body_size=14)
    d.save()


def detect_flow():
    d = Diagram("blog05-detect-flow", 1400, 620, "데드락 감지는 기다리자마자가 아니라 deadlock_timeout 뒤에 돈다",
                "락을 기다리게 된 프로세스는 지연을 두고 타이머를 건다 (lmgr README, 문서 20.12)", out=OUT)
    d.pill("s1", 40, 120, 300, 80, "락 요청이 충돌한다\n→ 대기를 시작한다", P["note_bg"], P["line"], size=15)
    d.pill("s2", 400, 120, 300, 80, "deadlock_timeout 타이머\n(기본 1초)", P["todo_bg"], P["orange"], size=15)
    d.pill("s3", 760, 120, 300, 80, "그 사이에 락을 받으면\n그냥 끝 — 검사 비용 없음", P["ok_bg"], P["green"], size=14)
    d.arrow([(340, 160), (400, 160)], P["muted"])
    d.arrow([(700, 160), (760, 160)], P["muted"], "받았다")
    d.pill("s4", 400, 270, 300, 80, "타이머가 울렸는데도\n락을 못 받았다", P["note_bg"], P["line"], size=15)
    d.arrow([(550, 200), (550, 270)], P["muted"], "못 받았다", label_at=(610, 235))
    d.pill("s5", 400, 400, 300, 80, "데드락 감지/해소 코드를\n돌린다 (대기 그래프 검사)", P["as_bg"], P["front"], size=15)
    d.arrow([(550, 350), (550, 400)], P["muted"])
    d.pill("o1", 40, 520, 340, 80, "사이클 없음 →\n데드락이 아니다. 계속 대기", P["white"], P["line"], size=14)
    d.pill("o2", 430, 520, 340, 80, "soft 사이클만 →\n큐를 재배열, 아무도 abort 안 함", P["ok_bg"], P["green"], size=14)
    d.pill("o3", 820, 520, 380, 80, "hard 사이클 → 시작점의 락 요청 취소\n그 트랜잭션에 에러 (40P01)", P["bad_bg"], P["red"], size=14)
    d.arrow([(450, 480), (210, 520)], P["muted"])
    d.arrow([(550, 480), (600, 520)], P["muted"])
    d.arrow([(650, 480), (1000, 520)], P["muted"])
    d.card("why", 780, 270, 580, 210, "왜 기다리자마자 검사하지 않나",
           "데드락 검사는 비교적 비싸서 서버가 락을 기다릴 때마다\n돌리지 않는다 (문서 20.12)\n\n기본 1초는 \"실제로 쓸 수 있는 가장 작은 값쯤\" 이라고\n문서가 적는다 — 그래서 데드락도 최소 이 시간만큼은 기다린다",
           bg=P["note_bg"], stroke=P["line"], title_size=15, body_size=14)
    d.save()


def upgrade():
    timeline("blog05-upgrade", "락 업그레이드로도 데드락이 생긴다",
             "둘 다 같은 행을 FOR SHARE 로 읽고, 각자 그 행을 UPDATE 한다 (실측: psql 2026-10-13)",
             [("A", "1  SELECT … FROM stock WHERE id = 7 FOR SHARE", "공유 락 — 읽으면서 잠가 둔다", None),
              ("B", "2  SELECT … FROM stock WHERE id = 7 FOR SHARE", "공유 락끼리는 안 막는다 — 둘이 함께 쥔다", None),
              ("A", "3  UPDATE stock SET … WHERE id = 7", "B 의 공유 락이 풀리기를 기다린다", "bad"),
              ("B", "4  UPDATE stock SET … WHERE id = 7", "A 의 공유 락이 풀리기를 기다린다", "bad")],
             [(2, 1, "A 는 B 의\n공유 락 대기", 0.5), (3, 0, "B 는 A 의\n공유 락 대기", 0.88)],
             "실측에서 한쪽이 deadlock detected 로 끊기고 다른 쪽은 UPDATE 1 이었다. 각자 상대의 공유 락이 풀리기를 기다린 원이다.\n"
             "문서: 처음 잡는 락은 필요한 것 중 가장 제한적인 모드여야 한다. 처음부터 FOR UPDATE(또는 FOR NO KEY UPDATE)로 잡으면\n"
             "두 번째 세션은 읽는 시점에 줄을 서고 원이 생기지 않는다.",
             "읽으면서 잠가 두었다가 나중에 고치는 코드가 위험하다", lane=84)


def order():
    d = Diagram("blog05-lock-order", 1400, 620, "예방 — 락 순서를 하나로: 방향이 아니라 행으로 정렬한다",
                "이체 1 → 2 와 2 → 1 이 동시에 온다", out=OUT)
    d.rect(None, 30, 100, 670, 400, P["white"], P["line"], dashed=True)
    d.text(50, 112, "인자 순서대로 (from → to) 잠그면", 17, P["red"], weight=700)
    d.card("t1", 60, 160, 290, 120, "이체 1 → 2", "1 번 행을 잠그고\n2 번 행을 잠근다", bg=P["as_bg"], stroke=P["front"], title_size=15, body_size=14)
    d.card("t2", 380, 160, 290, 120, "이체 2 → 1", "2 번 행을 잠그고\n1 번 행을 잠근다", bg=P["bff_bg"], stroke=P["back"], title_size=15, body_size=14)
    d.card("bad", 60, 320, 610, 150, "서로 상대가 쥔 행을 기다리는 원",
           "각자 첫 행을 쥔 채 둘째 행을 기다린다\n→ 데드락. 끊긴 쪽은 40P01 을 받는다",
           bg=P["bad_bg"], stroke=P["red"], title_size=16, body_size=14)
    d.rect(None, 720, 100, 650, 400, P["white"], P["line"], dashed=True)
    d.text(740, 112, "행 id 의 오름차순으로 잠그면 (구현 2)", 17, P["green"], weight=700)
    d.card("u1", 750, 160, 290, 120, "이체 1 → 2", "first = min = 1 번을 잠그고\nsecond = max = 2 번을 잠근다", bg=P["as_bg"], stroke=P["front"], title_size=15, body_size=14)
    d.card("u2", 1060, 160, 290, 120, "이체 2 → 1", "first = min = 1 번을 잠그고\nsecond = max = 2 번을 잠근다", bg=P["bff_bg"], stroke=P["back"], title_size=15, body_size=14)
    d.card("ok", 750, 320, 600, 150, "원이 생길 수 없다",
           "둘 다 1 → 2 순서이므로, 뒤에 온 쪽은 첫 행에서\n그냥 줄을 선다. UPDATE 의 방향(from → to)은 그대로 둔다",
           bg=P["ok_bg"], stroke=P["green"], title_size=16, body_size=14)
    d.card("n", 30, 520, 1340, 70, "잠그는 대상을 방향이 아니라 행으로 정렬한다 — 문서의 1차 방어: 여러 객체에 대해 일관된 순서로 락을 잡는 것 (13.3.4)",
           None, bg=P["note_bg"], stroke=P["line"], title_size=15)
    d.save()


def retry():
    d = Diagram("blog05-retry", 1400, 620, "순서를 못 정할 때 — 끊긴 트랜잭션을 통째로 재시도한다",
                "문서 13.3.4: 사전에 검증하기 어렵다면 데드락으로 abort 된 트랜잭션을 재시도하는 것으로 즉석에서 처리할 수 있다", out=OUT)
    d.rect(None, 30, 100, 1340, 270, P["white"], P["line"], dashed=True)
    d.text(50, 112, "재시도 루프 — 트랜잭션 바깥 (@Transactional 바깥)", 16, P["muted"], weight=700)
    d.pill("p1", 60, 160, 300, 80, "트랜잭션 전체를\n처음부터 실행", P["as_bg"], P["front"], size=15)
    d.pill("p2", 460, 160, 300, 80, "SQLSTATE 가\n40P01 인가?", P["todo_bg"], P["orange"], size=15)
    d.pill("p3", 860, 160, 300, 80, "아니오 →\n커밋 · 끝", P["ok_bg"], P["green"], size=15)
    d.pill("p4", 460, 275, 300, 80, "예 → 횟수 상한 + 지터로\n잠깐 쉰다", P["bad_bg"], P["red"], size=14)
    d.arrow([(360, 200), (460, 200)], P["muted"])
    d.arrow([(760, 200), (860, 200)], P["muted"], "아니오", label_at=(810, 185))
    d.arrow([(610, 240), (610, 275)], P["red"], "예", label_at=(640, 258))
    d.arrow([(460, 315), (210, 315), (210, 240)], P["red"], "처음부터 다시", label_at=(335, 315))
    d.card("r1", 40, 400, 640, 200, "규칙 (01.01 문서 05 와 같다)",
           "재시도는 트랜잭션 바깥에서, 처음부터 전체를\n(끊긴 트랜잭션은 이미 롤백됐다)\nSQLSTATE 40P01 로 판정한다 — 메시지 문구가 아니라 코드\n횟수 상한 + 지터 (해석 · 일반적인 설계)\n부수효과(메일 · 외부 API)는 커밋 이후로",
           bg=P["note_bg"], stroke=P["line"], title_size=15, body_size=14)
    d.card("r2", 720, 400, 640, 200, "그 밖의 방어",
           "트랜잭션을 짧게 — 락을 쥐는 시간이 줄면\n원이 만들어질 창도 줄어든다 (해석)\n필요한 것을 한 번에 잠그기\n외부 호출을 락 안에 넣지 않기",
           bg=P["note_bg"], stroke=P["line"], title_size=15, body_size=14)
    d.save()


def who_cut():
    timeline("blog05-who-cut", "누가 끊겼나 — 이 랩의 한 번의 관찰 (deadlock_timeout = 5s)",
             "관찰이지 규칙이 아니다. 간격 · 타이머에 따라 달라진다 (psql 2026-10-13)",
             [("A", "1  UPDATE account … WHERE id = 1", "행 1 을 쥔다", None),
              ("B", "2  UPDATE account … WHERE id = 2", "행 2 를 쥔다", None),
              ("A", "3  UPDATE account … WHERE id = 2", "대기 시작 — A 의 타이머가 먼저 시작", None),
              ("B", "4  UPDATE account … WHERE id = 1  (0.5 초 뒤)", "원이 닫힘 — B 의 타이머는 나중에 시작", None),
              ("A", "5  약 5 초 뒤  ERROR: deadlock detected", "먼저 기다리기 시작한 A 가 끊겼다", "bad"),
              ("B", "6  (그대로 진행)", "B 는 성공", "ok")],
             [(2, 1, "A 가 B 의\n행을 기다림", 0.5), (3, 0, "B 가 A 의\n행을 기다림", 0.88)],
             "서버 로그: process … detected deadlock while waiting for ShareLock on transaction … after 5001.485 ms.\n"
             "이 랩의 설명: A 의 타이머가 B 의 것보다 먼저 시작해 먼저 울렸고, A 가 원을 보고 자신을 끊었다. 소스 README 의\n"
             "\"감지를 돌린 프로세스가 자기 트랜잭션을 끊는다\" 와 맞지만 보장은 아니다.",
             "이 한 번의 관찰에서는 먼저 기다린 A 였다", vcolor="note", lane=84)


if __name__ == "__main__":
    for f in (intro, wfg, detect_flow, upgrade, order, retry, who_cut):
        f()
    finish()
