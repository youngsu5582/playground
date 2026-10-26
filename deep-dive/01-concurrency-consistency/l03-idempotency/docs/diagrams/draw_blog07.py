#!/usr/bin/env python3
"""01.03 블로그판 07 그림. 실행: python3 -I docs/diagrams/draw_blog07.py (레슨 폴더에서)"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[4] / "tools"))
from diagram import Diagram, P, finish  # noqa: E402

OUT = pathlib.Path(__file__).parent


def intro():
    d = Diagram("blog07-intro", 1360, 520, "앱에서 멱등 키를 선점하는 두 갈래",
                "같은 \"이미 있다\" 를 에러로 알아내느냐, 에러 없이 알아내느냐", out=OUT)
    d.text(40, 112, "1  에러로 알아낸다", 17, P["red"], weight=700)
    d.text(720, 112, "2  에러 없이 알아낸다 (이 레슨)", 17, P["green"], weight=700)
    left = [("INSERT", "키 행을 넣는다"), ("유니크 위반 예외를 catch", "예외가 났다 = 이미 있다"),
            ("\"이미 있다\" 로 해석", "기존 행을 조회하려 한다")]
    for i, (t, b) in enumerate(left):
        d.card(f"l{i}", 40, 140 + i * 110, 600, 90, t, b, bg=P["bad_bg"], stroke=P["red"], title_size=15, body_size=14)
        if i:
            d.arrow([d.anchor(f"l{i-1}", "s", 0.2), d.anchor(f"l{i}", "n", 0.2)], P["red"], start=f"l{i-1}", end=f"l{i}")
    d.card("lw", 40, 470, 600, 40, "문서 05 의 중단 상태 문제가 따라온다", None, bg=P["todo_bg"], stroke=P["orange"], title_size=14)
    right = [("ON CONFLICT DO NOTHING", "중복이어도 에러가 나지 않는다"), ("영향 행 수를 본다", "JDBC executeUpdate() 의 반환값\n1 = 내가 선점, 0 = 이미 있다")]
    for i, (t, b) in enumerate(right):
        d.card(f"r{i}", 720, 140 + i * 130, 620, 100, t, b, bg=P["ok_bg"], stroke=P["green"], title_size=15, body_size=14)
    d.arrow([d.anchor("r0", "s", 0.2), d.anchor("r1", "n", 0.2)], P["green"], start="r0", end="r1")
    d.card("rn", 720, 410, 620, 90, "트랜잭션이 중단되지 않는다", "그대로 SELECT 를 이어 할 수 있다",
           bg=P["ok_bg"], stroke=P["green"], title_size=15, body_size=14)
    d.save()


def translation():
    d = Diagram("blog07-translation", 1400, 640, "PostgreSQL 의 23505 가 Spring 예외가 되는 길",
                "두 경로 모두 DataIntegrityViolationException 아래로 모인다 (실측: 스크래치 프로브, 2026-10-13)", out=OUT)
    d.card("pg", 40, 110, 420, 80, "PostgreSQL", "유니크 위반 SQLSTATE 23505", bg=P["note_bg"], stroke=P["muted"], title_size=16, body_size=14)
    d.card("jdbc", 560, 110, 560, 80, "JDBC 드라이버 (pgjdbc)", "PSQLException · SQLException#getSQLState() = \"23505\"",
           bg=P["as_bg"], stroke=P["front"], title_size=16, body_size=14)
    d.arrow([d.anchor("pg", "e"), d.anchor("jdbc", "w")], P["muted"], "에러를\n보낸다", start="pg", end="jdbc")
    d.card("jt", 40, 270, 640, 110, "JdbcTemplate 경로", "SQLErrorCodeSQLExceptionTranslator 가 sql-error-codes.xml 을 본다\nPostgreSQL 항목: duplicateKeyCodes = 21000, 23505",
           bg=P["as_bg"], stroke=P["front"], title_size=16, body_size=14)
    d.card("jp", 740, 270, 620, 110, "JPA (Hibernate) · Spring Data 경로", "Hibernate ConstraintViolationException\n(cause: PSQLException 23505)",
           bg=P["bff_bg"], stroke=P["back"], title_size=16, body_size=14)
    d.arrow([d.anchor("jdbc", "s", 0.25), (700, 230), (360, 230), d.anchor("jt", "n", 0.5)], P["front"], None, start="jdbc", end="jt")
    d.arrow([d.anchor("jdbc", "s", 0.75), (980, 230), (1050, 230), d.anchor("jp", "n", 0.5)], P["back"], None, start="jdbc", end="jp")
    d.card("r1", 40, 450, 640, 70, "DuplicateKeyException", None, bg=P["ok_bg"], stroke=P["green"], title_size=17)
    d.card("r2", 740, 450, 620, 70, "DataIntegrityViolationException", "DuplicateKeyException 이 아니다", bg=P["todo_bg"], stroke=P["orange"], title_size=17, body_size=14)
    d.arrow([d.anchor("jt", "s"), d.anchor("r1", "n")], P["green"], "번역", start="jt", end="r1")
    d.arrow([d.anchor("jp", "s"), d.anchor("r2", "n")], P["orange"], "번역", start="jp", end="r2")
    d.card("n", 40, 560, 1320, 60, "DuplicateKeyException 은 DataIntegrityViolationException 을 상속한다",
           "두 결과 모두 DataIntegrityViolationException 의 하위라서, 상위로 잡으면 두 경로를 함께 잡는다",
           bg=P["note_bg"], stroke=P["line"], title_size=15, body_size=14)
    d.save()


def error_table():
    d = Diagram("blog07-error-table", 1400, 610, "SQLSTATE 별 Spring 예외 — 두 경로의 실측",
                "Spring Boot 3.5.16 · Spring 6.2.19 · Hibernate 6.6.53 · pgjdbc 42.7.11 · PostgreSQL 16.14, 2026-10-13, 스크래치 프로브", out=OUT)
    d.pill("h0", 40, 110, 160, 50, "SQLSTATE", P["note_bg"], P["line"], size=15)
    d.pill("h1", 210, 110, 450, 50, "JdbcTemplate 경로", P["as_bg"], P["front"], size=15)
    d.pill("h2", 670, 110, 690, 50, "JPA (Hibernate) · Spring Data 경로", P["bff_bg"], P["back"], size=15)
    rows = [("23505", "DuplicateKeyException", "DataIntegrityViolationException\n(cause: Hibernate ConstraintViolationException ← PSQLException 23505)", "ok"),
            ("40001", "CannotAcquireLockException", "CannotAcquireLockException (← Hibernate LockAcquisitionException)", None),
            ("40P01", "PessimisticLockingFailureException", "CannotAcquireLockException", None),
            ("55P03", "UncategorizedSQLException (번역되지 않는다)", "PessimisticLockingFailureException\n(← Hibernate PessimisticLockException)", "bad")]
    for i, (c, a, b, k) in enumerate(rows):
        y = 175 + i * 92
        d.pill(f"c{i}", 40, y, 160, 80, c, P["note_bg"], P["line"], size=16, mono=True)
        d.pill(f"a{i}", 210, y, 450, 80, a, P["todo_bg"] if k == "bad" else P["white"], P["orange"] if k == "bad" else P["line"], size=14)
        d.pill(f"b{i}", 670, y, 690, 80, b, P["white"], P["line"], size=14)
    d.text(40, 560, "23505 는 JPA 경로에서 DuplicateKeyException 이 아니다. 네 코드 중 JdbcTemplate 경로에서 번역되지 않는 것은 55P03 뿐이다", 14, P["muted"])
    d.save()


def rollback_mark():
    d = Diagram("blog07-rollback-mark", 1360, 520, "예외가 @Transactional 밖으로 나오는가, 안에서 삼켜지는가",
                "Spring 은 런타임(언체크) 예외를 롤백 대상으로 표시하고, 체크 예외는 기본 설정에서 롤백하지 않는다", out=OUT)
    d.pill("hs", 280, 110, 480, 44, "Spring 트랜잭션 인프라가 아는 것", P["as_bg"], P["front"], size=15)
    d.pill("hd", 800, 110, 520, 44, "DB 쪽 트랜잭션의 상태", P["bff_bg"], P["back"], size=15)
    d.card("q1", 40, 180, 220, 130, "예외가\n메서드 밖으로\n나온다", None, bg=P["note_bg"], stroke=P["muted"], title_size=15)
    d.card("s1", 280, 180, 480, 130, "RuntimeException 계열이다", "DuplicateKeyException 도 이 계열이다\n→ 롤백 대상으로 표시한다",
           bg=P["ok_bg"], stroke=P["green"], title_size=15, body_size=14)
    d.card("d1", 800, 180, 520, 130, "롤백된다", "(문서 05) 앞서 한 쓰기도 함께", bg=P["ok_bg"], stroke=P["green"], title_size=15, body_size=14)
    d.card("q2", 40, 340, 220, 130, "예외를 안에서\n잡아 삼킨다", None, bg=P["note_bg"], stroke=P["muted"], title_size=15)
    d.card("s2", 280, 340, 480, 130, "어디서 잡았나에 따라 다르다", "JdbcTemplate 예외를 직접 잡음 → Spring 은 모른다\n다른 빈의 @Transactional · JPA flush 실패 →\nrollback-only 표시 (실측: 트랙 05)", bg=P["todo_bg"], stroke=P["orange"], title_size=15, body_size=13)
    d.card("d2", 800, 340, 520, 130, "커밋이 조용히 롤백되거나 예외가 난다", "모를 때: DB 쪽만 중단 상태 → 다음 문장 거절(문서 05)\n· 커밋은 예외 없이 롤백된다\n표시됐을 때: 바깥 커밋에서 UnexpectedRollbackException", bg=P["bad_bg"], stroke=P["red"], title_size=15, body_size=13)
    d.arrow([d.anchor("q1", "e"), d.anchor("s1", "w")], P["muted"], start="q1", end="s1")
    d.arrow([d.anchor("s1", "e"), d.anchor("d1", "w")], P["green"], start="s1", end="d1")
    d.arrow([d.anchor("q2", "e"), d.anchor("s2", "w")], P["muted"], start="q2", end="s2")
    d.arrow([d.anchor("s2", "e"), d.anchor("d2", "w")], P["red"], start="s2", end="d2")
    d.save()


def jpa_save():
    d = Diagram("blog07-jpa-save", 1400, 620, "JPA save() 와 멱등 키 — 확인한 것과 모르는 것",
                "Spring Data JPA 문서에서 확인한 범위까지만. 수동 할당 식별자면 merge 경로로 간다", out=OUT)
    d.card("s", 40, 120, 300, 90, "save(entity)", "CrudRepository", bg=P["as_bg"], stroke=P["front"], title_size=17, body_size=14)
    d.card("n", 440, 110, 460, 130, "새 엔티티인가?", "Version 속성이 있으면 null 일 때 새것\n없으면 식별자 속성이 null 일 때 새것",
           bg=P["note_bg"], stroke=P["muted"], title_size=16, body_size=14)
    d.arrow([d.anchor("s", "e"), d.anchor("n", "w")], P["muted"], start="s", end="n")
    d.card("p", 1000, 110, 340, 60, "persist(…)", "새것이면", bg=P["ok_bg"], stroke=P["green"], title_size=16, body_size=13)
    d.card("m", 1000, 190, 340, 60, "merge(…)", "새것이 아니면", bg=P["todo_bg"], stroke=P["orange"], title_size=16, body_size=13)
    d.arrow([d.anchor("n", "e", 0.3), d.anchor("p", "w", 0.5)], P["green"], None, start="n", end="p")
    d.arrow([d.anchor("n", "e", 0.7), d.anchor("m", "w", 0.5)], P["orange"], None, start="n", end="m")
    d.card("k", 40, 320, 600, 150, "멱등 키를 @Id 로 쓰면", "수동 할당 식별자 · version 없음\n→ 식별자가 항상 non-null → 새것으로 판정되지 않는다\n→ 기본값으로 merge 를 부르게 된다\n(문서: Persistable 로 isNew() 를 직접 정하는 방법도 소개)",
           bg=P["bff_bg"], stroke=P["back"], title_size=16, body_size=14)
    d.card("q", 700, 320, 640, 150, "확인하지 못한 것", "merge 가 내부에서 SELECT 를 먼저 내는지\n그래서 SELECT → INSERT 틈이 생기는지\n(Spring Data 문서에 그 서술이 없다)",
           bg=P["todo_bg"], stroke=P["orange"], title_size=16, body_size=14)
    d.arrow([d.anchor("k", "e"), d.anchor("q", "w")], P["orange"], "그다음은?", start="k", end="q")
    d.card("r", 40, 510, 1300, 80, "그래서 JPA save 를 멱등 선점에 쓰는 것은 추천하지 않는다 (해석)",
           "선점은 JdbcTemplate/네이티브 쿼리의 INSERT … ON CONFLICT DO NOTHING + 영향 행 수로 하고, JPA 엔티티는 선점 뒤의 읽기 · 저장에 쓴다",
           bg=P["ok_bg"], stroke=P["green"], title_size=15, body_size=14)
    d.save()


def mysql_tools():
    d = Diagram("blog07-mysql-tools", 1360, 440, "PostgreSQL 과 MySQL 8.0 의 선점 도구",
                "같은 일을 하는 문장이 있지만 무시하는 범위가 다르다", out=OUT)
    d.pill("h0", 40, 110, 220, 50, "", P["white"], P["white"], size=14)
    d.pill("h1", 270, 110, 480, 50, "PostgreSQL", P["as_bg"], P["front"], size=16)
    d.pill("h2", 760, 110, 560, 50, "MySQL 8.0", P["bff_bg"], P["back"], size=16)
    rows = [("중복이면 무시", "ON CONFLICT DO NOTHING", "INSERT IGNORE", None),
            ("중복이면 갱신", "ON CONFLICT (key) DO UPDATE", "INSERT … ON DUPLICATE KEY UPDATE", None),
            ("에러 범위", "그 충돌만", "IGNORE 는 중복 키 외 \"무시 가능한 에러\" 를\n경고로 바꾼다", "bad")]
    for i, (a, b, c, k) in enumerate(rows):
        y = 175 + i * 92
        d.pill(f"a{i}", 40, y, 220, 80, a, P["note_bg"], P["line"], size=15)
        d.pill(f"b{i}", 270, y, 480, 80, b, P["ok_bg"] if k else P["white"], P["green"] if k else P["line"], size=15)
        d.pill(f"c{i}", 760, y, 560, 80, c, P["bad_bg"] if k else P["white"], P["red"] if k else P["line"], size=15)
    d.save()


def odku_rows():
    d = Diagram("blog07-odku-rows", 1360, 520, "ON DUPLICATE KEY UPDATE 의 영향 행 수는 1 · 2 · 0",
                "\"1 이면 내가 삽입\" 판정은 PostgreSQL 과 같지만, 갱신이 2 라서 해석을 바꿔야 한다", out=OUT)
    specs = [("1", "새 행을 삽입했다", "1 이면 내가 선점", P["ok_bg"], P["green"]),
             ("2", "기존 행을 갱신했다", "삽입 아님 — 값이 2 다", P["todo_bg"], P["orange"]),
             ("0", "기존 행을 현재 값으로 설정했다\n(변화 없음)", "CLIENT_FOUND_ROWS 플래그를\n주면 이 경우도 1", P["note_bg"], P["muted"])]
    for i, (n, t, b, bg, st) in enumerate(specs):
        d.pill(f"n{i}", 40 + i * 445, 130, 90, 90, n, bg, st, size=34)
        d.card(f"c{i}", 140 + i * 445, 130, 310, 130, t, b, bg=bg, stroke=st, title_size=15, body_size=13)
    d.card("pg", 40, 320, 1300, 70, "PostgreSQL 은 INSERT 0 N", "INSERT 0 N 의 N 이 영향 행 수다 — 값의 의미가 다르다",
           bg=P["as_bg"], stroke=P["front"], title_size=15, body_size=14)
    d.card("n", 40, 420, 1300, 70, "유니크 키가 여러 개인 테이블에서는 한 행만 갱신된다",
           "a=1 OR b=2 와 일치하는 행이 여럿이어도 한 행만 — 문서는 여러 유니크 인덱스가 있는 테이블에 이 절을 쓰지 말라고 권한다",
           bg=P["note_bg"], stroke=P["line"], title_size=15, body_size=14)
    d.save()


def innodb_locks():
    d = Diagram("blog07-innodb-locks", 1400, 760, "InnoDB 중복 키 에러 경로의 공유 락과 교착 (문서의 세션 3 개 예)",
                "같은 행을 여러 세션이 동시에 INSERT 하다가 앞선 세션이 롤백하는 경우", out=OUT)
    xs = [40, 500, 960]
    for i, t in enumerate(["세션 1", "세션 2", "세션 3"]):
        d.pill(f"h{i}", xs[i], 100, 400, 40, t, P["as_bg"] if i == 0 else P["bff_bg"], P["front"] if i == 0 else P["back"], size=15)
    d.card("a1", xs[0], 170, 400, 100, "INSERT (행 1)", "삽입한 행에 배타(exclusive) 레코드 락\n(next-key 락이 아니라 갭 락이 없다)",
           bg=P["as_bg"], stroke=P["front"], title_size=15, body_size=13)
    d.card("a2", xs[1], 300, 400, 100, "INSERT (같은 행)", "기다리던 세션 — 중복 키 에러 경로:\n중복된 인덱스 레코드에 공유(shared) 락을 건다",
           bg=P["bff_bg"], stroke=P["back"], title_size=15, body_size=13)
    d.card("a3", xs[2], 300, 400, 100, "INSERT (같은 행)", "기다리던 세션 — 중복 키 에러 경로:\n중복된 인덱스 레코드에 공유(shared) 락을 건다",
           bg=P["bff_bg"], stroke=P["back"], title_size=15, body_size=13)
    d.card("rb", xs[0], 430, 400, 80, "ROLLBACK", "앞선 세션이 롤백한다", bg=P["note_bg"], stroke=P["muted"], title_size=15, body_size=14)
    d.card("sh", xs[1], 540, 860, 70, "세션 2 · 3 이 공유 락을 함께 얻는다", "기다리던 세션들이 같은 행의 공유 락을 동시에 쥔다",
           bg=P["todo_bg"], stroke=P["orange"], title_size=15, body_size=14)
    d.card("dl", xs[1], 650, 860, 80, "서로 배타 락을 못 얻는다 — 교착 (deadlock)", "각자 배타 락이 필요한데 상대의 공유 락이 막는다",
           bg=P["bad_bg"], stroke=P["red"], title_size=16, body_size=14)
    d.arrow([d.anchor("a1", "s", 0.5), d.anchor("rb", "n", 0.5)], P["muted"], "시간이 지나\n롤백", start="a1", end="rb")
    d.arrow([d.anchor("rb", "e", 0.5), (460, 470), (460, 575), d.anchor("sh", "w", 0.5)], P["orange"], None, start="rb", end="sh")
    d.arrow([d.anchor("sh", "s", 0.5), d.anchor("dl", "n", 0.5)], P["red"], None, start="sh", end="dl")
    d.card("odku", 40, 560, 380, 170, "ON DUPLICATE KEY UPDATE 는", "중복 시 공유 락이 아니라 배타 락\n중복 primary key:\n배타 index-record 락\n중복 unique key: 배타 next-key 락",
           bg=P["ok_bg"], stroke=P["green"], title_size=15, body_size=14)
    d.save()


if __name__ == "__main__":
    for f in (intro, translation, error_table, rollback_mark, jpa_save, mysql_tools, odku_rows, innodb_locks):
        f()
    finish()
