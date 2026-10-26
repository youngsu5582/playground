#!/usr/bin/env python3
"""01.06 블로그 05 그림 (대사). 실행: python3 -I docs/diagrams/draw_blog05.py (레슨 폴더에서)"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[4] / "tools"))
from diagram import Diagram, P, finish, timeline as _timeline  # noqa: E402

OUT = pathlib.Path(__file__).parent


def timeline(*a, **k):
    return _timeline(*a, out=OUT, **k)


ACCT = [("0", "-94.00"), ("1", "65.00"), ("2", "31.00"), ("6", "7.00"), ("7", "0.00")]
LED = {"0": "-94.00", "1": "60.00", "2": "30.00", "8": "4.00"}


def table(d, x0, y0, rows, heads, widths, hl=()):
    x = x0
    for h, w in zip(heads, widths):
        d.pill(f"h{x0}{h}", x, y0, w, 40, h, P["note_bg"], P["line"], size=13)
        x += w + 8
    for r, row in enumerate(rows):
        x = x0
        bad = r in hl
        for c, (t, w) in enumerate(zip(row, widths)):
            d.pill(f"c{x0}{r}{c}", x, y0 + 48 + r * 48, w, 40, t, P["bad_bg"] if bad else P["white"], P["red"] if bad else P["line"], size=13, mono=True)
            x += w + 8


def intro():
    d = Diagram("blog05-intro", 1240, 540, "도입: 같은 사실을 두 곳에 적어 두면 맞춰 볼 수 있다",
                "계좌별 잔고(account)와 계좌별 원장 합(ledger) — 어긋난 줄을 찾는 것이 내부 대사다", out=OUT)
    rows = [("0", "-94.00", "-94.00", "맞음"), ("1", "65.00", "60.00", "5.00 차이"), ("2", "31.00", "30.00", "1.00 차이"),
            ("6", "7.00", "(원장 없음)", "잔고만 있음"), ("7", "0.00", "(원장 없음)", "맞음 (빈 계좌)"), ("8", "(계좌 없음)", "4.00", "원장만 있음")]
    table(d, 40, 110, rows, ["계좌 id", "account.balance", "ledger 합", "판정"], [140, 260, 260, 260], hl=(1, 2, 3, 5))
    d.card("n", 40, 470, 1160, 56, "어긋난 줄이 넷이다 — 이 쿼리가 어느 줄을 찾아야 하는지가 이 글의 주제다", None, bg=P["note_bg"], stroke=P["line"], title_size=15)
    d.save()


def joins():
    d = Diagram("blog05-joins", 1260, 560, "어떤 JOIN 이 어느 줄을 보나",
                "계좌 {0, 1, 2, 6, 7} 과 원장이 있는 계좌 {0, 1, 2, 8} 을 account_id 로 맞춘다 (문서 7.2.1.1)", out=OUT)
    cols = [("INNER JOIN", "양쪽에 다 있는 줄만", ["0", "1", "2"], P["bad_bg"], P["red"], "6 · 7 · 8 을 못 본다"),
            ("LEFT JOIN (account 기준)", "계좌는 모두 + 원장 없으면 NULL", ["0", "1", "2", "6", "7"], P["rs_bg"], P["orange"], "8 (계좌 없는 원장) 을 못 본다"),
            ("FULL OUTER JOIN", "양쪽 모두 + 없는 쪽은 NULL", ["0", "1", "2", "6", "7", "8"], P["ok_bg"], P["green"], "찾는 줄을 전부 본다")]
    for i, (a, b, ids, bg, st, c) in enumerate(cols):
        x = 40 + i * 410
        d.card(f"j{i}", x, 110, 380, 120, a, b, bg=bg, stroke=st, title_size=16, body_size=14)
        for k, idv in enumerate(ids):
            d.pill(f"i{i}{k}", x + 6 + k * 60, 260, 52, 44, idv, P["white"], st, size=15, mono=True)
        d.text(x + 6, 330, c, 14, st, weight=700)
    d.card("n", 40, 400, 1180, 130, "대사에서는 \"한쪽에만 있는 줄\" 이 바로 찾는 대상이다",
           "INNER JOIN 은 그 줄을 아예 못 본다.  문서(7.2.1.1): FULL OUTER JOIN 은 먼저 inner join 을 하고, T1 의 짝 없는 줄에 T2 열을 NULL 로 채워 추가하고,\n"
           "T2 의 짝 없는 줄에는 T1 열을 NULL 로 채워 추가한다.  그래서 어긋남의 모든 종류가 한 번에 나온다.",
           bg=P["note_bg"], stroke=P["line"], title_size=16)
    d.save()


def result():
    d = Diagram("blog05-result", 1240, 560, "FULL OUTER JOIN 대사 쿼리와 결과",
                "WHERE a.id IS NULL OR a.balance <> COALESCE(l.s, 0)  (실측: psql 2026-10-13, 임시 테이블)", out=OUT)
    d.card("q", 40, 100, 1160, 130, "쿼리",
           "SELECT COALESCE(a.id, l.account_id) AS id, a.balance, l.s\nFROM account a FULL OUTER JOIN (SELECT account_id, sum(amount) s FROM ledger GROUP BY account_id) l\n  ON l.account_id = a.id\nWHERE a.id IS NULL OR a.balance <> COALESCE(l.s, 0) ORDER BY 1",
           bg=P["note_bg"], stroke=P["line"], mono_body=True, body_size=13, title_size=15)
    rows = [("1", "65.00", "60.00", "BALANCE_NOT_MATCH"), ("2", "31.00", "30.00", "BALANCE_NOT_MATCH"),
            ("6", "7.00", "NULL → 0", "BALANCE_NOT_MATCH"), ("8", "NULL (계좌 없음)", "4.00", "LEDGER_WITHOUT_ACCOUNT")]
    table(d, 40, 260, rows, ["id", "balance", "ledger 합", "Mismatch.Kind"], [100, 300, 260, 400], hl=(0, 1, 2, 3))
    d.text(40, 520, "계좌 7 (잔고 0 · 원장 없음) 은 COALESCE(NULL, 0) = 0 이라 결과에 없다 — 빈 계좌는 정상이다", 14, P["muted"])
    d.save()


def null_trap():
    d = Diagram("blog05-null-trap", 1260, 540, "NULL 은 <> 로 비교되지 않는다 — COALESCE 가 필요하다",
                "sum 은 원장이 없으면 NULL (문서 9.21). NULL 과의 비교 결과는 참이 아니라 UNKNOWN 이다", out=OUT)
    d.card("a", 40, 110, 570, 210, "COALESCE 없이",
           "WHERE a.id IS NULL OR a.balance <> l.s\n\n계좌 6:  7.00 <> NULL  →  UNKNOWN  →  행이 걸러진다\n계좌 7:  0.00 <> NULL  →  UNKNOWN  →  걸러진다 (우연히 정상)\n\n결과: 1 · 2 · 8   ← 계좌 6 이 사라졌다",
           bg=P["bad_bg"], stroke=P["red"], body_size=14, mono_body=True)
    d.card("b", 650, 110, 570, 210, "COALESCE(l.s, 0) 와 비교",
           "WHERE a.id IS NULL OR a.balance <> COALESCE(l.s, 0)\n\n계좌 6:  7.00 <> 0  →  참  →  어긋남\n계좌 7:  0.00 <> 0  →  거짓  →  정상 (빈 계좌)\n\n결과: 1 · 2 · 6 · 8",
           bg=P["ok_bg"], stroke=P["green"], body_size=14, mono_body=True)
    d.arrow([(325, 320), (325, 380)], P["red"], "조용히 놓친다")
    d.arrow([(935, 320), (935, 380)], P["green"], "정확하다")
    d.card("c", 40, 390, 570, 130, "대사가 가장 위험한 때는 못 찾았을 때다",
           "빈 결과는 \"이상 없음\" 처럼 보인다.  못 찾는 대사기는 오히려 안심을 준다.", bg=P["note_bg"], stroke=P["line"], title_size=15)
    d.card("d", 650, 390, 570, 130, "실측 (psql 2026-10-13)",
           "COALESCE 를 빼면 계좌 6 이 결과에서 빠졌다.\n문서: sum 은 선택된 행이 없으면 null (coalesce 로 대체).", bg=P["note_bg"], stroke=P["line"], title_size=15, body_size=14)
    d.save()


def external():
    d = Diagram("blog05-external", 1260, 560, "외부 대사: 우리 거래 vs 외부 정산 내역",
                "거래 id 로 FULL OUTER JOIN — 한쪽만 있으면 OURS_ONLY / THEIRS_ONLY, 둘 다 있는데 금액이 다르면 AMOUNT_DIFFERS", out=OUT)
    rows = [("E1", "60.00", "60.00", "맞음"), ("E2", "30.00", "33.00", "AMOUNT_DIFFERS"), ("E3", "4.00", "(없음)", "OURS_ONLY"), ("E7", "(없음)", "12.00", "THEIRS_ONLY")]
    table(d, 40, 110, rows, ["거래 id", "우리 금액 (+ 다리)", "외부 금액", "판정"], [140, 300, 260, 400], hl=(1, 2, 3))
    d.card("n", 40, 370, 1180, 150, "우리 금액 = 그 거래의 + 다리 (Mismatch Javadoc)",
           "원장은 거래당 두 줄(- 다리 · + 다리)이라 거래 id 로 바로 맞추면 한 거래가 두 번 나온다.  그래서 WHERE amount > 0 으로 + 다리만 쓴다.\n"
           "금액은 numeric 으로 비교한다 — float8 이면 같은 금액도 다르다고 나온다 (01).  Mismatch 는 금액을 소수 둘째 자리로 맞춰 0 과 0.00 이 다르게 보이지 않게 한다.",
           bg=P["note_bg"], stroke=P["line"], title_size=16, body_size=14)
    d.save()


def legs_filter():
    d = Diagram("blog05-legs-filter", 1260, 520, "- 다리를 거르지 않으면 같은 거래가 두 줄로 나온다",
                "ledger 를 그대로 external_statement 와 맞추면 (실측: psql 2026-10-13)", out=OUT)
    rows = [("E1", "0", "-60.00", "60.00", "가짜 어긋남"), ("E2", "0", "-30.00", "33.00", "진짜 + 가짜"), ("E2", "2", "30.00", "33.00", "진짜"),
            ("E3", "0", "-4.00", "(없음)", "가짜 + 진짜"), ("E3", "8", "4.00", "(없음)", "진짜")]
    table(d, 40, 110, rows, ["txn", "account", "우리", "외부", "판정"], [120, 140, 200, 200, 300], hl=(0, 1, 3))
    d.card("n", 40, 420, 1180, 80, "WHERE amount > 0",
           "- 다리(차변)는 외부 금액과 부호가 달라 항상 어긋나 보인다. + 다리만 \"우리 거래 금액\" 으로 쓰면 거래당 한 줄이 된다.",
           bg=P["note_bg"], stroke=P["line"], title_size=15)
    d.save()


def snapshot():
    timeline("blog05-snapshot", "대사 쿼리를 둘로 쪼개면 사이에 낀 커밋이 거짓 경보를 만든다",
             "A 는 대사 (잔고를 읽고, 따로 원장 합을 읽는다). B 는 그 사이 이체 T-70 (계좌 11 에서 30 출금) 을 커밋한다",
             [("A", "1  SELECT balance … 계좌 11", "본 값: 100", None),
              ("B", "2  이체 T-70: 잔고 70 · 원장 -30  → COMMIT", "잔고와 원장이 한 트랜잭션으로 같이 커밋", None),
              ("A", "3  SELECT sum(amount) … 계좌 11 의 원장", "본 값: 70  (이체가 반영된 원장)", "bad")],
             [(1, 2, "새 커밋이\n두 번째 읽기에 보인다", 0.5)],
             "A 의 판정: 잔고 100 ≠ 원장 합 70 — 어긋남처럼 보이지만 둘 다 맞는 값이다. 읽은 시점이 달랐을 뿐이다.\n"
             "문서 13.2.1: READ COMMITTED 에서 한 쿼리는 시작 순간의 스냅샷을 보고, 같은 트랜잭션의 연속된 두 SELECT 는 다른 데이터를 볼 수 있다.\n"
             "잔고와 원장을 한 문장에서 읽으면 한 스냅샷을 본다 — 이 레슨의 내부 대사 쿼리가 한 문장인 이유다 (해석).",
             "거짓 경보", level="READ COMMITTED")


def timing():
    d = Diagram("blog05-timing", 1260, 520, "\"우리만 있음\" 이 곧 오류는 아니다 — 시차",
                "외부 정산이 하루 늦게 오는 경우 (일반 개념 · 해석 — 이 레슨의 구현은 시차를 다루지 않는다)", out=OUT)
    d.line([(80, 255), (1180, 255)], P["line"], dashed=False, sw=3)
    for i, (x, t, bg, st) in enumerate([(160, "D 일 23:50\n우리 원장에\nE3 기록", P["as_bg"], P["front"]),
                                         (500, "D+1 일 대사\n외부에 E3 없음\n= OURS_ONLY", P["rs_bg"], P["orange"]),
                                         (840, "D+1 일 늦게\n외부 정산 도착\nE3 가 생김", P["ok_bg"], P["green"]),
                                         (1100, "D+2 일 대사\n맞음", P["ok_bg"], P["green"])]):
        d.pill(f"t{i}", x - 100, 130, 200, 100, t, bg, st, size=13)
    d.card("n", 40, 290, 1180, 200, "그래서 실무 대사는 기간과 허용 지연을 둔다",
           "OURS_ONLY · THEIRS_ONLY 는 \"아직 안 온 것\" 일 수 있다.  정산 주기가 달라서일 수도 있다.\n"
           "정해 둔 시간이 지나도 남는 것만 오류로 올린다.  반대로 AMOUNT_DIFFERS 는 양쪽에 다 있는데 값이 다른 것이라 시차로 설명되지 않는다 (해석).\n"
           "이 레슨의 Reconciler 는 시점과 상관없이 현재 상태의 차이를 전부 돌려준다 — 시차를 걸러내는 일은 호출하는 쪽의 몫이다.",
           bg=P["note_bg"], stroke=P["line"], title_size=16, body_size=14)
    d.save()


def after_find():
    d = Diagram("blog05-after-find", 1280, 540, "찾은 뒤에는 — 그리고 대사는 무엇을 못 찾나",
                "대사는 \"막는 장치\" 를 대신하지 않는다 — 틀렸을 때 사람이 알아채게 하는 마지막 안전망이다", out=OUT)
    for i, (a, b, bg, st) in enumerate([("1  찾는다", "어긋남을 종류별로\n돌려준다 (읽기만 한다)", P["as_bg"], P["front"]),
                                         ("2  원인을 본다", "버그 · 수작업 · 시차 ·\n외부 오류?", P["rs_bg"], P["orange"]),
                                         ("3  정정한다", "원장은 고치지 않고\n반대 거래를 쌓는다 (02)", P["ok_bg"], P["green"]),
                                         ("4  다시 대사", "맞는지 확인한다", P["as_bg"], P["front"])]):
        x = 40 + i * 310
        d.card(f"s{i}", x, 110, 280, 130, a, b, bg=bg, stroke=st, title_size=17, body_size=14)
        if i:
            d.arrow([(x - 30, 175), (x, 175)], P["muted"])
    d.text(40, 270, "방어는 겹으로 쌓는다", 17, P["ink"], weight=700)
    for i, (a, b, bg, st) in enumerate([("제약 · 트리거", "CHECK · 합 0 · append-only\n(03)", P["ok_bg"], P["green"]),
                                         ("원자적 갱신 · 멱등", "balance = balance + ?\n선점 (04)", P["ok_bg"], P["green"]),
                                         ("대사", "막지 못한 것 · 외부와의 차이를\n사람에게 알린다 (05)", P["as_bg"], P["front"])]):
        x = 40 + i * 410
        d.card(f"l{i}", x, 310, 380, 100, a, b, bg=bg, stroke=st, title_size=16, body_size=14)
    d.card("n", 40, 430, 1200, 90, "대사가 못 찾는 것 (해석)",
           "같은 입력으로 두 기록이 함께 틀린 경우 — 예를 들어 잘못된 금액이 원장과 잔고에 똑같이 들어가면 두 곳이 일치해 통과한다.\n"
           "외부 대사는 이런 것을 외부의 기록과 맞춰 잡는 데 도움이 된다.",
           bg=P["note_bg"], stroke=P["line"], title_size=15, body_size=14)
    d.save()


if __name__ == "__main__":
    for f in (intro, joins, result, null_trap, external, legs_filter, snapshot, timing, after_find):
        f()
    finish()
