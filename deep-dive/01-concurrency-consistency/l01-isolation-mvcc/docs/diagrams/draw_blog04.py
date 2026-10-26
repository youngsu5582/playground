#!/usr/bin/env python3
"""01.01 블로그판 04 그림. 실행: python3 -I docs/diagrams/draw_blog04.py (레슨 폴더에서)"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[4] / "tools"))
from diagram import Diagram, P, finish, timeline as _timeline  # noqa: E402

OUT = pathlib.Path(__file__).parent


def timeline(*a, **k):
    return _timeline(*a, out=OUT, **k)


def intro():
    timeline("blog04-intro", "도입: 두 세션이 같은 행을 동시에 고친다",
             "재고 60 인 행 (id = 2). A 는 10 개, B 는 20 개를 빼는 UPDATE 를 거의 동시에 날린다",
             [("A", "1  UPDATE stock = stock - 10 WHERE id = 2", "아직 COMMIT 하지 않았다 — 이 행의 락을 쥔다", None),
              ("B", "2  UPDATE stock = stock - 20 WHERE id = 2", "같은 행이라 멈춘다 — A 가 끝나기를 기다린다", None),
              ("A", "3  COMMIT", "락이 풀린다 (재고 50)", None),
              ("B", "4  (UPDATE 가 이어서 진행된다)", "A 가 커밋한 50 위에서 계산 → 30", "ok")],
             [(0, 1, "같은 행 → 줄을 선다", 0.3), (2, 3, "락이 풀리면\n이어서 진행", 0.7)],
             "읽기는 MVCC 가 해결했지만, 같은 행을 둘이 동시에 고치는 일은 줄을 세워야 한다.\n"
             "A 의 10 도 B 의 20 도 사라지지 않았다 (60 - 10 - 20 = 30). 줄을 세우는 것이 행 락이고, 기다린 뒤에 어떻게 이어 가나는 격리수준마다 다르다.",
             "행 락이 줄을 세운다", vcolor="ok")


def three_fixes():
    d = Diagram("blog04-three-fixes", 1400, 560, "갱신 손실 — 해법은 크게 셋",
                "앱이 읽고 계산해서 덮어쓰면, 읽는 순간 행 락이 없으므로 DB 는 이것을 충돌로 보지 않는다 (read-modify-write)", out=OUT)
    d.card("bad", 40, 110, 1320, 110, "문제의 모양: 읽을 때 락 없음 -> 앱이 계산 -> 절대 값을 UPDATE",
           "SELECT stock (락 없음)  ->  앱이 stock - 10 을 계산  ->  UPDATE stock = 190\n"
           "그 사이 상대가 바꾼 것은 계산에 들어가지 않는다 — 한쪽 결과가 사라진다",
           bg=P["bad_bg"], stroke=P["red"], title_size=16, body_size=14, mono_body=False)
    cs = [("1  계산을 DB 안으로", "UPDATE ... SET stock = stock - 10\n한 문장 안에서 읽기-계산-쓰기\n행 락이 줄을 세운다", P["ok_bg"], P["green"]),
          ("2  읽을 때 잠그기", "SELECT ... FOR UPDATE\n읽은 행을 잠가 상대가 기다리게 한다\n(RR · SERIALIZABLE 에서는 40001 이 날 수 있다)", P["as_bg"], P["front"]),
          ("3  버전 컬럼으로 감지", "낙관적 락 (@Version)\n저장할 때 버전이 그대로인지 확인한다\n비교는 01.04 에서 다룬다", P["bff_bg"], P["back"])]
    for i, (t, b, bg, st) in enumerate(cs):
        d.card(f"c{i}", 40 + i * 450, 270, 420, 170, t, b, bg=bg, stroke=st, title_size=17, body_size=14)
        d.arrow([(250 + i * 450, 220), (250 + i * 450, 270)], P["muted"])
    d.card("n", 40, 470, 1320, 56, "이 글에서는 첫째 — 원자적 UPDATE 가 READ COMMITTED 에서 왜 안전한가 — 를 끝까지 본다", None,
           bg=P["note_bg"], stroke=P["line"], title_size=15)
    d.save()


def lock_in_tuple():
    d = Diagram("blog04-lock-in-tuple", 1400, 630, "행 락은 메모리가 아니라 튜플 자체에 적힌다",
                "한 세션이 SELECT ... FOR UPDATE 로 행을 잠그면, UPDATE 를 안 했는데도 xmax 에 잠근 트랜잭션이 적힌다 (실측: psql 2026-10-13)", out=OUT)
    d.card("t0", 40, 120, 340, 100, "잠그기 전", "xmin = 760   xmax = 0", bg=P["note_bg"], stroke=P["muted"], title_size=16, body_size=15, mono_body=True)
    d.arrow([d.anchor("t0", "e"), (560, 170)], P["front"], "트랜잭션 761 이\nFOR UPDATE", start="t0")
    d.card("t1", 560, 120, 380, 100, "잠근 뒤 (다른 세션이 읽은 행)", "xmin = 760   xmax = 761", bg=P["as_bg"], stroke=P["front"], title_size=16, body_size=15, mono_body=True)
    d.card("n", 980, 120, 380, 100, "HEAP_XMAX_LOCK_ONLY", "xmax 가 유효하다면 잠금자일 뿐이라는 표시",
           bg=P["todo_bg"], stroke=P["orange"], title_size=15, body_size=14)
    d.card("why", 40, 260, 1320, 90, "그래서 xmax 는 \"삭제자\" 와 \"잠금자\" 를 모두 나타낸다 (02 의 xmax 가 0 이 아닌데 보이는 행과 연결)",
           "문서 13.3.2: PostgreSQL 은 변경된 행에 대한 정보를 메모리에 기억하지 않는다 -> 한 번에 잠글 수 있는 행의 수에 제한이 없다\n"
           "그러나 행을 잠그면 디스크 쓰기가 생길 수 있다 — SELECT FOR UPDATE 는 선택한 행을 락 표시로 수정한다",
           bg=P["note_bg"], stroke=P["line"], title_size=15, body_size=14)
    d.text(40, 380, "행 락 모드 (문서 13.3.2)", 17, P["ink"], weight=700)
    ms = [("UPDATE (보통)", "FOR NO KEY UPDATE"), ("키 컬럼 변경 · DELETE", "FOR UPDATE")]
    for i, (a, b) in enumerate(ms):
        d.pill(f"ma{i}", 40, 415 + i * 60, 360, 46, a, P["as_bg"], P["front"], size=14)
        d.pill(f"mb{i}", 420, 415 + i * 60, 300, 46, b, P["white"], P["line"], size=14, mono=True)
    d.card("sel", 780, 400, 580, 80, "SELECT 의 락 절은 네 가지", "FOR UPDATE · FOR NO KEY UPDATE · FOR SHARE · FOR KEY SHARE",
           bg=P["white"], stroke=P["line"], title_size=15, body_size=13, mono_body=True)
    d.card("tbl", 40, 545, 1320, 60, "테이블 수준 (문서 13.3.1): UPDATE/DELETE/INSERT = ROW EXCLUSIVE, SELECT = ACCESS SHARE — 서로 충돌하지 않는다", None,
           bg=P["note_bg"], stroke=P["line"], title_size=14)
    d.save()


def pg_locks():
    d = Diagram("blog04-pg-locks", 1400, 600, "기다리는 모양 — 누가 누구를 기다리나",
                "세션 A(트랜잭션 737)가 UPDATE 후 커밋 전, 세션 B(738)가 같은 행을 UPDATE 하면 B 가 멈춘다 (실측: psql 2026-10-13)", out=OUT)
    d.card("a", 40, 120, 600, 200, "세션 A  (트랜잭션 737)",
           "pg_stat_activity: state = idle in transaction\n                  wait_event = ClientRead\n"
           "pg_locks: transactionid  ExclusiveLock  737\n          (자기 ID 에 대한 락)",
           bg=P["as_bg"], stroke=P["front"], title_size=16, body_size=14, mono_body=True)
    d.card("b", 760, 120, 600, 200, "세션 B  (트랜잭션 738)  — 멈춘다",
           "pg_stat_activity: state = active\n                  wait_event_type = Lock\n                  wait_event = transactionid\n"
           "pg_locks: transactionid  ShareLock  granted = f  737\n          tuple  ExclusiveLock (B 자신이 가진, 그 행)",
           bg=P["bad_bg"], stroke=P["red"], title_size=16, body_size=14, mono_body=True)
    d.arrow([d.anchor("b", "w"), d.anchor("a", "e")], P["red"], "737 이 끝나기를\n기다린다", start="b", end="a")
    d.card("n1", 40, 370, 660, 180, "행 락 자체는 pg_locks 에 한 줄로 안 나온다",
           "B 는 \"행의 현재 xmax 트랜잭션(737)이 끝나기를\"\n그 트랜잭션 ID 락으로 기다린다\n"
           "그래서 누가 누구를 기다리나의 답은\ntransactionid 번호가 누구의 것이냐다 (observe/SCRIPT.md 장면 3)",
           bg=P["todo_bg"], stroke=P["orange"], title_size=15, body_size=14)
    d.card("n2", 740, 370, 620, 180, "tuple 락은 왜 있나",
           "정확히 어떤 구조적 이유인지는 이 레슨에서 확인하지 않았다\n(해석 — 같은 행을 기다리는 줄을 세우는 용도로 보인다)",
           bg=P["note_bg"], stroke=P["line"], title_size=15, body_size=14)
    d.save()


def rc_steps():
    d = Diagram("blog04-rc-steps", 1400, 640, "READ COMMITTED — 기다린 뒤 최신 버전으로 재확인",
                "문서 13.2.1: UPDATE · DELETE · SELECT FOR UPDATE 가 이미 갱신 중인 행을 만났을 때", out=OUT)
    d.card("s1", 40, 110, 1320, 70, "1  문장 시작 시점의 스냅샷 기준으로 대상 행을 찾는다", None, bg=P["as_bg"], stroke=P["front"], title_size=16)
    d.card("s2", 40, 210, 1320, 70, "2  찾은 행을 다른 트랜잭션이 갱신(삭제 · 잠금) 중이면, 그 트랜잭션이 끝나기를 기다린다", None, bg=P["as_bg"], stroke=P["front"], title_size=16)
    d.arrow([(700, 180), (700, 210)], P["muted"])
    d.arrow([(700, 280), (700, 320)], P["muted"])
    d.card("r", 40, 320, 420, 130, "첫 트랜잭션이 롤백", "그 효과가 없어진다\n두 번째가 원래 찾은 행을 갱신한다", bg=P["ok_bg"], stroke=P["green"], title_size=16, body_size=14)
    d.card("c1", 490, 320, 420, 130, "커밋 — 그 행을 삭제했다", "그 행을 무시한다", bg=P["note_bg"], stroke=P["muted"], title_size=16, body_size=14)
    d.card("c2", 940, 320, 420, 130, "커밋 — 갱신했다", "갱신된 버전에 자기 연산을 적용한다\nWHERE 를 다시 평가해 여전히 맞는지 본다",
           bg=P["todo_bg"], stroke=P["orange"], title_size=16, body_size=14)
    d.card("side", 40, 490, 1320, 120, "부작용: 같은 행에서는 동시 갱신의 효과를 보고, 다른 행에서는 못 보는 일관되지 않은 스냅샷",
           "예: website.hits 가 9 와 10 인 두 행에 UPDATE website SET hits = hits + 1 이 도는 중 다른 세션이 DELETE FROM website WHERE hits = 10 을 하면,\n"
           "갱신 전후로 hits = 10 인 행이 있었는데도 DELETE 는 효과가 없다. 문서는 복잡한 검색 조건에는 부적합하고 단순한 경우에 알맞다고 한다",
           bg=P["note_bg"], stroke=P["line"], title_size=15, body_size=13)
    d.save()


def rc_recheck():
    timeline("blog04-rc-recheck", "READ COMMITTED — 기다렸다가 WHERE 를 다시 평가한다",
             "재고 50 인 행 (id = 4). B 는 \"재고가 40 이상일 때만 25 개를 뺀다\" 는 조건 UPDATE 를 날린다",
             [("A", "1  UPDATE stock = stock - 20 WHERE id = 4", "아직 COMMIT 하지 않았다 (50 -> 30)", None),
              ("B", "2  UPDATE stock = stock - 25  (stock >= 40 일 때만)", "처음 본 값은 50 — 조건은 맞는다. A 를 기다린다", None),
              ("A", "3  COMMIT", "최신 커밋 버전의 재고는 30", None),
              ("B", "4  (UPDATE 가 재개된다)", "최신 버전 30 에 WHERE 재평가 → 거짓 → 0행 갱신", "bad")],
             [(0, 1, "같은 행 → 기다린다", 0.3), (2, 3, "갱신된 버전(30)에\nWHERE 를 재평가", 0.7)],
             "B 가 스냅샷에서 본 값은 50 이었는데도 재평가는 최신 버전(30)에 적용됐다.\n"
             "그래서 B 는 \"재고 부족\" 에 해당하는 0행 갱신으로 끝난다 — 앱은 영향 행 수로 이를 안다.",
             "재평가가 최신 값에 적용된다")


def rr_40001():
    timeline("blog04-rr-40001", "REPEATABLE READ — 스냅샷 이후 바뀐 행은 고칠 수 없다",
             "재고 20 인 행 (id = 6). A 는 스냅샷을 잡은 뒤, 그 사이 B 가 바꿔 커밋한 행을 UPDATE 한다",
             [("A", "1  BEGIN;  SELECT stock WHERE id = 6", "본 값: 20 — 스냅샷이 여기서 고정된다", None),
              ("B", "2  UPDATE stock = 17  → COMMIT", "A 의 스냅샷 이후의 커밋", None),
              ("A", "3  UPDATE stock = stock - 1 WHERE id = 6", "ERROR 40001 — could not serialize access", "bad"),
              ("A", "4  SELECT ...", "25P02 — current transaction is aborted", "bad")],
             [(1, 2, "스냅샷 이후\n바뀐 행이다", 0.5)],
             "REPEATABLE READ 트랜잭션은 시작 후 다른 트랜잭션이 바꾼 행을 수정하거나 잠글 수 없다 (문서 13.2.2).\n"
             "에러 뒤 이 트랜잭션은 중단 상태다 — 다음 문장은 25P02 (current transaction is aborted, commands ignored until end of transaction block) 로 거절된다.\n"
             "그래서 ROLLBACK 후 트랜잭션 전체를 처음부터 다시 해야 한다.",
             "first-updater-wins — 늦은 쪽이 실패한다", level="REPEATABLE READ", level_b="autocommit")


def decision():
    d = Diagram("blog04-decision", 1400, 560, "같은 행에 UPDATE 가 부딪힐 때",
                "기다린 뒤의 행동이 격리수준마다 다르다. 갈리는 기준은 스냅샷이 문장 단위인가 트랜잭션 단위인가다", out=OUT)
    d.card("q", 40, 110, 1320, 70, "먼저 잡은 쪽이 아직 열려 있다 -> 기다린다 (RC · RR · SERIALIZABLE 모두)", None, bg=P["as_bg"], stroke=P["front"], title_size=17)
    d.arrow([(380, 180), (380, 250)], P["muted"], "상대가 커밋하면")
    d.arrow([(1020, 180), (1020, 250)], P["muted"], "상대가 커밋하면")
    d.card("rc", 40, 250, 680, 170, "READ COMMITTED",
           "기다린 뒤: 최신 버전에 WHERE 를 재평가해 계속\n결과: 조건이 아직 맞으면 적용, 아니면 0행\n"
           "이유: 문장마다 새 스냅샷 — 그 행의 최신 커밋 버전이 곧 내 세상의 일부다 (해석)",
           bg=P["ok_bg"], stroke=P["green"], title_size=17, body_size=14)
    d.card("rr", 740, 250, 620, 170, "REPEATABLE READ / SERIALIZABLE",
           "기다린 뒤: 상대가 커밋했으면 실패\n결과: 40001 — 앱이 트랜잭션 전체를 다시 한다\n"
           "이유: 스냅샷이 고정이라, 스냅샷 이후 바뀐 행을 고치면\n내가 읽은 세상과 다른 행을 덮어쓴다 (해석)",
           bg=P["bad_bg"], stroke=P["red"], title_size=17, body_size=14)
    d.card("n", 40, 450, 1320, 80, "한 가지 한계: 앱이 읽어서 계산한 절대 값을 쓰는 경우는 재평가가 도와주지 못한다",
           "읽을 때는 락이 없고, UPDATE 는 앱이 계산한 값을 그대로 쓴다 — 그 사이 상대가 바꾼 것이 계산에 들어가지 않는다. 이것이 갱신 손실이다",
           bg=P["todo_bg"], stroke=P["orange"], title_size=15, body_size=14)
    d.save()


def atomic():
    d = Diagram("blog04-atomic", 1400, 520, "절대 값을 쓰는 UPDATE 와 상대 값을 쓰는 UPDATE",
                "상대 값(SET x = x - n)은 기다린 뒤 최신 값에 적용된다. 절대 값은 앱이 계산한 값 그대로다", out=OUT)
    d.card("abs", 40, 110, 640, 250, "앱이 계산한 절대 값 (read-modify-write)",
           "SELECT stock            -> 200  (락 없음)\n앱이 200 - 40 = 160 을 계산\nUPDATE stock = 160\n\n"
           "그 사이 상대가 바꾼 값은 계산에 들어가지 않는다\n-> 갱신 손실",
           bg=P["bad_bg"], stroke=P["red"], title_size=17, body_size=14, mono_body=False)
    d.card("rel", 720, 110, 640, 250, "한 문장 안의 상대 값 (원자적 UPDATE)",
           "UPDATE account\n   SET balance = balance - :x\n WHERE id = :id AND balance >= :x\n\n"
           "행 락이 줄을 세우고, 기다린 쪽은 재확인으로\n최신 값에 대해 계산 · 검사한다\n영향 행 수(0/1)로 성공을 판정한다",
           bg=P["ok_bg"], stroke=P["green"], title_size=17, body_size=14, mono_body=False)
    d.card("n", 40, 390, 1320, 100, "READ COMMITTED 에서 이것이 정답인 이유는 13.2.1 의 재평가 규칙이다",
           "앱이 읽은 값이 아니라 갱신 시점의 최신 값에 적용되기 때문이다 (해석 — 문서 문장은 재평가 규칙까지이고, 이 정리는 그 적용)",
           bg=P["note_bg"], stroke=P["line"], title_size=15, body_size=14)
    d.save()


if __name__ == "__main__":
    for f in (intro, three_fixes, lock_in_tuple, pg_locks, rc_steps, rc_recheck, rr_40001, decision, atomic):
        f()
    finish()
