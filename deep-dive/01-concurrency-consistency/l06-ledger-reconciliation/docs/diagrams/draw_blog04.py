#!/usr/bin/env python3
"""01.06 블로그 04 그림 (원장에 기록하기). 실행: python3 -I docs/diagrams/draw_blog04.py (레슨 폴더에서)"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[4] / "tools"))
from diagram import Diagram, P, finish, timeline as _timeline  # noqa: E402

OUT = pathlib.Path(__file__).parent


def timeline(*a, **k):
    return _timeline(*a, out=OUT, **k)


def flow():
    d = Diagram("blog04-flow", 1300, 600, "post(): 이체 한 건이 지나는 길 — 전부 한 트랜잭션",
                "LedgerService#post 정답의 순서 (solutions/01.06.patch)", out=OUT)
    d.rect("tx", 30, 100, 1240, 250, P["white"], P["line"], dashed=True)
    d.text(46, 108, "setAutoCommit(false) — 여기부터 한 트랜잭션", 14, P["muted"])
    steps = [("1  선점", "INSERT posted_txn\nON CONFLICT DO NOTHING", P["ok_bg"], P["green"]),
             ("2  잔고", "UPDATE account\nSET balance = balance + ?\n(계좌 id 순서로 두 번)", P["as_bg"], P["front"]),
             ("3  원장", "INSERT ledger\n두 다리 (-금액 · +금액)", P["rs_bg"], P["orange"]),
             ("4  COMMIT", "지연 트리거가\n다리 합 0 을 검사", P["bff_bg"], P["back"])]
    for i, (a, b, bg, st) in enumerate(steps):
        x = 50 + i * 305
        d.card(f"s{i}", x, 150, 270, 170, a, b, bg=bg, stroke=st, body_size=14, mono_body=False)
        if i:
            d.arrow([(x - 35, 235), (x, 235)], P["muted"])
    d.pill("dup", 50, 400, 380, 70, "선점 실패 (이미 있음) → 롤백 · DUPLICATE", P["note_bg"], P["line"], size=14)
    d.pill("ins", 460, 400, 400, 70, "CHECK 위반(잔고 부족) → 롤백 · INSUFFICIENT", P["bad_bg"], P["red"], size=14)
    d.pill("ok", 890, 400, 380, 70, "COMMIT 성공 → POSTED", P["ok_bg"], P["green"], size=14)
    d.arrow([(185, 320), (240, 400)], P["muted"], "충돌")
    d.arrow([(490, 320), (640, 400)], P["red"], "CHECK 위반")
    d.arrow([(1100, 320), (1080, 400)], P["green"], "통과")
    d.card("n", 30, 500, 1240, 80, "순서의 이유",
           "선점이 맨 앞 — 중복이면 아무것도 건드리지 않는다.  잔고는 DB 안에서 계산 — 읽고 쓰는 틈이 없다.  두 계좌는 id 순서 — 락이 엇갈리지 않는다.",
           bg=P["note_bg"], stroke=P["line"], title_size=15, body_size=14)
    d.save()


def check_then_act():
    timeline("blog04-check-then-act", "있나 확인하고 넣기는 동시에 오면 둘 다 \"없네\" 를 본다",
             "같은 거래 T-60 이 재시도로 두 번 동시에 도착했다 (01.03 의 check-then-act)",
             [("A", "1  SELECT ... FROM posted_txn WHERE txn_id = 'T-60'", "본 값: 없음", None),
              ("B", "2  SELECT ... FROM posted_txn WHERE txn_id = 'T-60'", "본 값: 없음  (A 는 아직 안 넣었다)", None),
              ("A", "3  잔고 · 원장 반영 → COMMIT", "T-60 반영", None),
              ("B", "4  잔고 · 원장 반영 → COMMIT", "T-60 이 한 번 더 반영된다", "bad")],
             [(0, 1, "A 의 확인이\nB 에게 안 보인다", 0.5)],
             "확인과 선점이 두 문장이면 그 틈에 둘 다 통과한다.  INSERT … ON CONFLICT DO NOTHING 한 문장으로 확인과 선점을 한꺼번에 한다.",
             "같은 거래가 두 번 반영된다", level="READ COMMITTED")


def claim_timeline():
    timeline("blog04-claim", "한 문장으로 선점하면 두 번째는 기다렸다가 \"이미 처리됨\" 을 받는다",
             "같은 거래 T-60 을 두 세션이 동시에 올린다",
             [("A", "1  INSERT posted_txn T-60 ON CONFLICT DO NOTHING", "내가 처음 — 선점 (아직 커밋 전)", "ok"),
              ("B", "2  INSERT posted_txn T-60 ON CONFLICT DO NOTHING", "A 가 끝나기를 기다린다", None),
              ("A", "3  잔고 · 원장 반영 → COMMIT", "T-60 반영", None),
              ("B", "4  (대기 끝) 충돌 → 건너뜀 → 롤백", "DUPLICATE 반환 — 아무것도 반영하지 않는다", "ok")],
             [(0, 1, "B 가 A 의 결과를\n기다린다", 0.3)],
             "B 는 오류가 아니라 \"이미 처리됨\" 을 받는다 — 호출한 쪽이 재시도해도 안전하다.\n"
             "A 가 롤백했다면 B 의 선점이 성공한다 (실측: psql 2026-10-13, 03 문서의 동시 선점 실측).",
             "정확히 한 번만 반영된다", vcolor="ok", level="READ COMMITTED")


def lost_update():
    timeline("blog04-lost-update", "읽고 → 앱에서 계산 → 덮어쓰면 한쪽 출금이 사라진다",
             "계좌 11 잔고 1000. A 가 100, B 가 200 을 보낸다 (앱이 잔고를 읽어 빼고 다시 쓴다)",
             [("A", "1  SELECT balance", "본 값: 1000", None),
              ("B", "2  SELECT balance", "본 값: 1000", None),
              ("A", "3  UPDATE balance = 900  → COMMIT", "1000 - 100", None),
              ("B", "4  UPDATE balance = 800  → COMMIT", "1000 - 200  (A 의 100 이 사라진다)", "bad")],
             [(2, 3, "A 의 쓰기를\nB 가 덮어쓴다", 0.5)],
             "직렬로 돌렸다면 1000 - 100 - 200 = 700.  원장에는 두 이체가 모두 쌓였는데 잔고만 800 이다 — 대사가 찾는 어긋남이 이렇게 생긴다.",
             "잔고 800 ≠ 원장 합 700", level="READ COMMITTED")


def atomic():
    d = Diagram("blog04-atomic", 1260, 520, "잔고 갱신은 DB 안에서 한 문장으로",
                "UPDATE account SET balance = balance + ? — 읽기와 계산과 쓰기가 한 문장이다", out=OUT)
    d.card("a", 40, 110, 570, 190, "읽고 계산해서 덮어쓰기",
           "SELECT balance   ← 락 없이 읽는다\nnew = balance - amount   ← 앱에서 계산\nUPDATE … SET balance = new   ← 덮어쓴다",
           bg=P["bad_bg"], stroke=P["red"], body_size=13, mono_body=True)
    d.card("b", 650, 110, 570, 190, "상대값으로 갱신",
           "UPDATE account\n   SET balance = balance + ?\n WHERE id = ?\n\n행 락을 잡고, 기다렸다면 갱신된 최신 행에 다시 적용한다",
           bg=P["ok_bg"], stroke=P["green"], body_size=14, mono_body=True)
    d.arrow([(325, 300), (325, 350)], P["red"], "갱신 손실")
    d.arrow([(935, 300), (935, 350)], P["green"], "READ COMMITTED 재평가")
    d.card("c", 40, 360, 570, 130, "01.04", "읽고-계산-쓰기의 틈은 락 · 원자적 갱신 · 낙관적 락 등으로 메운다 — 01.04 문서", bg=P["note_bg"], stroke=P["line"], title_size=15)
    d.card("e", 650, 360, 570, 130, "실측 (psql 2026-10-13)",
           "잔고 85 에서 두 세션이 동시에 -60:\n첫 번째가 25 로 만든 뒤, 두 번째는 기다렸다가 25 - 60 = -35 로\n계산해 CHECK 에서 거절됐다 (갱신된 행에 적용)",
           bg=P["note_bg"], stroke=P["line"], title_size=15, body_size=13)
    d.save()


def insufficient():
    d = Diagram("blog04-insufficient", 1260, 540, "잔고 부족이면 선점도 같이 롤백한다",
                "거절된 거래 id 가 \"이미 처리됨\" 으로 남으면, 입금된 뒤에 같은 id 로 다시 시도해도 영영 DUPLICATE 다", out=OUT)
    d.text(40, 100, "옳은 방법 — 전체 롤백", 17, P["green"], weight=700)
    for i, (t, bg, st) in enumerate([("선점 INSERT", P["ok_bg"], P["green"]), ("잔고 UPDATE\nCHECK 위반", P["bad_bg"], P["red"]), ("ROLLBACK\n(선점도 사라진다)", P["ok_bg"], P["green"]), ("INSUFFICIENT\n같은 id 로 재시도 가능", P["ok_bg"], P["green"])]):
        x = 40 + i * 310
        d.pill(f"a{i}", x, 140, 270, 80, t, bg, st, size=14)
        if i:
            d.arrow([(x - 40, 180), (x, 180)], P["muted"])
    d.text(40, 270, "잘못된 방법 — 선점만 커밋", 17, P["red"], weight=700)
    for i, (t, bg, st) in enumerate([("선점 INSERT\n→ 커밋", P["rs_bg"], P["orange"]), ("잔고 UPDATE\nCHECK 위반", P["bad_bg"], P["red"]), ("선점은 남는다", P["bad_bg"], P["red"]), ("재시도 → DUPLICATE\n입금해도 영영 반영 안 됨", P["bad_bg"], P["red"])]):
        x = 40 + i * 310
        d.pill(f"b{i}", x, 310, 270, 80, t, bg, st, size=14)
        if i:
            d.arrow([(x - 40, 350), (x, 350)], P["muted"])
    d.card("n", 40, 430, 1180, 90, "구현 테스트가 확인한다",
           "LedgerImplementTest 의 가드: 잔고 부족 거절 뒤 같은 거래 id 로 입금 후 재시도하면 POSTED 여야 하고 원장에는 흔적이 없어야 한다.",
           bg=P["note_bg"], stroke=P["line"], title_size=15)
    d.save()


def deadlock():
    timeline("blog04-deadlock", "서로 반대 방향 이체가 락을 엇갈려 잡으면 데드락이다",
             "A: 계좌 11 → 12 · B: 계좌 12 → 11. 각자 보내는 쪽부터 UPDATE 한다 (행 락은 트랜잭션 끝까지 잡힌다)",
             [("A", "1  UPDATE 계좌 11  (balance - 10)", "11 번 행 락을 잡는다", None),
              ("B", "2  UPDATE 계좌 12  (balance - 5)", "12 번 행 락을 잡는다", None),
              ("A", "3  UPDATE 계좌 12  (balance + 10)", "B 의 락을 기다린다", None),
              ("B", "4  UPDATE 계좌 11  (balance + 5)", "A 의 락을 기다린다 → 서로 기다림", "bad")],
             [(0, 3, "B 가 A 의 11 을\n기다린다", 0.8), (1, 2, "A 가 B 의 12 를\n기다린다", 0.4)],
             "deadlock_timeout(기본 1초) 뒤 엔진이 순환을 찾아 한쪽을 중단시킨다 — ERROR: deadlock detected (SQLSTATE 40P01).\n"
             "실측: B 가 중단되고 A 는 커밋했다 (psql 2026-10-13). 누가 중단될지는 예측하지 않는다 (문서 13.3.4).",
             "락을 엇갈려 잡았다", level="READ COMMITTED")


def lock_order():
    timeline("blog04-lock-order", "항상 id 가 작은 계좌부터 갱신하면 순환이 생기지 않는다",
             "같은 두 이체. 이번에는 둘 다 11 번 → 12 번 순서로 갱신한다 (post 정답의 방식)",
             [("A", "1  UPDATE account … WHERE id = 11", "11 번 행 락", None),
              ("B", "2  UPDATE account … WHERE id = 11", "A 가 끝나기를 기다린다 (첫 락에서 줄을 선다)", None),
              ("A", "3  UPDATE account … WHERE id = 12 → COMMIT", "12 번도 잡고 커밋 — 락이 풀린다", "ok"),
              ("B", "4  (대기 끝) 11 → 12 갱신 → COMMIT", "순환이 없으니 둘 다 끝난다", "ok")],
             [(0, 1, "B 가 A 의 11 을\n기다린다", 0.4)],
             "기다림은 있지만 한 방향이라 데드락이 아니다.  문서 13.3.4: 여러 객체의 락을 항상 같은 순서로 잡는 것이 가장 좋은 방어다.\n"
             "실측: 같은 순서로 돌린 두 이체는 모두 COMMIT 했다 (psql 2026-10-13).",
             "같은 순서면 줄만 선다", vcolor="ok", level="READ COMMITTED")


def error_map():
    d = Diagram("blog04-error-map", 1260, 520, "post() 가 에러를 어떻게 번역하나",
                "SQLSTATE 로 가른다 — 메시지 문구가 아니라 코드 (문서 부록 A)", out=OUT)
    rows = [("충돌 (이미 처리됨)", "ON CONFLICT 로 건너뜀", "DUPLICATE (정상 결과)", P["note_bg"], P["line"]),
            ("CHECK 위반", "잔고 부족", "롤백 · INSUFFICIENT", P["rs_bg"], P["orange"]),
            ("40P01 deadlock_detected", "락 순서 엇갈림 (버그 신호)", "예외 — 호출자가 재시도 판단 (해석)", P["bad_bg"], P["red"]),
            ("그 밖의 SQLException", "연결 · 문법 · 합 0 위반 …", "롤백 · 예외로 던진다", P["bad_bg"], P["red"]),
            ("성공", "COMMIT 통과", "POSTED", P["ok_bg"], P["green"])]
    for i, t in enumerate(["받은 것", "뜻", "post() 의 결과"]):
        x = [40, 420, 830][i]
        w = [360, 390, 390][i]
        d.pill(f"h{i}", x, 100, w, 46, t, P["note_bg"], P["line"], size=14)
    for r, (a, b, c, bg, st) in enumerate(rows):
        y = 160 + r * 66
        for i, (t, x, w) in enumerate([(a, 40, 360), (b, 420, 390), (c, 830, 390)]):
            d.pill(f"r{r}{i}", x, y, w, 54, t, bg if i == 2 else P["white"], st if i == 2 else P["line"], size=13)
    d.save()


if __name__ == "__main__":
    for f in (flow, check_then_act, claim_timeline, lost_update, atomic, insufficient, deadlock, lock_order, error_map):
        f()
    finish()
