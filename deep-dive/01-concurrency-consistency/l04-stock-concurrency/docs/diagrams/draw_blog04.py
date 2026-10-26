#!/usr/bin/env python3
"""01.04 블로그판 04 그림. 실행: python3 -I docs/diagrams/draw_blog04.py (레슨 폴더에서)"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[4] / "tools"))
from diagram import Diagram, P, finish, timeline as _timeline  # noqa: E402

OUT = pathlib.Path(__file__).parent


def timeline(*a, **k):
    return _timeline(*a, out=OUT, **k)


def cas():
    d = Diagram("blog04-cas", 1460, 560, "낙관 락 — 읽을 땐 락 없이, 쓸 때 version 으로 확인",
                "compare-and-set (비교 후 교체) 와 같은 모양이다", out=OUT)
    d.card("r", 40, 110, 420, 130, "① 읽기 (락 없음)", "SELECT qty, version\nFROM stock WHERE sku = :sku\n본 값: version = v", bg=P["as_bg"], stroke=P["front"], title_size=17, body_size=14)
    d.card("c", 520, 110, 300, 130, "앱 계산", "새 qty 를 계산한다\n(틈이 있다)", bg=P["note_bg"], stroke=P["line"], title_size=17, body_size=14)
    d.card("w", 880, 110, 540, 130, "② 쓰기", "UPDATE stock SET qty = :새값, version = version + 1\nWHERE sku = :sku AND version = :읽은version", bg=P["todo_bg"], stroke=P["orange"], title_size=17, body_size=14)
    d.arrow([(460, 175), (520, 175)], P["muted"], start="r", end="c")
    d.arrow([(820, 175), (880, 175)], P["muted"], start="c", end="w")
    d.card("ok", 880, 300, 260, 110, "영향 행 1", "내가 읽은 뒤 아무도\n안 고쳤다 → 성공", bg=P["ok_bg"], stroke=P["green"], title_size=17, body_size=14)
    d.card("no", 1160, 300, 260, 110, "영향 행 0", "누군가 이 행을 고쳤다\n→ 충돌", bg=P["bad_bg"], stroke=P["red"], title_size=17, body_size=14)
    d.arrow([(1010, 240), (1010, 300)], P["green"], start="w", end="ok")
    d.arrow([(1290, 240), (1290, 300)], P["red"], start="w", end="no")
    d.card("re", 40, 440, 1380, 90, "충돌이면 읽은 값(qty)은 낡았으니 버리고 처음부터 다시 읽는다",
           "처음 읽은 qty 로 재계산하면 같은 충돌이 반복된다. 이 레슨의 retries 카운터가 세는 것이 이 횟수다",
           bg=P["note_bg"], stroke=P["line"], title_size=16, body_size=14)
    d.arrow([(1290, 410), (1290, 440)], P["red"])
    d.save()


def conflict():
    timeline("blog04-conflict", "충돌 장면: 두 구매자가 같은 version 을 읽는다",
             "재고 8, version 3. A 는 2 개, B 는 1 개를 산다",
             [("A", "1  SELECT qty, version", "본 값: qty 8, version 3", None),
              ("B", "2  SELECT qty, version", "본 값: qty 8, version 3", None),
              ("A", "3  UPDATE qty = 6, version = 4  WHERE version = 3", "행 락을 잡고 갱신 → COMMIT", None),
              ("B", "4  UPDATE qty = 7, version = 4  WHERE version = 3", "같은 행이라 A 가 끝나기를 기다린 뒤, 재평가", "bad")],
             [(2, 3, "version 이 3 에서\n4 로 바뀌었다", 0.5)],
             "B 의 WHERE version = 3 은 갱신된 행에서 거짓이 되어 갱신된 행이 없다 — \"충돌했다, 다시 읽어라\" 의 신호다.\n"
             "그래서 낙관 락의 낙관은 \"읽는 동안 락이 없다\" 이지 \"쓰는 순간 기다림이 없다\" 가 아니다.",
             "B 의 쓰기가 충돌로 감지된다")


def two_signals():
    d = Diagram("blog04-two-signals", 1460, 450, "충돌 신호는 두 가지 모양이다",
                "코드는 두 경로를 모두 알아야 한다", out=OUT)
    d.card("a", 40, 110, 680, 200, "READ COMMITTED (이 레슨)",
           "기다린 뒤 갱신된 행에 version 을 재평가\n→ 영향 행 0\n\nexecuteUpdate() == 0 으로 읽는다",
           bg=P["todo_bg"], stroke=P["orange"], title_size=18, body_size=15)
    d.card("b", 760, 110, 660, 200, "REPEATABLE READ 이상",
           "version 조건에 닿기 전에 엔진이 먼저 실패시킨다\nERROR: could not serialize access due to\nconcurrent update  (40001) — 예외\n\n트랜잭션은 롤백하고 처음부터 다시 한다",
           bg=P["bad_bg"], stroke=P["red"], title_size=18, body_size=15)
    d.card("n", 40, 340, 1380, 70, "executeUpdate() == 0 만 보는 재시도 루프는 두 번째 경로를 못 잡는다", None, bg=P["note_bg"], stroke=P["line"], title_size=15)
    d.save()


def retry_loop():
    d = Diagram("blog04-retry-loop", 1460, 570, "재시도 루프 — 상한이 필수다",
                "이 레슨의 선택: MAX_ATTEMPTS = 20, 대기 없이 바로 다시 읽는다", out=OUT)
    d.pill("rd", 40, 150, 260, 80, "읽기\nStockTable.read", P["as_bg"], P["front"], size=15)
    d.pill("ck", 380, 150, 260, 80, "재고 확인", P["note_bg"], P["line"], size=15)
    d.pill("up", 720, 150, 320, 80, "UPDATE ... WHERE version = v", P["todo_bg"], P["orange"], size=15)
    d.arrow([(300, 190), (380, 190)], P["muted"], start="rd", end="ck")
    d.arrow([(640, 190), (720, 190)], P["muted"], "충분", start="ck", end="up", label_size=13)
    d.pill("sold", 380, 300, 260, 70, "false (정상적인 품절)", P["ok_bg"], P["green"], size=15)
    d.arrow([(510, 230), (510, 300)], P["green"], "모자람", start="ck", end="sold", label_size=13)
    d.pill("ok", 1120, 150, 300, 80, "영향 행 1 → true (성공)", P["ok_bg"], P["green"], size=15)
    d.arrow([(1040, 190), (1120, 190)], P["green"], "1행", start="up", end="ok", label_size=13)
    d.pill("lose", 720, 300, 320, 70, "영향 행 0 → 충돌", P["bad_bg"], P["red"], size=15)
    d.arrow([(880, 230), (880, 300)], P["red"], "0행", start="up", end="lose", label_size=13)
    d.arrow([(880, 370), (880, 400), (170, 400), (170, 230)], P["orange"], "상한 이내면 처음부터 다시 읽는다", dashed=True, label_at=(520, 400), label_size=14)
    d.pill("ex", 1120, 300, 300, 70, "상한 초과 → IllegalStateException", P["bad_bg"], P["red"], size=14)
    d.arrow([(1040, 335), (1120, 335)], P["red"], "20 번 넘음", start="lose", end="ex", label_size=13)
    d.card("n", 40, 440, 1380, 100, "\"재고 부족\" 과 \"경합이 너무 심해 포기\" 는 다르다",
           "재고가 모자라면 예외가 아니라 false 다. 상한을 넘겼을 때만 예외를 던진다.\n재고가 있는데 품절이라고 응답하면 호출자가 거짓말을 하게 된다.",
           bg=P["note_bg"], stroke=P["line"], title_size=16, body_size=14)
    d.save()


def version_rule():
    d = Diagram("blog04-version-rule", 1460, 480, "왜 재고 N 이면 최대 N 번 지나",
                "version 은 판매가 성공한 UPDATE 에서만 오른다 (이 레슨 구현)", out=OUT)
    steps = [("1  한 번 진다", "읽고 쓰는 사이에\n다른 구매자의 판매가\n하나 성공했다"),
             ("2  다시 읽는다", "그 판매는 이미 반영돼 있다\n같은 판매가 나를\n두 번 이길 수 없다"),
             ("3  최대 N 번", "판매는 재고를 1 씩 줄이므로\n최대 N 번 지고\n다음 읽기는 재고 0 = 품절")]
    for i, (t, b) in enumerate(steps):
        d.card(f"s{i}", 40 + i * 470, 110, 440, 160, t, b, bg=P["as_bg"], stroke=P["front"], title_size=18, body_size=15)
    d.arrow([(480, 190), (510, 190)], P["muted"], start="s0", end="s1")
    d.arrow([(950, 190), (980, 190)], P["muted"], start="s1", end="s2")
    d.card("n", 40, 310, 1380, 110, "구매자가 한 번씩만 사는 경우 다른 구매자 수(구매자 - 1)도 상한이 된다 (해석)",
           "따라서 내가 진 횟수 <= 내가 읽고 쓰기 전에 끝난 서로 다른 판매의 수.\n진 횟수 상한 = min(재고, 구매자 - 1)",
           bg=P["note_bg"], stroke=P["line"], title_size=16, body_size=14)
    d.save()


def bound():
    d = Diagram("blog04-bound", 1460, 430, "상한 20 에 닿는 경우와 닿지 않는 경우",
                "구매자 50 명이 한 행에 동시에 몰린다 (이 레슨의 관찰 테스트 시나리오)", out=OUT)
    d.card("a", 40, 110, 680, 190, "재고 10 · 구매자 50", "진 횟수는 최대 10 번\n상한 20 에 닿지 않는다\n→ 재시도소진 0",
           bg=P["ok_bg"], stroke=P["green"], title_size=18, body_size=16)
    d.card("b", 760, 110, 660, 190, "재고 1000 · 구매자 50", "진 횟수는 최대 49 번\n상한 20 을 넘길 수 있다\n→ 재고가 있는데도 예외 (재시도소진)",
           bg=P["bad_bg"], stroke=P["red"], title_size=18, body_size=16)
    d.card("n", 40, 330, 1380, 70, "관찰 표의 재시도소진 칸이 오른쪽 경우다 (05) — 상한을 올리기보다 전략을 바꾸는 것이 해법이다", None, bg=P["note_bg"], stroke=P["line"], title_size=15)
    d.save()


def edit_form():
    d = Diagram("blog04-edit-form", 1460, 500, "낙관 락이 진짜 필요한 곳 — 트랜잭션 경계 밖",
                "화면에서 값을 불러와 한참 뒤 저장하는 편집 흐름 (관리자 재고 수정 등)", out=OUT)
    d.card("t1", 40, 110, 620, 130, "읽기 트랜잭션 (이미 끝났다)", "화면에 qty 와 version 을 같이 내려 준다", bg=P["as_bg"], stroke=P["front"], title_size=17, body_size=15)
    d.pill("gap", 40, 270, 1380, 60, "사용자가 화면을 열어 둔 시간 — 어떤 트랜잭션도 열려 있지 않다 (다른 사람이 같은 행을 고칠 수 있다)", P["bad_bg"], P["red"], size=15)
    d.card("t2", 800, 110, 620, 130, "쓰기 트랜잭션 (저장 때 새로 연다)", "UPDATE ... WHERE version = :화면의 version", bg=P["todo_bg"], stroke=P["orange"], title_size=17, body_size=15)
    d.arrow([(660, 175), (800, 175)], P["muted"], "서로 다른\n트랜잭션", start="t1", end="t2", label_size=13)
    d.card("n", 40, 360, 1380, 110, "엔진이 알려 주지 않는다",
           "읽은 시점과 쓰는 시점이 서로 다른 트랜잭션이라 DB 격리수준이 이 충돌을 대신 막아 주지 못한다.\n0 행이면 \"다른 사람이 먼저 수정했습니다\" 를 보여 준다.\n비관 락은 10분 동안 트랜잭션과 락을 쥐어야 해서 불가능하다.",
           bg=P["note_bg"], stroke=P["line"], title_size=16, body_size=14)
    d.save()


def jpa():
    d = Diagram("blog04-jpa", 1460, 560, "JPA @Version 충돌이 예외로 나오는 길",
                "실측: Hibernate 6.4.10 · 6.6.58 · PostgreSQL 16 (2026-10-13)", out=OUT)
    d.pill("a", 40, 120, 400, 90, "엔티티의 qty 를 바꾸고 flush\nupdate Stock set qty=?,version=?\nwhere id=? and version=?", P["as_bg"], P["front"], size=14, mono=False)
    d.pill("b", 520, 120, 300, 90, "다른 트랜잭션이 먼저\nversion 을 올려 두었다\n→ 0 행 갱신", P["bad_bg"], P["red"], size=14)
    d.pill("c", 960, 120, 460, 90, "jakarta.persistence.OptimisticLockException\ncause = org.hibernate.StaleObjectStateException\n\"Row was updated or deleted by another transaction …\"", P["bad_bg"], P["red"], size=14)
    d.arrow([(440, 165), (520, 165)], P["muted"], start="a", end="b")
    d.arrow([(820, 165), (960, 165)], P["red"], "예외로 감싸 던진다", start="b", end="c", label_size=13)
    d.card("n1", 40, 260, 680, 120, "네이티브 Session 도 마찬가지", "flush() · commit() 모두 StaleObjectStateException 이 직접 나오지 않고\nOptimisticLockException 으로 감싸져 나온다\n→ catch (StaleObjectStateException) 만 두면 못 잡는다",
           bg=P["todo_bg"], stroke=P["orange"], title_size=16, body_size=14)
    d.card("n2", 760, 260, 660, 120, "던져지면 트랜잭션은 롤백 표시 (스펙 3.4.5)", "그래서 재시도는 트랜잭션 밖\n= 트랜잭션 전체를 다시 실행하는 쪽에 둔다",
           bg=P["note_bg"], stroke=P["line"], title_size=16, body_size=14)
    d.card("n3", 40, 410, 1380, 100, "참고: 7.4.13 은 cause 사슬이 한 단계 더 길다",
           "StaleObjectStateException → StaleStateException (\"Unexpected row count (expected row count 1 but was 0)\")\n0 행이면 이 예외가 난다는 점은 User Guide(Locking · 6.4)도 쓴다",
           bg=P["note_bg"], stroke=P["line"], title_size=15, body_size=14)
    d.save()


if __name__ == "__main__":
    for f in (cas, conflict, two_signals, retry_loop, version_rule, bound, edit_form, jpa):
        f()
    finish()
