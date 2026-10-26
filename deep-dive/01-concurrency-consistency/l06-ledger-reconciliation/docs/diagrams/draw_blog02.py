#!/usr/bin/env python3
"""01.06 블로그 02 그림 (잔고와 원장). 실행: python3 -I docs/diagrams/draw_blog02.py (레슨 폴더에서)"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[4] / "tools"))
from diagram import Diagram, P, finish  # noqa: E402

OUT = pathlib.Path(__file__).parent


def intro():
    d = Diagram("blog02-intro", 1160, 480, "도입: 잔고가 70 인데, 왜 70 인가",
                "잔고를 숫자 하나로만 들고 있으면 \"지금 값\" 만 남고 \"어떻게 이 값이 됐나\" 가 사라진다", out=OUT)
    d.card("a", 40, 110, 330, 120, "account", "id = 11\nbalance = 70.00", bg=P["as_bg"], stroke=P["front"], mono_body=True, body_size=16)
    qs = [("언제 줄었나?", 440, 110), ("누가 얼마 뺐나?", 740, 110), ("처음은 얼마였나?", 440, 190), ("100 이었다면 30 은 어디로?", 740, 190)]
    for i, (q, x, y) in enumerate(qs):
        d.pill(f"q{i}", x, y, 280 if i != 3 else 380, 56, q, P["bad_bg"], P["red"], size=15)
    d.arrow([(370, 170), (440, 138)], P["red"])
    d.arrow([(370, 170), (440, 218)], P["red"])
    d.card("v", 40, 300, 1080, 140, "숫자 하나로는 답할 수 없다",
           "잔고가 틀렸다는 사실조차 알아채기 어렵다 — 비교할 근거가 없기 때문이다.\n"
           "그래서 잔고를 \"결과\" 로 두고, 그 근거가 되는 거래 내역을 따로 쌓는다.  이 글이 그 구조(원장)를 설명한다.",
           bg=P["note_bg"], stroke=P["line"], title_size=16)
    d.save()


def ledger_table():
    d = Diagram("blog02-ledger-rows", 1160, 520, "원장: 거래 내역을 한 줄씩 쌓는다",
                "계좌 11 의 원장 — amount 는 그 계좌의 잔고에 더해지는 값 (+ 입금 · - 출금)", out=OUT)
    heads = [("entry_id", 40, 120), ("txn_id", 170, 160), ("account_id", 340, 170), ("amount", 520, 150), ("읽는 법", 680, 440)]
    for i, (t, x, w) in enumerate(heads):
        d.pill(f"h{i}", x, 100, w, 46, t, P["note_bg"], P["line"], size=14, mono=True)
    rows = [("1", "OPEN-11", "11", "+100.00", "개설 입금 100"), ("2", "T-21", "11", "-30.00", "이체로 30 나감"), ("3", "T-35", "11", "+0.00", "")]
    rows = rows[:2]
    for r, (a, b, c, e, f) in enumerate(rows):
        y = 160 + r * 60
        for i, (t, x, w) in enumerate([(a, 40, 120), (b, 170, 160), (c, 340, 170), (e, 520, 150), (f, 680, 440)]):
            d.pill(f"r{r}{i}", x, y, w, 48, t, P["white"], P["line"], size=14, mono=(i < 4))
    d.arrow([(595, 285), (595, 330)], P["green"], "SUM(amount)")
    d.pill("sum", 400, 335, 390, 56, "원장 합 = +100.00 - 30.00 = 70.00", P["ok_bg"], P["green"], size=16)
    d.pill("bal", 830, 335, 290, 56, "balance = 70.00", P["as_bg"], P["front"], size=16)
    d.arrow([(790, 363), (830, 363)], P["green"], "같다", label_at=(810, 335))
    d.card("n", 40, 420, 1080, 80, "잔고를 설명할 수 있다",
           "70 은 \"개설 100 에서 거래 T-21 로 30 이 나간 결과\" 다. 줄을 지우거나 고치지 않고 쌓기만 하므로 이력이 그대로 남는다.",
           bg=P["note_bg"], stroke=P["line"], title_size=15)
    d.save()


def balance_is_sum():
    d = Diagram("blog02-balance-sum", 1160, 440, "잔고는 원장의 합이다",
                "두 곳이 같은 사실을 말한다 — 같으면 정상, 다르면 어딘가가 틀린 것이다", out=OUT)
    d.card("l", 40, 130, 420, 160, "ledger  (진실의 근거)",
           "계좌 11:  +100.00 · -30.00 · +5.00 · …\n거래가 생길 때마다 한 줄 추가\n고치거나 지우지 않는다 (append-only)",
           bg=P["rs_bg"], stroke=P["orange"], body_size=15)
    d.card("a", 700, 130, 420, 160, "account.balance  (읽기용 요약)",
           "계좌 11:  75.00\n거래가 생길 때마다 같이 갱신\n읽을 때 SUM 을 안 해도 된다",
           bg=P["as_bg"], stroke=P["front"], body_size=15)
    d.pill("eq", 500, 180, 160, 60, "같아야 한다", P["ok_bg"], P["green"], size=16)
    d.arrow([(460, 210), (500, 210)], P["green"])
    d.arrow([(700, 210), (660, 210)], P["green"])
    d.card("v", 40, 330, 1080, 90, "어긋나면?",
           "원장이 \"쌓기만 하는 기록\" 이라 원장을 근거로 본다.  어긋남을 찾는 일이 대사다 (05).",
           bg=P["note_bg"], stroke=P["line"], title_size=16)
    d.save()


def two_legs():
    d = Diagram("blog02-two-legs", 1240, 560, "이체 한 건 = 원장 두 줄 + 잔고 두 곳",
                "계좌 11 → 계좌 12 로 30.00 이체 (거래 T-21). 두 다리의 합은 0 이다", out=OUT)
    d.card("t", 40, 110, 420, 80, "거래 T-21", "계좌 11 에서 30.00 을 계좌 12 로", bg=P["note_bg"], stroke=P["line"], title_size=17)
    d.card("l1", 540, 100, 330, 76, "ledger 다리 1 (차변)", "(T-21, 계좌 11, -30.00)", bg=P["bad_bg"], stroke=P["red"], mono_body=True, body_size=14)
    d.card("l2", 540, 200, 330, 76, "ledger 다리 2 (대변)", "(T-21, 계좌 12, +30.00)", bg=P["ok_bg"], stroke=P["green"], mono_body=True, body_size=14)
    d.arrow([(460, 150), (540, 138)], P["muted"])
    d.arrow([(460, 160), (540, 238)], P["muted"])
    d.pill("z", 920, 150, 280, 76, "-30.00 + 30.00 = 0", P["ok_bg"], P["green"], size=17)
    d.arrow([(870, 138), (920, 175)], P["green"], "합")
    d.arrow([(870, 238), (920, 205)], P["green"])
    d.card("b1", 540, 330, 330, 80, "account 11", "balance = balance - 30.00", bg=P["as_bg"], stroke=P["front"], mono_body=True)
    d.card("b2", 920, 330, 280, 80, "account 12", "balance = balance + 30.00", bg=P["as_bg"], stroke=P["front"], mono_body=True)
    d.arrow([(705, 276), (705, 330)], P["front"], "같은 트랜잭션에서")
    d.arrow([(1060, 226), (1060, 330)], P["front"], "같은 트랜잭션에서")
    d.card("n", 40, 450, 1160, 90, "차변 · 대변 (일반 개념 · 해석)",
           "복식부기에서는 모든 거래를 \"어디서 나가고 어디로 들어갔나\" 두 줄로 적고 두 줄의 합이 0 이 되게 한다.\n"
           "이 레슨은 그 틀을 빌렸다 — 차변은 -금액, 대변은 +금액이다. 합이 0 이 아닌 거래는 규칙 위반이다 (03).",
           bg=P["note_bg"], stroke=P["line"], title_size=15)
    d.save()


def cache():
    d = Diagram("blog02-cache", 1280, 560, "잔고 컬럼은 합계의 캐시다 — 그래서 어긋날 수 있다",
                "읽기를 빠르게 하려고 요약을 둔다 — 대신 쓸 때 두 곳을 맞춰야 한다 (해석)", out=OUT)
    d.text(40, 100, "읽기", 18, P["ink"], weight=700)
    d.card("r1", 40, 135, 560, 100, "잔고 컬럼 없이", "SELECT SUM(amount) FROM ledger WHERE account_id = 11\n→ 그 계좌의 원장 행 수만큼 읽어야 한다 (일반 개념 · 해석)",
           bg=P["bad_bg"], stroke=P["red"], body_size=14)
    d.card("r2", 680, 135, 560, 100, "잔고 컬럼이 있으면", "SELECT balance FROM account WHERE id = 11\n→ 행 하나만 읽는다",
           bg=P["ok_bg"], stroke=P["green"], body_size=14)
    d.text(40, 270, "쓰기", 18, P["ink"], weight=700)
    d.card("w1", 40, 305, 380, 90, "원장에 한 줄 INSERT", "근거를 쌓는다", bg=P["rs_bg"], stroke=P["orange"])
    d.card("w2", 500, 305, 380, 90, "잔고 UPDATE", "요약을 맞춘다", bg=P["as_bg"], stroke=P["front"])
    d.arrow([(420, 350), (500, 350)], P["muted"], "둘 다")
    d.pill("tx", 940, 320, 300, 60, "한 트랜잭션 안에서", P["ok_bg"], P["green"], size=16)
    d.card("v", 40, 430, 1200, 100, "한쪽만 바뀌면 어긋난다",
           "코드 버그 · 수작업 UPDATE · 장애 중 일부 반영 · 동시 갱신 손실(01.04) — 이유는 여럿이다.\n"
           "그래서 막는 장치(제약 · 원자적 갱신)와 틀렸을 때 알아채는 장치(대사)를 둘 다 둔다.",
           bg=P["note_bg"], stroke=P["line"], title_size=16)
    d.save()


def invariants():
    d = Diagram("blog02-invariants", 1280, 520, "지켜야 하는 세 가지 (불변식)",
                "이 레슨의 스키마와 테스트가 지키는 것 — 앞 둘이 지켜지면 셋째는 따라온다", out=OUT)
    items = [("1  거래별", "한 거래의 다리 합 = 0", "DB 가 커밋 때 검사한다\n(지연 제약 트리거 — 03)", P["ok_bg"], P["green"]),
             ("2  계좌별", "잔고 = 그 계좌의 원장 합", "원자적 갱신으로 막고\n대사로 확인한다 (04 · 05)", P["as_bg"], P["front"]),
             ("3  전체", "모든 잔고의 합 = 0", "1 · 2 가 지켜지면 따라온다\n값싼 점검으로도 쓴다", P["rs_bg"], P["orange"])]
    for i, (a, b, c, bg, st) in enumerate(items):
        x = 40 + i * 410
        d.card(f"c{i}", x, 120, 380, 240, a, b + "\n\n" + c, bg=bg, stroke=st, title_size=18, body_size=16)
    d.card("n", 40, 390, 1200, 100, "왜 전체 합이 0 인가",
           "돈이 바깥에서 들어오고 나가는 상대편으로 시스템 계정(id 0)을 두기 때문이다 (스키마 주석).  시스템 계정은 마이너스 잔고가 허용된다.\n"
           "그래서 이체는 돈을 만들지도 없애지도 않는다 — 전체 합이 0 이 아니면 어딘가 새거나 어긋난 것이다.",
           bg=P["note_bg"], stroke=P["line"], title_size=15)
    d.save()


def reversal():
    d = Diagram("blog02-reversal", 1300, 560, "잘못 올린 거래는 고치지 않고 반대 거래를 쌓는다",
                "T-40 (계좌 11 → 12, 50.00) 이 잘못 올라갔다고 하자 (일반 개념 · 해석)", out=OUT)
    d.card("x", 40, 110, 560, 150, "고쳐 쓰기  (UPDATE / DELETE)",
           "원장의 T-40 줄을 수정하거나 지운다\n→ 이 레슨의 스키마는 BEFORE UPDATE OR DELETE 행 트리거로 막는다\n→ 막지 않으면 \"왜 이 잔고인가\" 의 근거가 사라진다",
           bg=P["bad_bg"], stroke=P["red"], body_size=14)
    d.card("o", 680, 110, 560, 150, "반대 거래 쌓기",
           "새 거래 R-40 : 계좌 12 → 11, 50.00\n원장에 줄이 둘 더 생긴다 (+ 잔고 두 곳 갱신)\n→ 이력이 모두 남고 합은 다시 맞는다",
           bg=P["ok_bg"], stroke=P["green"], body_size=14)
    heads = ["txn_id", "account", "amount"]
    for i, t in enumerate(heads):
        d.pill(f"h{i}", 680 + i * 190, 300, 180, 40, t, P["note_bg"], P["line"], size=13, mono=True)
    rows = [("T-40", "11", "-50.00", False), ("T-40", "12", "+50.00", False), ("R-40", "12", "-50.00", True), ("R-40", "11", "+50.00", True)]
    for r, row in enumerate(rows):
        for i, t in enumerate(row[:3]):
            d.pill(f"r{r}{i}", 680 + i * 190, 348 + r * 46, 180, 40, t, P["ok_bg"] if row[3] else P["white"], P["green"] if row[3] else P["line"], size=13, mono=True)
    d.card("n", 40, 300, 560, 240, "순서",
           "1. 어긋남(또는 오류)을 찾는다 — 대사 (05)\n2. 원인을 본다 — 고치기 전에\n3. 반대 거래를 같은 방식으로 올린다\n    (멱등 선점 · 두 다리 · 잔고 갱신 — 04)\n4. 다시 대사해서 맞는지 확인한다",
           bg=P["note_bg"], stroke=P["line"], title_size=16, body_size=15)
    d.save()


def schema():
    d = Diagram("blog02-schema", 1300, 560, "이 레슨의 테이블 네 개",
                "스키마: src/main/resources/ledger-schema.sql — 테스트와 observe 가 같이 쓴다", out=OUT)
    d.card("a", 40, 110, 290, 200, "account", "id  int  PK\nbalance  numeric(20,2)\n  CHECK (balance >= 0\n          OR id = 0)\n\n잔고 (읽기용 요약)", bg=P["as_bg"], stroke=P["front"], mono_body=True, body_size=13)
    d.card("l", 360, 110, 330, 200, "ledger", "entry_id  bigserial  PK\ntxn_id  text\naccount_id  int\namount  numeric(20,2)\nUNIQUE (txn_id, account_id)\n\n원장 (쌓기만 한다)", bg=P["rs_bg"], stroke=P["orange"], mono_body=True, body_size=13)
    d.card("p", 720, 110, 260, 200, "posted_txn", "txn_id  text  PK\n\n\n이미 반영한 거래 id\n(멱등 선점)", bg=P["ok_bg"], stroke=P["green"], mono_body=True, body_size=13)
    d.card("e", 1010, 110, 250, 200, "external_statement", "txn_id  text  PK\namount  numeric(20,2)\n\n\n외부가 보내 준 정산\n(외부 대사의 상대편)", bg=P["bff_bg"], stroke=P["back"], mono_body=True, body_size=13)
    d.card("t1", 40, 350, 610, 150, "트리거 두 개 (ledger)",
           "ledger_txn_net_zero — AFTER INSERT · DEFERRABLE INITIALLY DEFERRED\n   한 거래의 다리 합이 0 이 아니면 커밋 때 거절한다 (03)\nledger_no_update_delete — BEFORE UPDATE OR DELETE\n   원장을 고치거나 지우지 못하게 한다 (03)",
           bg=P["note_bg"], stroke=P["line"], body_size=14, title_size=16)
    d.card("t2", 680, 350, 580, 150, "읽는 순서",
           "02  account ↔ ledger (잔고 = 원장 합)\n03  트리거 · 제약 (언제 검사하나)\n04  posted_txn (멱등) · 잔고 갱신\n05  external_statement 와 맞춰 본다 (대사)",
           bg=P["note_bg"], stroke=P["line"], body_size=14, title_size=16)
    d.save()


if __name__ == "__main__":
    for f in (intro, ledger_table, balance_is_sum, two_legs, cache, invariants, reversal, schema):
        f()
    finish()
