#!/usr/bin/env python3
"""01.04 블로그판 06 그림. 실행: python3 -I docs/diagrams/draw_blog06.py (레슨 폴더에서)"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[4] / "tools"))
from diagram import Diagram, P, finish, timeline as _timeline  # noqa: E402

OUT = pathlib.Path(__file__).parent


def timeline(*a, **k):
    return _timeline(*a, out=OUT, **k)


def two_worlds():
    d = Diagram("blog06-two-worlds", 1460, 520, "InnoDB 에서 일반 SELECT 와 갱신 문장은 서로 다른 세상을 본다",
                "MySQL 8.0 문서 17.7.2.3 · 17.7.2.4 의 요지", out=OUT)
    d.card("a", 40, 110, 680, 230, "일반 SELECT — 일관된 읽기 (스냅샷)",
           "락을 걸지 않는다\n다른 세션이 같은 테이블을 동시에 고칠 수 있다\n\nREPEATABLE READ 에서는 첫 읽기가 세운\n스냅샷을 본다",
           bg=P["as_bg"], stroke=P["front"], title_size=18, body_size=15)
    d.card("b", 760, 110, 660, 230, "UPDATE · DELETE · SELECT ... FOR UPDATE",
           "최신 커밋 데이터에 적용된다\nFOR UPDATE 는 읽은 각 행에 배타 락을 건다\n(검색된 UPDATE 가 거는 것과 같은 락)\n\n락은 커밋 · 롤백에서 풀린다",
           bg=P["rs_bg"], stroke=P["orange"], title_size=18, body_size=15)
    d.card("n", 40, 370, 1380, 110, "문서의 예 (17.7.2.3)",
           "REPEATABLE READ 트랜잭션에서 SELECT COUNT(...) 는 0 인데 UPDATE 는 10 행을 바꾼다 —\n다른 트랜잭션이 방금 커밋한 행에 DELETE / UPDATE 가 영향을 줄 수 있고, 바뀐 행은 현재 트랜잭션에 보이게 된다",
           bg=P["note_bg"], stroke=P["line"], title_size=16, body_size=14)
    d.save()


def trap():
    timeline("blog06-trap", "RR 의 함정 — 읽은 값으로 계산해 쓰기 (해석, 직접 재현하지 않음)",
             "InnoDB REPEATABLE READ. 재고 10, B 는 4 개를 사고 A 는 3 개를 산다",
             [("A", "1  SELECT qty", "본 값: 10  (스냅샷이 세워진다)", None),
              ("B", "2  UPDATE qty = qty - 4  → COMMIT", "최신 행은 이제 6", None),
              ("A", "3  SELECT qty", "본 값: 10  (일반 SELECT 는 옛 스냅샷)", None),
              ("A", "4  UPDATE qty = 7  → COMMIT", "10 - 3 = 7 을 최신 행에 적용 (해석)", "bad")],
             [(1, 3, "B 의 4 개가\n덮인다", 0.5)],
             "UPDATE 는 최신 커밋 행에 적용되므로 막지 않고 덮어쓸 수 있다 (해석 — 문서 두 문장의 조합).\n"
             "PostgreSQL REPEATABLE READ 라면 같은 상황에서 40001 로 막아 준다. 에러가 나던 곳이 조용히 통과하는 방향이다.",
             "갱신 손실 — 앱이 계산한 절대 값이 남의 갱신을 덮어쓴다", level="REPEATABLE READ")


def pg_vs_innodb():
    d = Diagram("blog06-pg-vs-innodb", 1460, 470, "스냅샷 이후 바뀐 행을 UPDATE 하면 — 두 엔진",
                "REPEATABLE READ 에서 같은 상황", out=OUT)
    d.card("p", 40, 110, 680, 200, "PostgreSQL 16",
           "스냅샷 이후 바뀐 행을 고치려 하면\n40001 로 거절한다 (문서 13.2.2)\n\n앱이 트랜잭션 전체를 재시도한다",
           bg=P["ok_bg"], stroke=P["green"], title_size=18, body_size=15)
    d.card("m", 760, 110, 660, 200, "MySQL 8.0 InnoDB",
           "UPDATE 가 최신 커밋 행에 적용된다\n이 \"직렬화 실패\" 에러는 문서에서 못 찾았다 (해석)\n\n읽은 옛 값으로 계산한 절대 값은 덮어쓸 수 있다",
           bg=P["bad_bg"], stroke=P["red"], title_size=18, body_size=15)
    d.card("n", 40, 340, 1380, 90, "같은 앱 코드를 PostgreSQL 에서 MySQL 로 옮길 때 \"에러가 나던 곳이 조용히 통과\" 하는 방향이다 (해석)", None,
           bg=P["note_bg"], stroke=P["line"], title_size=15)
    d.save()


def three_strategies():
    d = Diagram("blog06-three-strategies", 1460, 350, "InnoDB 에서 세 전략 (모두 해석 — 문서 문장에서 이은 것)",
                "MySQL 을 직접 돌려 보지 않았다", out=OUT)
    cs = [("원자 UPDATE", "최신 커밋 행에 적용되고\n행 락으로 줄을 선다\n격리수준(RR · RC)과 무관하게\n안전해 보인다\n영향 행 수로 판정하는 것도 같다", P["ok_bg"], P["green"]),
          ("비관 락", "SELECT ... FOR UPDATE 가\n최신 값을 읽고 잠근다\n\n일반 SELECT 로 읽고 UPDATE\n하면 안 된다 — RR 에서\n일반 SELECT 는 옛 스냅샷", P["rs_bg"], P["orange"]),
          ("낙관 락", "WHERE version = ? 는\n최신 커밋 행에 평가되어\n충돌 시 0 행이 된다\n\nPostgreSQL RR 처럼 40001 로\n먼저 막는 경로가 없다\n(직접 확인하지 않았다)", P["as_bg"], P["front"])]
    for i, (t, b, bg, st) in enumerate(cs):
        d.card(f"c{i}", 40 + i * 470, 110, 440, 200, t, b, bg=bg, stroke=st, title_size=18, body_size=15)
    d.save()


def locks_index():
    d = Diagram("blog06-locks-index", 1460, 440, "락의 범위 — 인덱스가 중요하다 (17.7.3)",
                "UPDATE ... WHERE ... 는 검색이 만나는 모든 인덱스 레코드에 배타 next-key 락을 건다", out=OUT)
    d.card("a", 40, 110, 680, 170, "유니크 인덱스(PK)로 유일한 행을 찾는다",
           "인덱스 레코드 락만 필요하다\n\n재고 테이블에서 sku 로 찾는 UPDATE 가\nPK / 유니크 인덱스를 타야 한다 (해석)",
           bg=P["ok_bg"], stroke=P["green"], title_size=18, body_size=15)
    d.card("b", 760, 110, 660, 170, "적합한 인덱스가 없어 테이블 전체를 스캔한다",
           "\"every row of the table becomes locked,\nwhich in turn blocks all inserts by other users\"\n\nWHERE 조건이 행을 제외하더라도\n스캔된 모든 인덱스 레코드에 락이 걸린다",
           bg=P["bad_bg"], stroke=P["red"], title_size=18, body_size=15)
    d.card("n", 40, 310, 1380, 100, "PostgreSQL 의 \"행 락은 그 행만\" 이 InnoDB 에서는 인덱스 설계에 달려 있다",
           "인덱스 없는 조건으로 차감하면 락이 한 행이 아니라 스캔한 범위로 번진다\n한 SKU 차감이 다른 SKU 를 막는 장애로 이어진다",
           bg=P["note_bg"], stroke=P["line"], title_size=16, body_size=15)
    d.save()


def sqlstate():
    d = Diagram("blog06-sqlstate", 1460, 430, "SQLSTATE 40001 — 같은 코드, 다른 상황",
                "코드만 보고 같은 상황이라고 읽지 않는다", out=OUT)
    d.card("p", 40, 110, 680, 160, "PostgreSQL", "REPEATABLE READ 에서 스냅샷 이후 바뀐 행을 고치려 할 때\n40001 could not serialize access due to concurrent update",
           bg=P["as_bg"], stroke=P["front"], title_size=18, body_size=15)
    d.card("m", 760, 110, 660, 160, "MySQL", "InnoDB 데드락(에러 1213, ER_LOCK_DEADLOCK)의\nSQLSTATE 로도 쓰인다\n\"직렬화 실패\" 상황의 에러가 있다는 뜻이 아니다",
           bg=P["rs_bg"], stroke=P["orange"], title_size=18, body_size=15)
    d.card("n", 40, 300, 1380, 90, "MySQL 에서 40001 은 데드락에도 쓰인다 — InnoDB 문서는 DML 이 방금 커밋된 행에 영향을 줄 수 있다고 한다", None,
           bg=P["note_bg"], stroke=P["line"], title_size=15)
    d.save()


if __name__ == "__main__":
    for f in (two_worlds, trap, pg_vs_innodb, three_strategies, locks_index, sqlstate):
        f()
    finish()
