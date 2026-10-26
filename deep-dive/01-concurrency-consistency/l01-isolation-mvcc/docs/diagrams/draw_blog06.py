#!/usr/bin/env python3
"""01.01 블로그판 06 그림. 실행: python3 -I docs/diagrams/draw_blog06.py (레슨 폴더에서)"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[4] / "tools"))
from diagram import Diagram, P, finish, timeline as _timeline  # noqa: E402

OUT = pathlib.Path(__file__).parent


def timeline(*a, **k):
    return _timeline(*a, out=OUT, **k)


def intro():
    timeline("blog06-intro", "도입: 열어 둔 트랜잭션 하나가 VACUUM 을 막는다",
             "100행 테이블 (이 테이블의 autovacuum 은 꺼 두었다 — 실측: psql 2026-10-13). 읽기 한 번만 한 REPEATABLE READ 트랜잭션이 열려 있다",
             [("A", "1  BEGIN;  SELECT count(*) FROM t", "스냅샷 고정 — 그대로 열어 둔다 (idle in transaction)", None),
              ("B", "2  50행 DELETE + 전체 UPDATE", "옛 튜플들이 죽은 튜플이 된다", None),
              ("B", "3  VACUUM (VERBOSE) t", "100 are dead but not yet removable", "bad"),
              ("A", "4  COMMIT", "열린 스냅샷이 사라진다", None),
              ("B", "5  VACUUM (VERBOSE) t", "100 removed, 0 are dead but not yet removable", "ok")],
             [(0, 2, "A 의 스냅샷이 아직\n옛 버전을 볼 수 있다", 0.45), (3, 4, "스냅샷이 끝나자\n치울 수 있다", 0.5)],
             "열린 스냅샷 하나가 100개의 죽은 튜플 청소를 막았다. 열린 트랜잭션이 끝나자 같은 VACUUM 이 바로 치웠다.\n"
             "읽기 한 번뿐인 트랜잭션이었다 — 오래 열려 있는 것만으로도 테이블이 부푼다.",
             "읽기만 한 트랜잭션도 청소를 막는다", level="REPEATABLE READ", level_b="autocommit")


def dead_life():
    d = Diagram("blog06-dead-life", 1400, 480, "옛 튜플의 일생 — 죽었다고 바로 치울 수 있는 것은 아니다",
                "UPDATE · DELETE 가 남긴 옛 튜플이 치워지기까지", out=OUT)
    steps = [("살아 있다", "현재 버전", P["ok_bg"], P["green"]),
             ("UPDATE · DELETE", "옛 튜플에 xmax 가 적힌다", P["as_bg"], P["front"]),
             ("아직 못 치운다", "열린 스냅샷 중 누군가 아직\n볼 수 있다 (VACUUM VERBOSE 가\ndead but not yet removable 로 센다)", P["bad_bg"], P["red"]),
             ("치울 수 있다", "어떤 스냅샷에서도\n보이지 않는다 = 죽었다(dead)", P["note_bg"], P["muted"]),
             ("VACUUM", "공간을 재사용 가능으로\n표시한다", P["todo_bg"], P["orange"])]
    for i, (t, b, bg, st) in enumerate(steps):
        d.card(f"s{i}", 40 + i * 270, 120, 250, 150, t, b, bg=bg, stroke=st, title_size=15, body_size=14, align="center")
        if i:
            d.arrow([(40 + i * 270 - 20, 195), (40 + i * 270, 195)], P["muted"])
    d.card("n", 40, 320, 1320, 110, "UPDATE · DELETE 가 남긴 옛 튜플은 어떤 스냅샷에서도 보이지 않게 되면 \"죽었다(dead)\" (문서 25.1)",
           "VACUUM 이 죽은 튜플을 치워 공간을 재사용 가능하게 표시한다 (문서 25.1)\n"
           "세 번째 단계에 머무르게 만드는 것이 열려 있는 트랜잭션이다 — 이 글의 나머지가 그 이야기다",
           bg=P["note_bg"], stroke=P["line"], title_size=15, body_size=14)
    d.save()


def vacuum_reasons():
    d = Diagram("blog06-vacuum-reasons", 1400, 480, "VACUUM 이 필요한 네 가지 이유 (문서 25.1)",
                "죽은 튜플 청소가 첫째이고, 나머지 셋도 같은 도구가 맡는다", out=OUT)
    cs = [("1  공간 회수 · 재사용", "갱신·삭제된 행이 차지한\n디스크 공간", P["as_bg"], P["front"]),
          ("2  통계 갱신", "쿼리 플래너가 쓰는 통계", P["bff_bg"], P["back"]),
          ("3  visibility map 갱신", "인덱스 전용 스캔을 빠르게", P["ok_bg"], P["green"]),
          ("4  XID wraparound 방지", "트랜잭션 ID (및 multixact ID)\nwraparound 로 인한 아주 오래된\n데이터 손실 방지", P["bad_bg"], P["red"])]
    for i, (t, b, bg, st) in enumerate(cs):
        d.card(f"c{i}", 40 + i * 335, 120, 315, 190, t, b, bg=bg, stroke=st, title_size=15, body_size=14)
    d.card("n", 40, 350, 1320, 80, "이 글은 첫째(죽은 튜플과 horizon)와 넷째(wraparound)를 따라간다", None,
           bg=P["note_bg"], stroke=P["line"], title_size=15)
    d.save()


def horizon():
    d = Diagram("blog06-horizon", 1400, 600, "xmin horizon — 어디까지 치울 수 있나",
                "가장 오래된 열린 스냅샷이 아직 볼 수 있는 튜플은 치울 수 없다 (트랜잭션 ID 는 설명용 숫자)", out=OUT)
    d.arrow([(40, 190), (1360, 190)], P["muted"], "트랜잭션 ID 가 커지는 방향")
    # horizon line
    d.arrow([(760, 120), (760, 260)], P["red"], head=False, dashed=True, sw=3)
    d.text(760, 100, "horizon = 가장 오래된 열린 스냅샷의 xmin (backend_xmin)", 15, P["red"], align="center", weight=700)
    tuples = [(100, "죽은 튜플\nxmax = 810", True), (260, "죽은 튜플\nxmax = 820", True), (420, "죽은 튜플\nxmax = 830", True),
              (900, "죽은 튜플\nxmax = 910", False), (1060, "죽은 튜플\nxmax = 920", False), (1220, "죽은 튜플\nxmax = 930", False)]
    for i, (x, t, ok) in enumerate(tuples):
        d.pill(f"t{i}", x, 290, 140, 70, t, P["ok_bg"] if ok else P["bad_bg"], P["green"] if ok else P["red"], size=13)
    d.text(260, 380, "horizon 보다 먼저 죽었다\n-> 아무 스냅샷도 못 본다 -> 치울 수 있다", 14, P["green"], align="center")
    d.text(1060, 380, "horizon 이후에 죽었다\n-> 열린 스냅샷이 아직 볼 수 있다\n-> dead but not yet removable", 14, P["red"], align="center")
    d.card("q", 40, 470, 1320, 100, "pg_stat_activity.backend_xmin = \"현재 백엔드의 xmin horizon\" (문서 28.2)",
           "열린 트랜잭션은 \"그 트랜잭션에게만 보일 수 있는 최근에 죽은 튜플\" 을 VACUUM 이 치우는 것을 막는다 — 오래 idle 이면 테이블 bloat 의 원인이 된다 (문서 20.11)",
           bg=P["note_bg"], stroke=P["line"], title_size=15, body_size=14)
    d.save()


def measured():
    d = Diagram("blog06-measured", 1400, 520, "실측 — 같은 VACUUM 이 열린 트랜잭션 때문에 달라진다",
                "100행 테이블, 50행 삭제 + 전체 UPDATE 뒤 VACUUM (VERBOSE) (실측: psql 2026-10-13)", out=OUT)
    d.card("a", 40, 110, 640, 220, "열린 REPEATABLE READ 트랜잭션이 있을 때",
           "tuples: 25 removed, 150 remain,\n        100 are dead but not yet removable\nremovable cutoff: 793,\n        which was 1 XIDs old when operation ended\n\n"
           "그 세션: state = idle in transaction, backend_xmin = 793",
           bg=P["bad_bg"], stroke=P["red"], title_size=16, body_size=14, mono_body=True)
    d.card("b", 720, 110, 640, 220, "열린 트랜잭션이 끝난(커밋) 뒤",
           "tuples: 100 removed, 50 remain,\n        0 are dead but not yet removable\nremovable cutoff: 794,\n        which was 0 XIDs old when operation ended",
           bg=P["ok_bg"], stroke=P["green"], title_size=16, body_size=14, mono_body=True)
    d.arrow([d.anchor("a", "e"), d.anchor("b", "w")], P["muted"], "트랜잭션\n커밋", start="a", end="b")
    d.card("n", 40, 360, 1320, 130, "열린 스냅샷 하나가 100개의 죽은 튜플 청소를 막았다",
           "\"25 removed\" 는 HOT 정리 등 페이지 접근 중 이미 치워진 몫으로 보인다 (해석 — 직접 확인하지 않았다)\n"
           "결과를 결정적으로 만들려고 그 테이블의 autovacuum 은 꺼 두었다",
           bg=P["note_bg"], stroke=P["line"], title_size=16, body_size=14)
    d.save()


def vs_full():
    d = Diagram("blog06-vs-full", 1400, 520, "일반 VACUUM 과 VACUUM FULL, 그리고 autovacuum",
                "공간을 \"재사용 표시\" 하는 것과 \"돌려주는 것\" 은 다르다 (문서 25.1)", out=OUT)
    d.card("v", 40, 120, 640, 220, "VACUUM (일반)",
           "죽은 튜플을 치우고 공간을 재사용 가능으로 표시한다\nOS 에 돌려주지는 않는다\n(예외: 테이블 끝의 페이지가 전부 비고\n배타 락을 쉽게 얻을 때)\n"
           "운영과 병행 가능 — SELECT/INSERT/UPDATE/DELETE 계속 동작\n(ALTER TABLE 같은 정의 변경은 불가)",
           bg=P["ok_bg"], stroke=P["green"], title_size=17, body_size=14)
    d.card("f", 720, 120, 640, 220, "VACUUM FULL",
           "테이블을 새로 써서 공간을 줄인다\n느리고 ACCESS EXCLUSIVE 락이 필요해\n다른 사용을 막는다 · 추가 디스크 공간 필요\n\n"
           "문서는 일반 VACUUM 을 쓰고 FULL 을 피하라고 권한다",
           bg=P["bad_bg"], stroke=P["red"], title_size=17, body_size=14)
    d.card("n", 40, 380, 1320, 100, "autovacuum 은 VACUUM FULL 을 절대 실행하지 않는다 (문서 25.1)",
           "한 번 부푼 테이블은 그냥 두면 줄지 않는다 — 부푼 뒤의 조치는 비싸다. 그래서 예방(짧은 트랜잭션 · 타임아웃)이 핵심이다 (해석)",
           bg=P["note_bg"], stroke=P["line"], title_size=15, body_size=14)
    d.save()


def xid_bar():
    d = Diagram("blog06-xid-bar", 1400, 640, "XID wraparound 와 freeze — 나이(age)가 어디까지 갔나",
                "눈금은 축척이 아니다. 기본값은 PostgreSQL 16 (문서는 autovacuum_freeze_max_age 만 \"기본 2억\" 이라 쓴다 — 나머지는 실측: psql 2026-10-13 SHOW)", out=OUT)
    d.rect("bar", 40, 150, 1320, 36, P["ok_bg"], P["green"])
    marks = [(120, "50,000,000", "vacuum_freeze_min_age", "VACUUM 이 이보다 오래된 행을\nfrozen 으로 표시", P["front"]),
             (420, "150,000,000", "vacuum_freeze_table_age", "문서: 유효 최댓값은\n0.95 * autovacuum_freeze_max_age", P["orange"]),
             (720, "200,000,000", "autovacuum_freeze_max_age", "넘으면 autovacuum 이 꺼져 있어도\n강제 vacuum (to prevent wraparound)", P["red"]),
             (1020, "wraparound 4천만 전", "WARNING", "database \"...\" must be vacuumed\nwithin ... transactions", P["orange"]),
             (1250, "wraparound 300만 미만", "새 XID 발급 거부", "database is not accepting commands\nto avoid wraparound data loss", P["red"])]
    for x, a, b, c, col in marks:
        d.arrow([(x, 150), (x, 130)], col, head=False, sw=3)
        d.text(x, 100, a, 13, col, align="center", weight=700)
        d.text(x, 200, b, 13, col, align="center", mono=True)
        d.text(x, 230, c, 12, P["ink"], align="center")
    d.text(40, 130, "age = 0", 13, P["muted"])
    d.card("w", 40, 330, 640, 130, "트랜잭션 ID 는 32비트라 순환한다",
           "모든 테이블을 20억 트랜잭션마다 한 번 이상 VACUUM 해야 한다\nFrozenTransactionId 는 보통의 비교 규칙을 따르지 않고\n모든 일반 XID 보다 오래된 것으로 취급된다",
           bg=P["note_bg"], stroke=P["line"], title_size=15, body_size=14)
    d.card("fz", 720, 330, 640, 130, "freeze 는 플래그 비트로 한다",
           "9.4 이전에는 xmin 을 실제로 바꿨지만 지금은 플래그 비트만 세운다 (xmin 보존)\n소스: HEAP_XMIN_FROZEN = HEAP_XMIN_COMMITTED | HEAP_XMIN_INVALID",
           bg=P["note_bg"], stroke=P["line"], title_size=15, body_size=14)
    d.card("q", 40, 490, 1320, 120, "점검 쿼리 (문서 25.1)",
           "SELECT datname, age(datfrozenxid) FROM pg_database;      테이블별은 age(relfrozenxid)\n"
           "pg_xact 크기는 autovacuum_freeze_max_age 에 비례한다 — 기본 2억이면 약 50MB",
           bg=P["todo_bg"], stroke=P["orange"], title_size=15, body_size=14, mono_body=False)
    d.save()


def monitor():
    d = Diagram("blog06-monitor", 1400, 560, "감시 — 어디를 보면 horizon 을 붙잡은 범인이 보이나",
                "pg_stat_activity · pg_stat_user_tables · VACUUM (VERBOSE) (PostgreSQL 16, 문서 28.2 의 컬럼)", out=OUT)
    cs = [("pg_stat_activity", "xact_start 가 오래된 트랜잭션\nstate = idle in transaction\nbackend_xmin · age(backend_xmin)\n"
           "state_change = state 가 마지막으로 바뀐 시각", "backend_xmin 이 오래되었으면\nhorizon 을 붙잡는 후보", P["as_bg"], P["front"]),
          ("pg_stat_user_tables", "n_dead_tup (추정 죽은 행 수) · n_live_tup\nlast_autovacuum · autovacuum_count\nn_tup_hot_upd / n_tup_upd (HOT 비율)",
           "죽은 튜플이 쌓이는데\nautovacuum 이 안 도는지", P["ok_bg"], P["green"]),
          ("VACUUM (VERBOSE) 테이블", "dead but not yet removable", "0 이 아니면 horizon 이 붙잡힌 것", P["bad_bg"], P["red"])]
    for i, (t, a, b, bg, st) in enumerate(cs):
        d.card(f"c{i}", 40 + i * 450, 110, 420, 250, t, a + "\n\n-> " + b, bg=bg, stroke=st, title_size=16, body_size=13)
    d.card("st", 40, 400, 1320, 120, "state 값 (문서 28.2)",
           "active · idle · idle in transaction (트랜잭션 안에서 쿼리 안 도는 중) · idle in transaction (aborted) (그 안에서 한 문장이 에러)\n"
           "age(backend_xmin) = 현재 XID 로부터 몇 개 전인가 (문서 25.1 이 age(c.relfrozenxid) 로 쓰는 함수)",
           bg=P["note_bg"], stroke=P["line"], title_size=15, body_size=14)
    d.save()


def defenses():
    d = Diagram("blog06-defenses", 1400, 600, "방어선 — 앱과 서버 양쪽에",
                "오래 열린 트랜잭션을 막는 장치들. PostgreSQL 16 에는 transaction_timeout 이 없다 (문서 20.11)", out=OUT)
    d.card("app", 40, 110, 640, 210, "앱 쪽",
           "트랜잭션 안에서 외부 API · 파일 · 사용자 응답 대기를 하지 않는다\n@Transactional(timeout = n) — 초 단위, REQUIRED/REQUIRES_NEW 일 때 적용\n"
           "이것이 서버 쪽 timeout 을 대체하지는 않는다 — 앱이 죽거나\n연결이 반쯤 끊긴 경우를 서버가 정리해야 한다 (해석)",
           bg=P["as_bg"], stroke=P["front"], title_size=17, body_size=14)
    d.card("srv", 720, 110, 640, 210, "서버 쪽",
           "idle_in_transaction_session_timeout — 기본 0 (꺼짐)\n트랜잭션 안에서 idle 인 세션을 끊는다\n"
           "예: ALTER ROLE app_user SET\n      idle_in_transaction_session_timeout = '5min';\n"
           "idle_session_timeout 은 트랜잭션 밖 idle 세션을 끊는다",
           bg=P["ok_bg"], stroke=P["green"], title_size=17, body_size=14)
    d.card("warn", 40, 360, 1320, 110, "주의: 풀 뒤에서 idle_session_timeout 을 쓸 때",
           "문서는 커넥션 풀 뒤에서 쓰면 풀이 갑작스런 종료에 잘 대응하지 못할 수 있으니 조심하라고 쓴다\n"
           "트랜잭션 안 idle 쪽(idle_in_transaction_...)과 구분한다",
           bg=P["todo_bg"], stroke=P["orange"], title_size=15, body_size=14)
    d.card("n", 40, 500, 1320, 70, "이미 부푼 테이블은 일반 VACUUM 으로 재사용 표시 — 공간 반환은 VACUUM FULL(배타 락). 장기 트랜잭션부터 끊는다", None,
           bg=P["note_bg"], stroke=P["line"], title_size=15)
    d.save()


if __name__ == "__main__":
    for f in (intro, dead_life, vacuum_reasons, horizon, measured, vs_full, xid_bar, monitor, defenses):
        f()
    finish()
