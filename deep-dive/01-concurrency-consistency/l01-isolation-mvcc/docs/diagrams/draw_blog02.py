#!/usr/bin/env python3
"""01.01 블로그판 02 그림. 실행: python3 -I docs/diagrams/draw_blog02.py (레슨 폴더에서)"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[4] / "tools"))
from diagram import Diagram, P, finish, timeline as _timeline  # noqa: E402

OUT = pathlib.Path(__file__).parent


def timeline(*a, **k):
    return _timeline(*a, out=OUT, **k)


def intro():
    timeline("blog02-intro", "도입: A 가 고치는 중에 B 가 같은 행을 읽는다",
             "재고 40 인 행 (id = 7). A 는 35 로 고치는 중이고 아직 COMMIT 하지 않았다",
             [("A", "1  UPDATE stock = 35 WHERE id = 7", "아직 COMMIT 하지 않았다 (원래 40)", None),
              ("B", "2  SELECT stock WHERE id = 7", "본 값: 40 — A 를 기다리지 않는다", "ok")],
             [(0, 1, "A 의 쓰기가 B 의\n읽기를 막지 않는다")],
             "A 는 40 을 지우고 35 를 쓴 것이 아니다. 행에 버전이 둘 있고, B 는 A 가 커밋하기 전의 버전을 본다.\n"
             "이 글은 그 \"버전\" 이 디스크에서 무엇인지 — 튜플 헤더의 xmin · xmax · ctid — 를 따라가며 설명한다.",
             "읽는 쪽은 기다리지 않고 옛 값을 본다", vcolor="ok")


def update_chain():
    d = Diagram("blog02-update-chain", 1300, 600, "UPDATE 한 문장이 하는 일 세 가지",
                "재고 40 인 행을 트랜잭션 205 가 35 로 바꾼다 (트랜잭션 ID · 위치는 설명용 숫자)", out=OUT)
    d.card("b", 40, 120, 300, 130, "UPDATE 전: 튜플 하나",
           "위치 (0,1)\nxmin = 200   xmax = 0\nstock = 40",
           bg=P["ok_bg"], stroke=P["green"], body_size=15, mono_body=True)
    d.card("o", 500, 120, 320, 130, "옛 튜플 — 지워지지 않는다",
           "위치 (0,1)\nxmin = 200   xmax = 205\nt_ctid = (0,2)   stock = 40",
           bg=P["bad_bg"], stroke=P["red"], body_size=14, mono_body=True)
    d.arrow([d.anchor("b", "e"), d.anchor("o", "w")], P["muted"], "트랜잭션 205\n가 UPDATE", start="b", end="o", label_size=13)
    d.card("n", 980, 120, 300, 130, "새 튜플",
           "위치 (0,2)\nxmin = 205   xmax = 0\nt_ctid = (0,2)   stock = 35",
           bg=P["ok_bg"], stroke=P["green"], body_size=14, mono_body=True)
    d.arrow([d.anchor("o", "e"), d.anchor("n", "w")], P["front"], "t_ctid 가\n새 것을 가리킨다", start="o", end="n")
    steps = [("1  새 튜플을 만든다", "새 xmin (205), 새 위치 (0,2)"),
             ("2  옛 튜플의 xmax 에 적는다", "지운 트랜잭션 = 205"),
             ("3  옛 튜플의 t_ctid 를 잇는다", "옛 것 -> 새 것 : 버전의 사슬")]
    for i, (t, s) in enumerate(steps):
        d.card(f"st{i}", 40 + i * 420, 320, 400, 90, t, s, bg=P["as_bg"], stroke=P["front"], title_size=16, body_size=14)
    d.card("note", 40, 450, 1220, 110, "결과: 같은 논리 행의 버전이 둘이다",
           "옛 튜플은 xmax 만 채워진 채 그 자리에 남는다. 205 가 커밋하기 전에 읽는 쪽은 옛 튜플을, 커밋한 뒤에 읽는 쪽은 새 튜플을 고른다.\n"
           "누가 어느 쪽을 보는지의 판정은 다음 글(03)이고, 아무도 못 보게 된 옛 튜플을 치우는 것은 VACUUM(06)이다.",
           bg=P["note_bg"], stroke=P["line"], title_size=15, body_size=14)
    d.save()


def tuple_header():
    d = Diagram("blog02-tuple-header", 1400, 570, "튜플 헤더 — 판정에 쓰이는 필드와 페이지 안의 배치",
                "힙(테이블 파일)은 보통 8 kB 페이지로 나뉘고, 한 버전이 곧 페이지 안의 튜플 하나다", out=OUT)
    d.rect("page", 40, 110, 640, 260, P["br_bg"], P["muted"])
    d.text(60, 122, "힙 페이지 (보통 8 kB)", 15, P["muted"], weight=700)
    for i in range(3):
        d.pill(f"lp{i}", 60 + i * 76, 160, 66, 44, f"항목 {i + 1}", P["as_bg"], P["front"], size=13)
    d.text(60, 214, "항목 식별자(line pointer) 배열\n앞에서 자란다 ->", 13, P["front"])
    d.pill("free", 290, 160, 120, 44, "빈 공간", P["white"], P["line"], size=13)
    for i in range(3):
        d.card(f"tp{i}", 420 + i * 86, 150, 80, 190, f"튜플 {3 - i}", None, bg=P["ok_bg"], stroke=P["green"],
               title_size=13, align="center")
    d.text(420, 346, "<- 튜플은 뒤에서 자란다", 13, P["green"])
    d.card("hd", 40, 400, 640, 130, "항목 식별자가 튜플의 위치를 가리킨다",
           "ctid = (페이지 번호, 페이지 안 항목 번호)\n"
           "식별자는 해제되기 전에는 옮겨지지 않는다 (문서 73.6)\n"
           "고정 헤더는 대부분의 머신에서 23바이트",
           bg=P["note_bg"], stroke=P["line"], title_size=15, body_size=14)
    rows = [("t_xmin  (xmin)", "이 버전을 만든 트랜잭션 ID"),
            ("t_xmax  (xmax)", "이 버전을 지운 트랜잭션 ID, 안 지워졌으면 0"),
            ("t_ctid  (ctid)", "이 버전 또는 더 새 버전의 위치"),
            ("t_infomask 등", "여러 플래그 비트 (hint bit 이 여기 있다)")]
    for i, (a, b) in enumerate(rows):
        y = 110 + i * 70
        d.pill(f"f{i}", 730, y, 200, 56, a, P["as_bg"], P["front"], size=15, mono=True)
        d.pill(f"fv{i}", 940, y, 420, 56, b, P["white"], P["line"], size=14)
    d.card("xact", 730, 410, 630, 130, "커밋했는지는 튜플이 아니라 pg_xact 에 있다",
           "pg_xact = 트랜잭션 커밋 상태 데이터를 담는 하위 디렉터리 (문서 73.1)\n"
           "튜플의 xmin 이 가리키는 트랜잭션이 커밋했는지는\n이 기록으로 확인한다 (판정 흐름은 다음 글)",
           bg=P["todo_bg"], stroke=P["orange"], title_size=15, body_size=14)
    d.save()


def xmax_nonzero():
    d = Diagram("blog02-xmax-nonzero", 1400, 440, "xmax 가 0 이 아닌데도 보이는 버전",
                "xmax 가 0 이 아니다 != 지워진 행이다 (문서 5.5)", out=OUT)
    cs = [("지운 트랜잭션이 아직 커밋 전", "xmax = 다른 세션의 UPDATE 중인 트랜잭션 ID\n그 삭제는 아직 없는 일이다\n-> 옛 버전이 그대로 보인다", P["ok_bg"], P["green"]),
          ("삭제 시도가 롤백됐다", "xmax = 롤백한 트랜잭션 ID\n그 삭제는 성립하지 않았다\n-> 옛 버전이 계속 보인다", P["ok_bg"], P["green"]),
          ("행 락 표시", "xmax 는 삭제자 외에 잠금자도 나타낸다\nSELECT ... FOR UPDATE 가 xmax 에 적힌다\n(다음 글 04 에서 실측)", P["as_bg"], P["front"])]
    for i, (t, b, bg, st) in enumerate(cs):
        d.card(f"c{i}", 40 + i * 450, 120, 420, 140, t, b, bg=bg, stroke=st, title_size=16, body_size=14)
    d.card("v", 40, 300, 1320, 100, "읽는 쪽의 질문은 \"xmax 가 있나\" 가 아니라 \"xmax 의 트랜잭션이 내 기준으로 끝나 커밋했나\" 다",
           "실측: 다른 세션이 UPDATE 중일 때 읽은 쪽은 xmax = 그 트랜잭션 ID 인 옛 버전을 기다림 없이 읽었다\n"
           "판정 규칙의 전체는 다음 글(03)에서 다룬다",
           bg=P["note_bg"], stroke=P["line"], title_size=15, body_size=14)
    d.save()


def rollback():
    d = Diagram("blog02-rollback", 1400, 400, "롤백해도 튜플은 남는다",
                "트랜잭션 740 이 UPDATE 한 뒤 롤백했다 (실측 숫자: psql 2026-10-13). 이전 시도들이 남긴 버전도 같은 페이지에 있었다", out=OUT)
    d.card("o", 40, 120, 600, 110, "옛 버전  (0,4)  xmin = 739  xmax = 740",
           "740 은 커밋하지 않았으므로 \"지운다\" 가 성립하지 않는다\n-> 옛 버전이 계속 보인다 (롤백 뒤 SELECT 에서 확인)",
           bg=P["ok_bg"], stroke=P["green"], title_size=15, body_size=14)
    d.card("n", 760, 120, 600, 110, "새 버전  (0,5)  xmin = 740",
           "만든 트랜잭션이 중단됨 — 아무도 볼 수 없다\n그래도 즉시 사라지지 않는다 (\"중단된 트랜잭션이 만들었다\" 로만 취급)",
           bg=P["bad_bg"], stroke=P["red"], title_size=15, body_size=14)
    d.arrow([d.anchor("o", "e"), d.anchor("n", "w")], P["muted"], "t_ctid", start="o", end="n")
    d.card("vac", 40, 280, 1320, 80, "둘 다 나중에 VACUUM 이 정리한다 (06)",
           "롤백은 \"되돌리기\" 가 아니라 \"이 트랜잭션은 중단됐다\" 는 기록이다 — 치우는 일은 따로 한다",
           bg=P["todo_bg"], stroke=P["orange"], title_size=16, body_size=14)
    d.save()


def hintbit():
    d = Diagram("blog02-hintbit", 1400, 520, "SELECT 가 튜플 헤더의 플래그를 바꾼다",
                "롤백된 A(740) 의 버전들 — t_infomask 읽기 전과 읽은 뒤 (실측: psql 2026-10-13, heap_page_items)", out=OUT)
    d.pill("h0", 40, 110, 360, 46, "튜플", P["note_bg"], P["line"], size=14)
    d.pill("h1", 420, 110, 280, 46, "읽기 전", P["note_bg"], P["line"], size=14)
    d.pill("h2", 960, 110, 400, 46, "읽은 뒤", P["note_bg"], P["line"], size=14)
    rows = [("롤백된 A 가 만든 새 버전\nxmin 740 / xmax 0", "0x2800\n(XMAX_INVALID)", "0x2a00\nXMIN_INVALID 비트가 추가됨"),
            ("롤백된 A 가 지우려던 옛 버전\nxmin 739 / xmax 740", "0x2100\n(XMIN_COMMITTED)", "0x2900\nA 롤백 뒤 B 가 SELECT 한 뒤\nXMAX_INVALID 비트가 추가됨")]
    for i, (a, b, c) in enumerate(rows):
        y = 176 + i * 120
        d.pill(f"r{i}a", 40, y, 360, 100, a, P["as_bg"], P["front"], size=14)
        d.pill(f"r{i}b", 420, y, 280, 100, b, P["white"], P["line"], size=14, mono=True)
        d.pill(f"r{i}c", 960, y, 400, 100, c, P["ok_bg"], P["green"], size=14)
        d.arrow([(700, y + 50), (960, y + 50)], P["green"], "읽기 문장이\n플래그를 갱신", label_size=12)
    d.card("n", 40, 420, 1320, 80, "앞자리 0x2000 은 \"UPDATE 로 만든 버전\" 비트 (HEAP_UPDATED)",
           "커밋 상태의 단일 출처는 pg_xact 이고, 튜플의 플래그는 그 결과를 적어 둔 것이다", bg=P["note_bg"], stroke=P["line"],
           title_size=14, body_size=14)
    d.save()


def hot():
    d = Diagram("blog02-hot", 1400, 680, "일반 UPDATE 와 HOT (Heap-Only Tuple)",
                "인덱스가 어디를 가리키고, UPDATE 가 인덱스 항목을 새로 만드나", out=OUT)
    # 일반
    d.text(40, 100, "일반 UPDATE", 18, P["red"], weight=700)
    d.card("i1", 40, 140, 280, 70, "인덱스 항목 1", None, bg=P["as_bg"], stroke=P["front"], title_size=14)
    d.card("i2", 40, 260, 280, 70, "인덱스 항목 2  (새로 생긴다)", None, bg=P["bad_bg"], stroke=P["red"], title_size=14)
    d.card("t1", 420, 140, 250, 70, "옛 튜플", None, bg=P["note_bg"], stroke=P["muted"], title_size=14)
    d.card("t2", 420, 260, 250, 70, "새 튜플", None, bg=P["ok_bg"], stroke=P["green"], title_size=14)
    d.arrow([d.anchor("i1", "e"), d.anchor("t1", "w")], P["front"], start="i1", end="t1")
    d.arrow([d.anchor("i2", "e"), d.anchor("t2", "w")], P["red"], start="i2", end="t2")
    d.text(40, 350, "인덱스마다 새 항목이 생긴다 — 새 튜플을 가리키는 항목", 14, P["ink"])
    # HOT
    d.text(740, 100, "HOT", 18, P["green"], weight=700)
    d.card("hi", 740, 140, 280, 70, "인덱스 항목 (그대로)", None, bg=P["as_bg"], stroke=P["front"], title_size=14)
    d.card("hr", 1090, 140, 270, 70, "사슬의 뿌리 (옛 튜플)\nHEAP_HOT_UPDATED", None, bg=P["note_bg"], stroke=P["muted"], title_size=13)
    d.card("hn", 1090, 260, 270, 70, "새 튜플\nHEAP_ONLY_TUPLE", None, bg=P["ok_bg"], stroke=P["green"], title_size=13)
    d.arrow([d.anchor("hi", "e"), d.anchor("hr", "w")], P["front"], start="hi", end="hr")
    d.arrow([d.anchor("hr", "s"), d.anchor("hn", "n")], P["green"], "같은 페이지에서\n앞으로 따라간다", start="hr", end="hn")
    d.text(740, 350, "새 인덱스 항목이 없다 — 인덱스는 사슬의 뿌리를 가리킨다", 14, P["ink"])
    d.card("cond", 40, 410, 660, 110, "HOT 이 되는 조건 (둘 다)",
           "1  갱신하는 컬럼이 어떤 인덱스에도 없다 (BRIN 같은 요약 인덱스 제외)\n2  새 버전이 같은 힙 페이지에 들어갈 자리가 있다",
           bg=P["todo_bg"], stroke=P["orange"], title_size=15, body_size=14)
    d.card("prune", 740, 410, 620, 110, "사슬 정리(pruning)는 VACUUM 만 하지 않는다",
           "SELECT · UPDATE · DELETE 같은 일반 페이지 접근 중에도 일어난다\n페이지가 거의 찼을 때(여유 10% 미만) · cleanup 락을 막힘 없이 얻을 때",
           bg=P["note_bg"], stroke=P["line"], title_size=15, body_size=14)
    d.card("meas", 40, 550, 1320, 100, "실측: 전부가 HOT 은 아니었다 (psql 2026-10-13)",
           "인덱스 둘(id pk · k)이 있는 100행 테이블에서 인덱스 없는 컬럼 v 를 두 번 UPDATE -> n_tup_upd = 200, n_tup_hot_upd = 100\n"
           "이어 인덱스된 k 를 10행 UPDATE -> n_tup_upd = 210, n_tup_hot_upd 는 그대로 100",
           bg=P["bad_bg"], stroke=P["red"], title_size=15, body_size=14)
    d.save()


def vs_undo():
    d = Diagram("blog02-vs-undo", 1400, 380, "옛 버전은 어디에 있나 — PostgreSQL 과 InnoDB",
                "둘 다 MVCC 이지만 옛 버전을 두는 곳이 다르다 (문서로 확인되는 만큼만)", out=OUT)
    d.card("pg", 40, 120, 640, 130, "PostgreSQL",
           "옛 버전이 힙(테이블 파일)에 그대로 남는다\n옛 튜플과 새 튜플이 같은 페이지에 나란히 보인다\n"
           "그래서 부푼 만큼을 VACUUM 이 치운다",
           bg=P["as_bg"], stroke=P["front"], title_size=17, body_size=15)
    d.card("my", 720, 120, 640, 130, "MySQL InnoDB",
           "옛 버전은 undo 로 \"재구성\" 한다\n(\"undo 로그를 레코드의 메모리 복사본에 적용해\" — 17.7.2.4)\n"
           "옛 버전 자체를 잠글 수는 없다",
           bg=P["bff_bg"], stroke=P["back"], title_size=17, body_size=15)
    d.card("n", 40, 290, 1320, 56, "그 결과 어디가 부풀고 무엇이 치워지는지(purge 등)의 세부는 확인하지 않았다", None,
           bg=P["note_bg"], stroke=P["line"], title_size=15)
    d.save()


if __name__ == "__main__":
    for f in (intro, update_chain, tuple_header, xmax_nonzero, rollback, hintbit, hot, vs_undo):
        f()
    finish()
