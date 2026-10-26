#!/usr/bin/env python3
"""01.02 블로그판 04 그림. 실행: python3 -I docs/diagrams/draw_blog04.py (레슨 폴더에서)"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[4] / "tools"))
from diagram import Diagram, P, finish  # noqa: E402

OUT = pathlib.Path(__file__).parent


def intro():
    d = Diagram("blog04-intro", 1400, 520, "자식 INSERT 한 줄이 부모 행에 남기는 흔적",
                "자식이 부모를 \"읽기만\" 하는 것처럼 보이지만, 부모 행에 락 표시가 남는다", out=OUT)
    d.card("a", 40, 130, 340, 190, "세션 A", "BEGIN;\nINSERT INTO order_items\n  (order_id) VALUES (5);\n\n(커밋은 아직)",
           bg=P["as_bg"], stroke=P["front"], title_size=17, body_size=14, mono_body=True)
    d.card("ri", 520, 110, 380, 230, "외래키 검사 (RI 트리거)",
           "부모가 존재하는지 확인하는 쿼리:\n\nSELECT 1 FROM ONLY orders x\n WHERE id = 5\n   FOR KEY SHARE OF x",
           bg=P["note_bg"], stroke=P["line"], title_size=16, body_size=14, mono_body=True)
    d.card("p", 1020, 130, 340, 190, "부모 orders 의 id = 5 행",
           "UPDATE 도 안 했는데\n튜플에 락 표시가 남는다\n= FOR KEY SHARE (가장 약한 행 락)",
           bg=P["todo_bg"], stroke=P["orange"], title_size=16, body_size=14)
    d.arrow([d.anchor("a", "e"), d.anchor("ri", "w")], P["muted"], "자식 INSERT", start="a", end="ri")
    d.arrow([d.anchor("ri", "e"), d.anchor("p", "w")], P["orange"], "부모 행 잠금", start="ri", end="p")
    d.card("n", 40, 380, 1320, 100, "그래서 이 글의 질문",
           "부모 행이 이미 FOR KEY SHARE 로 잠겨 있을 때, 부모에 오는 UPDATE · DELETE 는 어떻게 되나?\n"
           "답은 락 모드의 충돌표(01 글)에서 나온다 — 부모의 키를 건드리느냐가 갈림길이다",
           bg=P["as_bg"], stroke=P["front"], title_size=16, body_size=14)
    d.save()


def why_two():
    d = Diagram("blog04-why-two-modes", 1400, 520, "왜 \"가장 약한\" 락이면 되나 — 키만 지키면 된다",
                "위 문장은 모드 정의에서 이은 해석이다. 두 모드를 둔 도입 이유를 문서가 따로 적은 것은 찾지 못했다 (해석)", out=OUT)
    d.card("need", 40, 130, 440, 250, "자식이 필요한 보장",
           "자식 행을 넣는 동안\n부모가 존재해야 하고\n지워지지 않아야 한다\n\n= 부모의 키가 안 바뀌고\n  안 지워지면 안전하다",
           bg=P["as_bg"], stroke=P["front"], title_size=17, body_size=15)
    d.card("ks", 560, 130, 380, 250, "FOR KEY SHARE",
           "\"이 행의 키가 안 바뀌고\n안 지워지게\" 만 지킨다\n\nFOR UPDATE 하고만 충돌한다\n\n외래키 검사가 쓴다",
           bg=P["ok_bg"], stroke=P["green"], title_size=17, body_size=15)
    d.card("nk", 980, 130, 380, 250, "FOR NO KEY UPDATE",
           "키가 아닌 열을 바꾸는\nUPDATE 가 잡는다\n\nFOR KEY SHARE 와\n충돌하지 않는다",
           bg=P["todo_bg"], stroke=P["orange"], title_size=17, body_size=15)
    d.arrow([d.anchor("need", "e"), d.anchor("ks", "w")], P["muted"], "충분하다", start="need", end="ks")
    d.card("n", 40, 410, 1320, 80, "부모를 FOR UPDATE(가장 강함)로 잠그면 부모의 어떤 UPDATE 도 막히지만, 그럴 필요는 없다",
           None, bg=P["note_bg"], stroke=P["line"], title_size=15)
    d.save()


def ri_source():
    d = Diagram("blog04-ri-source", 1400, 540, "외래키 검사가 FOR KEY SHARE 를 쓴다는 소스 근거",
                "ri_triggers.c (PostgreSQL 16) — 세 함수가 같은 절을 만든다", out=OUT)
    fns = [("RI_FKey_check", "자식 INSERT · 참조 열 UPDATE 때\n부모를 조회한다"),
           ("ri_Check_Pk_Match", "부모 테이블을 재확인한다"),
           ("ri_restrict", "RESTRICT · NO ACTION 일 때\n자식 테이블을 조회한다")]
    for i, (n, t) in enumerate(fns):
        d.card(f"f{i}", 40, 120 + i * 120, 480, 100, n, t, bg=P["as_bg"], stroke=P["front"], title_size=16, body_size=14)
    d.card("sql", 640, 160, 720, 160, "만들어지는 쿼리",
           "SELECT 1 FROM ONLY <pktable> x\n WHERE … FOR KEY SHARE OF x",
           bg=P["todo_bg"], stroke=P["orange"], title_size=16, body_size=15, mono_body=True)
    for i in range(3):
        d.arrow([d.anchor(f"f{i}", "e"), d.anchor("sql", "w", 0.25 + 0.25 * i)], P["muted"])
    d.card("cm", 640, 350, 720, 110, "소스 주석",
           "\"pk_rel is opened in RowShareLock mode since that's what\nour eventual SELECT FOR KEY SHARE will get on it\"",
           bg=P["note_bg"], stroke=P["line"], title_size=15, body_size=14)
    d.text(40, 490, "문서의 외래키 절(ddl-constraints)에는 락 얘기가 없다. 근거는 소스와 실측이다", 14, P["muted"])
    d.save()


def parent_side():
    d = Diagram("blog04-parent-side", 1400, 460, "부모에 오는 연산은 자식 INSERT 와 부딪히나 (표 13.3)",
                "A 의 자식 INSERT 가 부모 행에 FOR KEY SHARE 를 쥐고 있을 때", out=OUT)
    d.pill("h0", 40, 100, 440, 44, "부모에 대한 연산", P["note_bg"], P["line"], size=14)
    d.pill("h1", 490, 100, 330, 44, "필요한 락", P["note_bg"], P["line"], size=14)
    d.pill("h2", 830, 100, 530, 44, "A 의 자식 INSERT(FOR KEY SHARE)와", P["note_bg"], P["line"], size=14)
    rows = [("키가 아닌 열 UPDATE", "FOR NO KEY UPDATE", "충돌 없음", P["ok_bg"], P["green"]),
            ("DELETE · 키 열 UPDATE", "FOR UPDATE", "충돌 — 기다린다", P["bad_bg"], P["red"]),
            ("다른 자식 INSERT", "FOR KEY SHARE", "충돌 없음", P["ok_bg"], P["green"])]
    for i, (a, b, c, bg, st) in enumerate(rows):
        y = 156 + i * 80
        d.pill(f"a{i}", 40, y, 440, 68, a, P["white"], P["line"], size=15)
        d.pill(f"b{i}", 490, y, 330, 68, b, P["white"], P["line"], size=14)
        d.pill(f"c{i}", 830, y, 530, 68, c, bg, st, size=16)
    d.text(40, 420, "첫 줄은 실측으로 확인, 나머지는 표 13.3 에서 읽은 것", 14, P["muted"])
    d.save()


def tuple_flags():
    d = Diagram("blog04-tuple-flags", 1400, 540, "자식 INSERT 중인 부모 튜플을 들여다보면 (실측: psql 2026-10-13)",
                "세션 A: BEGIN; INSERT INTO child VALUES (1, 1);  후 열어 둠 (부모 id = 1 을 참조)", out=OUT)
    d.card("t", 40, 120, 640, 250, "부모 튜플 헤더 (pageinspect)",
           "t_xmax      = A 의 트랜잭션 ID\nHEAP_XMAX_LOCK_ONLY   켜짐\nHEAP_XMAX_IS_MULTI    꺼짐\nHEAP_XMAX_KEYSHR_LOCK 켜짐\n\nUPDATE 도 안 했는데 부모 행의 xmax 에 A 가 적혔다",
           bg=P["todo_bg"], stroke=P["orange"], title_size=16, body_size=14, mono_body=True)
    d.card("l", 720, 120, 640, 120, "pg_locks 의 테이블 락",
           "부모: RowShareLock    자식: RowExclusiveLock\n(ROW SHARE = SELECT FOR … 가 잡는 테이블 락, ROW EXCLUSIVE = INSERT)",
           bg=P["note_bg"], stroke=P["line"], title_size=15, body_size=14)
    d.card("u", 720, 260, 640, 110, "다른 세션의 UPDATE parent SET name = 'y' WHERE id = 1",
           "(키 아님) → 기다리지 않고 UPDATE 1",
           bg=P["ok_bg"], stroke=P["green"], title_size=14, body_size=15)
    d.card("n", 40, 400, 1320, 100, "즉시 알 수 있는 것",
           "자식 INSERT 는 부모를 읽기만 했는데도 부모 행에 락 표시를 남긴다 (디스크 쓰기, 01 글)\n비트 이름은 소스 헤더(htup_details.h)의 이름이다",
           bg=P["as_bg"], stroke=P["front"], title_size=15, body_size=14)
    d.save()


def many_children():
    d = Diagram("blog04-many-children", 1400, 520, "인기 있는 부모 하나에 자식 INSERT 가 몰려도 서로 줄 서지 않는다",
                "FOR KEY SHARE 끼리는 충돌하지 않는다 (표 13.3)", out=OUT)
    for i in range(3):
        d.card(f"c{i}", 40, 120 + i * 110, 420, 90, f"세션 {i + 1}", f"INSERT INTO order_items (order_id) VALUES (5)",
               bg=P["as_bg"], stroke=P["front"], title_size=15, body_size=13, mono_body=True)
    d.card("p", 760, 170, 600, 190, "부모 orders 의 id = 5 행",
           "FOR KEY SHARE 가 여럿 겹쳐 있다\n서로 기다리지 않는다\n\n여러 트랜잭션이 같은 부모를 동시에 KEY SHARE 하면 MultiXact 가 쓰인다\n(해석 — FK 경로의 MultiXact 사용은 실측하지 않았다)",
           bg=P["todo_bg"], stroke=P["orange"], title_size=16, body_size=14)
    for i in range(3):
        d.arrow([d.anchor(f"c{i}", "e"), d.anchor("p", "w", 0.25 + 0.25 * i)], P["green"], "KEY SHARE" if i == 1 else None, start=f"c{i}")
    d.save()


def child_index():
    d = Diagram("blog04-child-index", 1400, 560, "부모 DELETE 는 자식에서 일치하는 행을 찾아야 한다",
                "문서는 참조하는(자식) 열에 인덱스를 두는 것이 대개 좋다고 쓴다. 외래키 선언이 자식 인덱스를 자동으로 만들지는 않는다", out=OUT)
    d.card("del", 40, 150, 360, 130, "부모 DELETE · 참조 열 UPDATE", "자식에 이 부모를 가리키는 행이\n남아 있는지 확인해야 한다",
           bg=P["as_bg"], stroke=P["front"], title_size=15, body_size=14)
    d.card("no", 540, 120, 380, 150, "자식 열에 인덱스가 없으면",
           "자식 테이블 전체 스캔\n(자식이 수억 행이면 오래 걸린다)",
           bg=P["bad_bg"], stroke=P["red"], title_size=15, body_size=14)
    d.card("yes", 540, 300, 380, 150, "자식 열에 인덱스가 있으면",
           "인덱스 스캔으로\n일치하는 행만 찾는다",
           bg=P["ok_bg"], stroke=P["green"], title_size=15, body_size=14)
    d.arrow([d.anchor("del", "e", 0.3), d.anchor("no", "w")], P["red"], start="del", end="no")
    d.arrow([d.anchor("del", "e", 0.7), d.anchor("yes", "w")], P["green"], start="del", end="yes")
    d.card("lock", 980, 120, 380, 330, "락 관점의 부작용 (해석)",
           "스캔이 오래 걸리는 동안\n부모 행에 건 락과 트랜잭션도\n길어질 수 있다\n\n이 레슨에서 시간은\n측정하지 않았다",
           bg=P["todo_bg"], stroke=P["orange"], title_size=15, body_size=14)
    d.save()


if __name__ == "__main__":
    for f in (intro, why_two, ri_source, parent_side, tuple_flags, many_children, child_index):
        f()
    finish()
