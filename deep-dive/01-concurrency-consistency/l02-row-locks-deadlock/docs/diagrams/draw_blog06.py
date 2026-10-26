#!/usr/bin/env python3
"""01.02 블로그판 06 그림. 실행: python3 -I docs/diagrams/draw_blog06.py (레슨 폴더에서)"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[4] / "tools"))
from diagram import Diagram, P, finish  # noqa: E402

OUT = pathlib.Path(__file__).parent


def table(d, x, y, widths, header, rows, hh=44, rh=64, size=14, hl=None):
    xs = [x]
    for w in widths[:-1]:
        xs.append(xs[-1] + w + 10)
    for c, t in enumerate(header):
        d.pill(f"{d.name}-h{c}", xs[c], y, widths[c], hh, t, P["note_bg"], P["line"], size=14)
    for r, row in enumerate(rows):
        yy = y + hh + 12 + r * (rh + 10)
        for c, t in enumerate(row):
            bg, st = P["white"], P["line"]
            if hl and (r, c) in hl:
                bg, st = hl[(r, c)]
            d.pill(f"{d.name}-c{r}-{c}", xs[c], yy, widths[c], rh, t, bg, st, size=size)


def intro():
    d = Diagram("blog06-intro", 1400, 560, "락 코드를 다른 DB 로 옮길 때 틀리기 쉬운 세 곳",
                "(해석 — 실무 경험칙이 아니라 이 글이 비교한 차이를 세 갈래로 묶은 것)", out=OUT)
    cards = [("1. 타임아웃 기본값", "락 대기 무한정\n(lock_timeout = 0)", "innodb_lock_wait_timeout\n기본 50 초"),
             ("2. 실패 후 상태", "에러가 트랜잭션을\n중단 상태로 만든다", "기본은 현재 문장만 롤백\n(트랜잭션은 열려 있다)"),
             ("3. 락이 걸리는 단위", "존재하는 행\n(갭 락 개념이 없다 — 해석)", "인덱스 레코드\n+ 갭 · 넥스트키 락")]
    for i, (t, pg, my) in enumerate(cards):
        x = 40 + i * 450
        d.card(f"c{i}", x, 110, 420, 380, t, None, bg=P["note_bg"], stroke=P["line"], title_size=19)
        d.card(f"p{i}", x + 16, 170, 388, 130, "PostgreSQL 16", pg, bg=P["as_bg"], stroke=P["front"], title_size=14, body_size=14)
        d.card(f"m{i}", x + 16, 330, 388, 130, "MySQL 8.0 InnoDB", my, bg=P["todo_bg"], stroke=P["orange"], title_size=14, body_size=14)
    d.save()


def jpa_sql():
    d = Diagram("blog06-jpa-sql", 1400, 600, "PESSIMISTIC_WRITE 는 호출 방식에 따라 다른 락 절이 된다",
                "Hibernate 6.4.10 · 6.6.58 을 PostgreSQL 16 에 붙여 show_sql 로 읽은 결과 (실측: 2026-10-13)", out=OUT)
    rows = [("PESSIMISTIC_WRITE\nem.find · JPQL setLockMode", "… where s1_0.id=? for no key update\n(for update 가 아니다)"),
            ("PESSIMISTIC_WRITE\nem.lock (이미 읽은 엔티티)", "select id from Stock where id=? and version=?\nfor update  — 여기만 for update"),
            ("PESSIMISTIC_READ\nem.find · JPQL", "for share"),
            ("PESSIMISTIC_READ\nem.lock", "select id from Stock where id=? and version=?\nfor share")]
    d.pill("h0", 40, 100, 440, 44, "요청", P["note_bg"], P["line"], size=14)
    d.pill("h1", 490, 100, 870, 44, "PostgreSQL 16 에서 나간 락 절", P["note_bg"], P["line"], size=14)
    for i, (a, b) in enumerate(rows):
        y = 156 + i * 90
        hot = P["todo_bg"], P["orange"]
        d.pill(f"a{i}", 40, y, 440, 80, a, P["white"], P["line"], size=14)
        bg, st = (hot if i == 1 else (P["white"], P["line"]))
        d.pill(f"b{i}", 490, y, 870, 80, b, bg, st, size=14, mono=True)
    d.card("n", 40, 530, 1320, 50, "같은 PESSIMISTIC_WRITE 가 find · JPQL 이면 FOR NO KEY UPDATE, em.lock 이면 FOR UPDATE — 호출 방식에 따라 락 모드가 달라진다",
           None, bg=P["as_bg"], stroke=P["front"], title_size=15)
    d.save()


def timeout_hint():
    d = Diagram("blog06-timeout-hint", 1400, 560, "jakarta.persistence.lock.timeout 힌트는 SQL 에 어떻게 반영되나",
                "PESSIMISTIC_WRITE + find · JPQL 기준 (실측: Hibernate 6.4.10 · 6.6.58 · 7.4.13, 2026-10-13)", out=OUT)
    widths = [260, 520, 520]
    rows = [("힌트 0", "for no key update nowait", "for no key update of s1_0 nowait"),
            ("힌트 -2", "for no key update skip locked", "for no key update of s1_0 skip locked"),
            ("힌트 3000 (양수)", "for no key update\n절 그대로, 추가 SQL 도 없다 — 무한 대기", "select current_setting('lock_timeout', true)\n→ set local lock_timeout = 3000 → 잠금 SELECT\n→ set local lock_timeout = 0"),
            ("힌트 없음", "for no key update", "(양수와 같은 경로는 아님 — 힌트 없음)")]
    d.pill("h0", 40, 100, widths[0], 44, "힌트 값", P["note_bg"], P["line"], size=14)
    d.pill("h1", 310, 100, widths[1], 44, "6.4 · 6.6", P["note_bg"], P["line"], size=14)
    d.pill("h2", 840, 100, widths[2], 44, "7.4.13 (참고)", P["note_bg"], P["line"], size=14)
    for i, (a, b, c) in enumerate(rows[:3]):
        y = 156 + i * 110
        hot = (P["bad_bg"], P["red"]) if i == 2 else (P["white"], P["line"])
        d.pill(f"a{i}", 40, y, widths[0], 100, a, P["white"], P["line"], size=14)
        d.pill(f"b{i}", 310, y, widths[1], 100, b, hot[0], hot[1], size=13, mono=True)
        d.pill(f"c{i}", 840, y, widths[2], 100, c, P["ok_bg"] if i == 2 else P["white"], P["green"] if i == 2 else P["line"], size=12, mono=True)
    d.card("n", 40, 500, 1320, 50, "6.x 에서 \"JPA 힌트로 3 초 대기\" 는 PostgreSQL 에서 안 먹고 무한 대기다 — SET LOCAL lock_timeout 을 직접 걸거나 7.x 로 올려야 한다",
           None, bg=P["bad_bg"], stroke=P["red"], title_size=14)
    d.save()


def innodb_locks():
    d = Diagram("blog06-innodb-locks", 1400, 620, "InnoDB 의 락은 인덱스 레코드와 그 사이 간격에 걸린다",
                "인덱스 레코드 10 · 20 · 30 (MySQL 8.0 · 17.7.1 InnoDB Locking)", out=OUT)
    recs = [(160, "10"), (560, "20"), (960, "30")]

    def row(y, label):
        d.text(40, y - 6, label, 16, P["ink"], weight=700)
        for x0, x1 in ((40, 160), (280, 560), (680, 960), (1080, 1360)):
            d.line([(x0, y + 50), (x1, y + 50)], P["line"], dashed=False, sw=2)
        for x, n in recs:
            d.pill(f"{label}-{n}", x, y + 20, 120, 60, n, P["white"], P["ink"], size=17)

    row(110, "레코드 락")
    d.rect(None, 548, 122, 144, 76, P["bad_bg"], P["red"], dashed=True)
    d.pill("rl20", 560, 130, 120, 60, "20", P["bad_bg"], P["red"], size=17)
    d.text(710, 124, "인덱스 레코드 20 만 잠근다", 14, P["red"])
    row(260, "갭 락")
    d.rect(None, 292, 274, 256, 72, P["bad_bg"], P["red"], dashed=True)
    d.text(420, 356, "10 과 20 사이 간격 (레코드 자체는 아님)", 14, P["red"], align="center")
    row(410, "넥스트키 락")
    d.rect(None, 292, 424, 400, 72, P["bad_bg"], P["red"], dashed=True)
    d.pill("nk20", 560, 430, 120, 60, "20", P["bad_bg"], P["red"], size=17)
    d.text(492, 506, "레코드 20 + 그 앞의 간격", 14, P["red"], align="center")
    d.card("n", 40, 545, 1320, 60, "갭 락은 범위 조건 잠금으로 팬텀을 막는 데 쓰인다. READ COMMITTED 에서는 검색 · 인덱스 스캔의 갭 락이 꺼지고 외래키 검사 · 중복 키 검사에만 쓰인다",
           None, bg=P["note_bg"], stroke=P["line"], title_size=14)
    d.save()


def wait_timeout():
    d = Diagram("blog06-wait-timeout", 1400, 560, "락 대기 초과 뒤, 트랜잭션은 어떻게 되나",
                "같은 상황에서 두 엔진은 반대 방향이다", out=OUT)
    d.rect(None, 30, 100, 670, 440, P["white"], P["line"], dashed=True)
    d.text(50, 112, "PostgreSQL 16", 18, P["front"], weight=700)
    d.pill("p1", 60, 160, 610, 70, "lock_timeout 초과 (기본은 꺼짐 — 무한 대기)", P["note_bg"], P["line"], size=14)
    d.pill("p2", 60, 260, 610, 70, "에러가 트랜잭션을 중단 상태로 만든다", P["bad_bg"], P["red"], size=15)
    d.pill("p3", 60, 360, 610, 70, "이어 쓰면 25P02 — ROLLBACK 만 의미가 있다", P["bad_bg"], P["red"], size=15)
    d.arrow([(365, 230), (365, 260)], P["muted"]); d.arrow([(365, 330), (365, 360)], P["muted"])
    d.text(60, 455, "문장 단위 복구는 SAVEPOINT 를 앱이 명시한다 (03 글)", 14, P["muted"])
    d.rect(None, 720, 100, 650, 440, P["white"], P["line"], dashed=True)
    d.text(740, 112, "MySQL 8.0 InnoDB", 18, P["orange"], weight=700)
    d.pill("m1", 750, 160, 590, 70, "innodb_lock_wait_timeout (기본 50 초) 초과", P["note_bg"], P["line"], size=14)
    d.pill("m2", 750, 260, 590, 70, "현재 문장만 롤백 — 트랜잭션은 열려 있다", P["todo_bg"], P["orange"], size=15)
    d.pill("m3", 750, 360, 590, 70, "앞선 락 · 변경이 남은 채 이어질 수 있다", P["todo_bg"], P["orange"], size=15)
    d.arrow([(1045, 230), (1045, 260)], P["muted"]); d.arrow([(1045, 330), (1045, 360)], P["muted"])
    d.text(750, 455, "전체 롤백은 --innodb-rollback-on-timeout 로 서버 시작 시 지정", 14, P["muted"])
    d.text(750, 480, "문서: 대기 초과는 문장을 재시도, rollback-on-timeout 이면 트랜잭션 전체를 재시도", 14, P["muted"])
    d.save()


def compare_table():
    d = Diagram("blog06-compare", 1400, 680, "기다림 · 데드락의 기본값 비교",
                "PostgreSQL 16 vs MySQL 8.0 InnoDB", out=OUT)
    widths = [180, 540, 580]
    rows = [("락 대기 기본", "무한정 (lock_timeout = 0)", "innodb_lock_wait_timeout 50 초"),
            ("대기 초과 시", "에러가 트랜잭션을 중단 상태로", "현재 문장만 롤백 (전체는 rollback-on-timeout)"),
            ("데드락", "감지(deadlock_timeout 후) · 희생자 예측 불가", "감지 기본 ON · 작은 트랜잭션(변경 행 수)을 롤백하려 한다"),
            ("데드락 후", "트랜잭션 전체 재시도", "트랜잭션 전체를 롤백, 전체 재시도"),
            ("감지 끄기", "해당 없음 (deadlock_timeout 은 지연)", "innodb_deadlock_detect (전역, 동적)"),
            ("데드락 확인", "서버 로그 (deadlock detected + DETAIL)", "SHOW ENGINE INNODB STATUS (최근 하나) · innodb_print_all_deadlocks")]
    table(d, 40, 100, widths, ["항목", "PostgreSQL 16", "MySQL 8.0 InnoDB"], rows, rh=72, size=13)
    d.save()


def errors():
    d = Diagram("blog06-errors", 1400, 640, "같은 일, 다른 에러 번호 — SQLSTATE 로 같은 처리를 하면 안 된다",
                "PostgreSQL 은 SQLSTATE, MySQL 은 에러 번호 + SQLSTATE", out=OUT)
    widths = [260, 500, 520]
    rows = [("락 대기 초과", "55P03 (NOWAIT · lock_timeout)", "1205 ER_LOCK_WAIT_TIMEOUT (HY000)"),
            ("데드락", "40P01 deadlock_detected", "1213 ER_LOCK_DEADLOCK (40001)"),
            ("NOWAIT 실패", "55P03", "3572 (HY000, \"Do not wait for lock.\")"),
            ("statement_timeout", "57014 query_canceled", "(이 레슨은 확인하지 않음)"),
            ("중단된 트랜잭션에 문장", "25P02", "(이 레슨은 확인하지 않음)")]
    table(d, 40, 100, widths, ["상황", "PostgreSQL 16", "MySQL 8.0"], rows, rh=60, size=14,
          hl={(1, 1): (P["bad_bg"], P["red"]), (1, 2): (P["bad_bg"], P["red"])})
    d.card("n", 40, 520, 1320, 80, "40001 만 재시도 대상으로 잡은 코드는 PostgreSQL 에서 40P01 을 놓친다 (해석)",
           "MySQL 의 데드락은 SQLSTATE 40001, PostgreSQL 의 데드락은 40P01 이다", bg=P["todo_bg"], stroke=P["orange"], title_size=15, body_size=14)
    d.save()


def spring_map():
    d = Diagram("blog06-spring-map", 1400, 520, "락 실패가 Spring 에서 어떤 예외가 되나 (PostgreSQL 16)",
                "Spring Boot 3.5.16 · Spring 6.2.19 · Hibernate 6.6.53 · pgjdbc 42.7.11 · PostgreSQL 16.14 (실측: 2026-10-13)", out=OUT)
    widths = [260, 560, 480]
    rows = [("55P03\nNOWAIT · lock_timeout", "UncategorizedSQLException\n(번역 안 됨, SQLState 는 메시지 · cause 에)", "PessimisticLockingFailureException\n(← Hibernate PessimisticLockException)"),
            ("40P01\n데드락", "PessimisticLockingFailureException", "CannotAcquireLockException"),
            ("25P02\n이미 중단됨", "UncategorizedSQLException", "JpaSystemException")]
    table(d, 40, 100, widths, ["SQLSTATE", "JdbcTemplate", "JPA · Spring Data"], rows, rh=84, size=13)
    d.text(40, 470, "57014 · 25P02 는 별도로 재지 않았다 (25P02 는 05-spring-jpa-mapping.md 에서 확인). 표 · 상위 갈래는 ../../docs/05-spring-jpa-mapping.md", 13, P["muted"])
    d.save()


if __name__ == "__main__":
    for f in (intro, jpa_sql, timeout_hint, innodb_locks, wait_timeout, compare_table, errors, spring_map):
        f()
    finish()
