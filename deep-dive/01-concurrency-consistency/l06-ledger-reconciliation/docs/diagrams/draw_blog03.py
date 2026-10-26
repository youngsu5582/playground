#!/usr/bin/env python3
"""01.06 블로그 03 그림 (규칙은 언제 검사하나). 실행: python3 -I docs/diagrams/draw_blog03.py (레슨 폴더에서)"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[4] / "tools"))
from diagram import Diagram, P, finish, timeline as _timeline  # noqa: E402

OUT = pathlib.Path(__file__).parent


def timeline(*a, **k):
    return _timeline(*a, out=OUT, **k)


def intro():
    d = Diagram("blog03-intro", 1240, 520, "도입: 두 줄을 넣는 사이에는 합이 0 이 아니다",
                "이체 T-50 (계좌 11 → 12, 30.00). 규칙: 한 거래의 다리 합은 0", out=OUT)
    steps = [("문장 1", "INSERT (T-50, 11, -30.00)", "다리 합 = -30.00", P["bad_bg"], P["red"]),
             ("문장 2", "INSERT (T-50, 12, +30.00)", "다리 합 = 0", P["ok_bg"], P["green"]),
             ("COMMIT", "트랜잭션 끝", "최종 상태가 규칙을 지키면 된다", P["as_bg"], P["front"])]
    for i, (a, b, c, bg, st) in enumerate(steps):
        x = 40 + i * 400
        d.card(f"s{i}", x, 120, 360, 130, a, b + "\n" + c, bg=bg, stroke=st, mono_body=False, body_size=15)
        if i:
            d.arrow([(x - 40, 185), (x, 185)], P["muted"])
    d.card("v", 40, 300, 1160, 170, "문장마다 검사하면 첫 문장에서 막힌다",
           "정상적인 이체조차 첫 줄을 넣는 순간 합이 -30 이라 규칙 위반이다.\n"
           "그래서 이런 규칙은 \"문장이 끝날 때마다\" 가 아니라 \"트랜잭션이 끝날 때\" 검사해야 한다 — 지연(deferred) 검사.\n"
           "반대로 한 행만 보고 판단할 수 있는 규칙(잔고 >= 0)은 그 자리에서 바로 검사하는 편이 낫다.  이 글은 둘을 가르는 이야기다.",
           bg=P["note_bg"], stroke=P["line"], title_size=16)
    d.save()


def when():
    d = Diagram("blog03-when", 1280, 480, "검사가 일어나는 자리: 즉시 vs 지연",
                "문서(CREATE TABLE): 지연 불가 제약은 매 명령 직후 검사 · 지연 가능 제약은 INITIALLY DEFERRED 면 트랜잭션 끝에서만 검사", out=OUT)
    xs = [260, 560, 860]
    labels = ["문장 1", "문장 2", "COMMIT"]
    for lane, (name, y, marks, bg, st) in enumerate([
            ("즉시 (NOT DEFERRABLE · INITIALLY IMMEDIATE)", 140, [1, 1, 0], P["as_bg"], P["front"]),
            ("지연 (DEFERRABLE INITIALLY DEFERRED)", 300, [0, 0, 1], P["rs_bg"], P["orange"])]):
        d.text(40, y - 38, name, 16, st, weight=700)
        d.line([(60, y - 6), (1220, y - 6)], P["line"], dashed=False, sw=3)
        for i, x in enumerate(xs):
            d.pill(f"l{lane}{i}", x - 70, y, 140, 44, labels[i], P["white"], P["line"], size=14)
            if marks[i]:
                d.pill(f"m{lane}{i}", x - 70, y + 70, 140, 44, "검사", bg, st, size=15)
            else:
                d.text(x, y + 82, "(검사 안 함)", 13, P["muted"], align="center")
    d.save()


def tools():
    d = Diagram("blog03-tools", 1300, 560, "규칙을 지키는 도구와 검사 시점",
                "PostgreSQL 16 — 지연 가능 여부는 도구마다 정해져 있다 (CREATE TABLE · SET CONSTRAINTS · CREATE TRIGGER 문서)", out=OUT)
    heads = [("도구", 40, 270), ("보는 범위", 320, 250), ("지연 가능?", 580, 330), ("이 레슨에서", 920, 340)]
    for i, (t, x, w) in enumerate(heads):
        d.pill(f"h{i}", x, 100, w, 46, t, P["note_bg"], P["line"], size=14)
    rows = [("CHECK · NOT NULL", "한 행", "불가 — 항상 즉시", "잔고 >= 0 (CHECK)", P["bad_bg"], P["red"]),
            ("UNIQUE · PRIMARY KEY", "인덱스 (행 사이)", "가능 (기본은 NOT DEFERRABLE)", "txn_id PK · UNIQUE (txn_id, account_id)", P["ok_bg"], P["green"]),
            ("FOREIGN KEY · EXCLUDE", "다른 테이블 · 행 사이", "가능 (기본은 NOT DEFERRABLE)", "(이 레슨에서는 쓰지 않는다)", P["white"], P["line"]),
            ("constraint trigger", "원하는 쿼리 (여러 행)", "가능 — AFTER · FOR EACH ROW", "거래의 다리 합 0", P["rs_bg"], P["orange"]),
            ("일반 트리거", "원하는 쿼리", "SET CONSTRAINTS 대상 아님", "BEFORE UPDATE OR DELETE 금지", P["as_bg"], P["front"])]
    for r, (a, b, c, e, bg, st) in enumerate(rows):
        y = 160 + r * 68
        for i, (t, x, w) in enumerate([(a, 40, 270), (b, 320, 250), (c, 580, 330), (e, 920, 340)]):
            d.pill(f"r{r}{i}", x, y, w, 56, t, bg if i == 2 else P["white"], st if i == 2 else P["line"], size=13)
    d.text(40, 510, "근거: CREATE TABLE · SET CONSTRAINTS (UNIQUE · PK · REFERENCES · EXCLUDE 만 지연 가능, NOT NULL · CHECK 는 항상 즉시) · CREATE TRIGGER (constraint trigger 는 AFTER ROW)", 13, P["muted"])
    d.save()


def constraint_trigger():
    d = Diagram("blog03-constraint-trigger", 1300, 560, "지연 제약 트리거가 하는 일",
                "ledger_txn_net_zero — AFTER INSERT · DEFERRABLE INITIALLY DEFERRED · FOR EACH ROW", out=OUT)
    d.pill("a", 40, 130, 260, 70, "INSERT 한 줄", P["as_bg"], P["front"], size=16)
    d.pill("b", 380, 130, 300, 70, "트리거 호출을 큐에 쌓는다", P["rs_bg"], P["orange"], size=15)
    d.pill("c", 760, 130, 220, 70, "COMMIT", P["as_bg"], P["front"], size=16)
    d.pill("e", 1050, 130, 210, 70, "큐의 호출 실행", P["rs_bg"], P["orange"], size=15)
    d.arrow([(300, 165), (380, 165)], P["muted"], "행마다")
    d.arrow([(680, 165), (760, 165)], P["muted"], "나중에")
    d.arrow([(980, 165), (1050, 165)], P["muted"])
    d.card("f", 380, 260, 520, 120, "함수 본문",
           "SELECT sum(amount) FROM ledger\n WHERE txn_id = NEW.txn_id   -- 그 거래의 모든 다리\nIF 합 <> 0 THEN RAISE EXCEPTION …",
           bg=P["white"], stroke=P["line"], mono_body=True, body_size=13)
    d.arrow([(1150, 200), (1150, 320), (900, 320)], P["muted"], "실행")
    d.pill("ok", 960, 410, 300, 60, "합 = 0  →  커밋 완료", P["ok_bg"], P["green"], size=15)
    d.pill("ng", 960, 490, 300, 60, "합 ≠ 0  →  에러 · 전체 롤백", P["bad_bg"], P["red"], size=15)
    d.card("n", 40, 260, 300, 290, "조건 (CREATE TRIGGER)",
           "AFTER 만\nFOR EACH ROW 만\n일반 테이블에서만\nDEFERRABLE · INITIALLY 는\nconstraint trigger 에서만\n\n위반 시 예외를 던질 책임은\n함수에 있다",
           bg=P["note_bg"], stroke=P["line"], body_size=14, title_size=16)
    d.save()


def fail_timeline():
    timeline("blog03-fail-timeline", "지연 제약은 COMMIT 에서 터진다 (거래 X3 — 다리 합이 맞지 않는 두 줄)",
             "A 가 합이 1.00 인 두 줄을 넣는다. B 는 같은 거래를 조회한다",
             [("A", "1  INSERT (X3, 계좌 1, +50.00)", "검사 안 함", None),
              ("B", "2  SELECT count(*) WHERE txn_id = 'X3'", "본 값: 0  (A 가 커밋 전이라 안 보인다)", None),
              ("A", "3  INSERT (X3, 계좌 0, -49.00)", "합 1.00 이지만 검사 안 함", None),
              ("A", "4  COMMIT", "에러 — 규칙 위반 · 트랜잭션 전체 롤백", "bad")],
             [(0, 1, "커밋 전 줄은\n안 보인다", 0.5)],
             "두 INSERT 모두 성공했는데 COMMIT 이 실패했다. 에러는 규칙을 어긴 줄이 아니라 커밋 지점에서 난다.\n"
             "실패한 커밋은 롤백이라 두 줄 모두 사라진다 (실측: psql 2026-10-13).",
             "문장은 통과, 커밋이 거절", level="READ COMMITTED")


def set_constraints():
    d = Diagram("blog03-set-constraints", 1280, 520, "SET CONSTRAINTS 로 검사 자리를 옮긴다",
                "문서(SET CONSTRAINTS): DEFERRED 를 IMMEDIATE 로 바꾸면 쌓인 검사를 그 자리에서 한다 (retroactively) · constraint trigger 도 같은 설정을 따른다", out=OUT)
    xs = [220, 520, 820, 1100]
    labels = ["BEGIN", "INSERT", "SET CONSTRAINTS\nALL IMMEDIATE", "COMMIT"]
    for lane, (name, y, mark, bg, st) in enumerate([
            ("기본 (INITIALLY DEFERRED)", 130, 3, P["rs_bg"], P["orange"]),
            ("SET CONSTRAINTS ALL IMMEDIATE 를 중간에 실행", 300, 2, P["as_bg"], P["front"])]):
        d.text(40, y - 38, name, 16, st, weight=700)
        d.line([(60, y - 6), (1240, y - 6)], P["line"], dashed=False, sw=3)
        for i, x in enumerate(xs):
            d.pill(f"l{lane}{i}", x - 90, y, 180, 56, labels[i], P["white"], P["line"], size=13)
        d.pill(f"m{lane}", xs[mark] - 70, y + 80, 140, 44, "검사", bg, st, size=15)
        d.arrow([(xs[mark], y + 56), (xs[mark], y + 80)], st)
    d.text(40, 470, "설정은 현재 트랜잭션 안에서만 유효하다 (문서). 지연 불가 제약(CHECK 등)은 이름을 줘서 DEFERRED 로 바꾸려 하면 에러 — 실측: constraint \"account_check\" is not deferrable", 13, P["muted"])
    d.save()


def deferral_cost():
    d = Diagram("blog03-deferral-cost", 1260, 500, "지연의 대가: 에러가 난 자리와 원인 문장이 떨어진다",
                "즉시 검사는 에러 문장 = 원인 문장 · 지연 검사는 COMMIT 에서 알려 준다", out=OUT)
    d.card("a", 40, 110, 570, 200, "즉시 (CHECK 잔고 >= 0)",
           "UPDATE account SET balance = balance - 5000 …\n→ 이 문장에서 에러 (실측: 위반 메시지에\n   새 행 내용 · 제약 이름이 나온다)\n→ 어디가 문제인지 바로 안다",
           bg=P["ok_bg"], stroke=P["green"], body_size=14)
    d.card("b", 650, 110, 570, 200, "지연 (거래 합 0 트리거)",
           "INSERT … · INSERT … · COMMIT\n→ COMMIT 에서 에러\n→ 메시지: \"거래 X3 의 다리 합이 0 이 아니다: 1.00\"\n→ 어느 문장이 원인인지는 앱이 찾아야 한다 (해석)",
           bg=P["bad_bg"], stroke=P["red"], body_size=14)
    d.card("c", 40, 350, 1180, 120, "앱이 해야 할 것",
           "지연 제약을 쓰면 COMMIT 호출도 실패할 수 있다 — commit 의 예외까지 처리해야 한다 (일반 개념 · 해석).\n"
           "원인 문장을 바로 보고 싶으면 SET CONSTRAINTS … IMMEDIATE 로 그 자리에서 검사한다.",
           bg=P["note_bg"], stroke=P["line"], title_size=16)
    d.save()


def append_only():
    d = Diagram("blog03-append-only", 1260, 520, "행 트리거는 어떤 문장에서 불리나",
                "CREATE TRIGGER 문서: TRUNCATE 는 문장 트리거(FOR EACH STATEMENT)만 가능 · TRUNCATE 문서: ON DELETE 트리거를 부르지 않는다", out=OUT)
    heads = ["문장", "행 트리거 (BEFORE UPDATE OR DELETE)", "문장 트리거 (BEFORE TRUNCATE)"]
    xs = [(40, 260), (310, 480), (800, 420)]
    for i, h in enumerate(heads):
        d.pill(f"h{i}", xs[i][0], 100, xs[i][1], 46, h, P["note_bg"], P["line"], size=13)
    rows = [("UPDATE", "불린다", "해당 없음"), ("DELETE", "불린다", "해당 없음"), ("TRUNCATE", "불리지 않는다", "불린다 (만들어 두면)")]
    for r, row in enumerate(rows):
        y = 160 + r * 70
        for i, t in enumerate(row):
            bad = t.startswith("불리지")
            ok = t.startswith("불린다")
            d.pill(f"r{r}{i}", xs[i][0], y, xs[i][1], 56, t, P["bad_bg"] if bad else (P["ok_bg"] if ok and i else P["white"]), P["red"] if bad else (P["green"] if ok and i else P["line"]), size=14)
    d.card("n", 40, 390, 1180, 100, "그래서",
           "행 트리거만으로는 \"쌓기만 한다\" 를 지킬 수 없다.  막으려면 TRUNCATE 용 문장 트리거를 따로 달고(실측: 에러로 막힘),\n"
           "테이블 소유자가 ALTER TABLE … DISABLE TRIGGER 로 트리거를 끌 수 있으니 권한도 나눈다 (해석).",
           bg=P["note_bg"], stroke=P["line"], title_size=16)
    d.save()


def unique_flow():
    d = Diagram("blog03-unique-flow", 1260, 480, "INSERT … ON CONFLICT DO NOTHING 이 하는 일",
                "문서(INSERT): 충돌한 행은 넣지 않고 건너뛴다 · 결과의 count 는 실제로 삽입된(갱신된) 행 수 · 지연 가능한 제약은 arbiter 가 될 수 없다", out=OUT)
    d.pill("a", 40, 150, 300, 70, "INSERT posted_txn (txn_id)\nON CONFLICT DO NOTHING", P["as_bg"], P["front"], size=14, mono=True)
    d.pill("q", 440, 160, 260, 56, "같은 txn_id 가 있나?", P["note_bg"], P["line"], size=15)
    d.arrow([(340, 185), (440, 185)], P["muted"])
    d.pill("n", 840, 110, 380, 60, "없다 → 삽입 → count = 삽입된 행 수", P["ok_bg"], P["green"], size=14)
    d.pill("y", 840, 230, 380, 60, "있다 → 건너뜀 → 에러 없이 끝", P["rs_bg"], P["orange"], size=14)
    d.arrow([(700, 175), (840, 140)], P["green"], "아니오", label_at=(770, 140))
    d.arrow([(700, 200), (840, 260)], P["orange"], "예", label_at=(770, 250))
    d.card("c", 40, 340, 1180, 110, "ON CONFLICT 없이 INSERT 하면",
           "충돌은 제약 위반 에러가 된다. ON CONFLICT 는 \"충돌 = 에러\" 를 \"충돌 = 이미 처리됨\" 으로 바꿔 준다 (01.03 과 연결).\n"
           "이 레슨은 거래 id 선점(posted_txn)을 이 문장으로 하고, ledger 의 UNIQUE(txn_id, account_id)는 뒤의 안전망이다.",
           bg=P["note_bg"], stroke=P["line"], title_size=16)
    d.save()


def summary():
    d = Diagram("blog03-summary", 1300, 520, "이 레슨의 규칙 다섯 개와 검사 시점",
                "ledger-schema.sql", out=OUT)
    heads = [("규칙", 40, 360), ("도구", 410, 360), ("검사 시점", 780, 240), ("실패하면", 1030, 240)]
    for i, (t, x, w) in enumerate(heads):
        d.pill(f"h{i}", x, 100, w, 46, t, P["note_bg"], P["line"], size=14)
    rows = [("잔고는 0 이상 (시스템 계정 제외)", "CHECK (balance >= 0 OR id = 0)", "문장 · 즉시", "그 문장에서 에러"),
            ("한 거래의 다리 합 = 0", "constraint trigger", "커밋 · 지연", "COMMIT 에서 에러"),
            ("원장은 고치거나 지우지 않는다", "BEFORE UPDATE OR DELETE 행 트리거", "문장 · 즉시", "그 문장에서 에러"),
            ("같은 거래 id 는 한 번만", "posted_txn PK · ON CONFLICT", "문장 · 즉시", "건너뜀 또는 에러"),
            ("한 거래는 계좌마다 한 줄", "UNIQUE (txn_id, account_id)", "문장 · 즉시", "그 문장에서 에러")]
    for r, row in enumerate(rows):
        y = 160 + r * 66
        for i, (t, (_, x, w)) in enumerate(zip(row, heads)):
            hl = (r == 1 and i in (2, 3))
            d.pill(f"r{r}{i}", x, y, w, 54, t, P["rs_bg"] if hl else P["white"], P["orange"] if hl else P["line"], size=13)
    d.save()


if __name__ == "__main__":
    for f in (intro, when, tools, constraint_trigger, fail_timeline, set_constraints, deferral_cost, append_only, unique_flow, summary):
        f()
    finish()
