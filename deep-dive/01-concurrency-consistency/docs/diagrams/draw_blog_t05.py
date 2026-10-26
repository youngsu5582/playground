#!/usr/bin/env python3
"""01 트랙 블로그판 05 (Spring · JPA) 그림. 실행: python3 -I docs/diagrams/draw_blog_t05.py (트랙 폴더에서)"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from blog_common import Diagram, P, finish, tw, kc, vchain, hchain, sequence, matrix, new, card_h, ARROW  # noqa: E402


def path():
    d = hchain("blog-t05-path", "DB 의 SQLSTATE 가 우리 코드의 예외가 되는 길",
               "(실측: spring-probe) 40001 의 예 — JdbcTemplate 은 Hibernate 단계가 없고, JPA 경로는 cause 사슬이 길다",
               [("PostgreSQL", "SQLSTATE 40001\n(직렬화 실패)", "a"),
                ("pgjdbc", "PSQLException", "b"),
                ("Hibernate\n(JPA 경로만)", "LockAcquisitionException", "warn"),
                ("Spring 번역", "CannotAcquireLockException", "ok"),
                ("우리 코드", "catch 에서 받는다", "w")],
               labels=("", "", "", ""), gap=30, h=150, top=120, extra=190)
    d.card("n", 40, 330, 1320, 150, "읽는 법",
           "같은 SQLSTATE 가 경로에 따라 다른 클래스가 된다 (40P01: JDBC PessimisticLockingFailureException / JPA CannotAcquireLockException)\n재시도 판정을 클래스 하나에 걸지 말고 ConcurrencyFailureException 이상의 상위 갈래로 걸거나\ncause 의 SQLException.getSQLState() 로 판정한다 (해석)\n40001 은 커밋 시점에도 난다 — 재시도 루프는 커밋을 포함한 호출 전체를 감싸야 한다",
           bg=P["note_bg"], stroke=P["line"], title_size=16, body_size=14)
    d.save()


def hierarchy():
    d = new("blog-t05-hierarchy", 1440, 720, "예외 계층 — 재시도 후보는 ConcurrencyFailureException 아래다",
            "(실측: 클래스 사슬 출력) 왼쪽이 상위 클래스 — 선은 상위 → 하위. 주황 = 재시도 후보 갈래")

    def box(key, x, y, w, text, kind, h=44, size=13):
        bg, st = kc(kind)
        d.pill(key, x, y, w, h, text, bg, st, size=size)

    def ln(a, b):
        ax, ay, aw, ah = d.boxes[a]
        bx, by, bw, bh = d.boxes[b]
        mx = ax + aw + (bx - ax - aw) / 2
        d.line([(ax + aw, ay + ah / 2), (mx, ay + ah / 2), (mx, by + bh / 2), (bx, by + bh / 2)], P["muted"], dashed=False, sw=1.5)

    box("T", 40, 150, 290, "TransientDataAccessException", "warn")
    box("C", 380, 150, 280, "ConcurrencyFailureException", "warn")
    box("PL", 710, 100, 330, "PessimisticLockingFailureException", "warn")
    box("OL", 710, 330, 330, "OptimisticLockingFailureException", "warn")
    box("c1", 1090, 50, 310, "CannotAcquireLockException", "ok")
    box("c2", 1090, 110, 310, "CannotSerializeTransactionException\n(6.0.3 deprecated)", "note", h=54, size=12)
    box("c3", 1090, 180, 310, "DeadlockLoserDataAccessException\n(6.0.3 deprecated)", "note", h=54, size=12)
    box("o1", 1090, 330, 310, "ObjectOptimisticLockingFailureException", "ok", size=12)
    for a, b in (("T", "C"), ("C", "PL"), ("C", "OL"), ("PL", "c1"), ("PL", "c2"), ("PL", "c3"), ("OL", "o1")):
        ln(a, b)
    box("N", 40, 470, 290, "NonTransientDataAccessException", "note")
    box("DI", 380, 470, 280, "DataIntegrityViolationException", "bad")
    box("DK", 710, 470, 330, "DuplicateKeyException  (JdbcTemplate 23505)", "bad", size=12)
    box("U", 380, 560, 280, "UncategorizedDataAccessException", "note", size=12)
    box("U1", 710, 540, 330, "UncategorizedSQLException  (JDBC 55P03)", "note", size=12)
    box("U2", 710, 600, 330, "JpaSystemException", "note")
    for a, b in (("N", "DI"), ("DI", "DK"), ("N", "U"), ("U", "U1"), ("U", "U2")):
        ln(a, b)
    d.text(1090, 400, "40001 · 40P01(JPA) 는 위쪽,\n23505 는 DataIntegrityViolation 쪽 —\n55P03 은 JDBC 에서 Uncategorized 라\nConcurrencyFailureException 에 안 걸린다", 14, P["muted"])
    d.save()


def when_thrown():
    d = new("blog-t05-when-thrown", 1400, 520, "JPA 에서 예외는 flush · commit 시점에 난다 (23505, 실측)",
            "@Transactional 안에서 save() 가 정상 반환해도 INSERT 는 아직 안 나갔을 수 있다")
    d.text(40, 112, "SEQUENCE id · @Transactional 안", 16, P["front"], weight=700)
    a = [("save()", "정상 반환\n(INSERT 는 아직 안 나감)", "ok"), ("다른 코드", "영속성 컨텍스트에만\n쌓여 있다", "note"),
         ("flush 시점", "flush() · 쿼리 직전 자동 flush\n· 커밋", "warn"), ("INSERT 가 나가며", "DataIntegrityViolation\nException", "bad")]
    for i, (t, b, k) in enumerate(a):
        bg, st = kc(k)
        d.card(f"a{i}", 40 + i * 340, 140, 290, 120, t, b, bg=bg, stroke=st, title_size=16, body_size=14)
    for i in range(3):
        d.arrow([(330 + i * 340, 200), (380 + i * 340, 200)], P["muted"], None, start=f"a{i}", end=f"a{i + 1}")
    d.text(40, 300, "IDENTITY id", 16, P["back"], weight=700)
    b = [("save()", "id 를 얻으려고\n즉시 INSERT", "warn"), ("save() 호출 중", "예외가 난다", "bad")]
    for i, (t, bd, k) in enumerate(b):
        bg, st = kc(k)
        d.card(f"b{i}", 40 + i * 340, 330, 290, 100, t, bd, bg=bg, stroke=st, title_size=16, body_size=14)
    d.arrow([(330, 380), (380, 380)], P["muted"], None, start="b0", end="b1")
    d.card("o", 800, 300, 560, 180, "그 밖의 경우 (실측)",
           "saveAndFlush() · repo.flush()  →  그 호출에서\ntransaction 밖 save()  →  save() 호출 중 (자기 트랜잭션)\nEntityManager.persist + em.flush()  →  번역 안 된 Hibernate\n  ConstraintViolationException (DataAccessException 아님)\nEntityManager.persist 후 커밋만  →  커밋 시 번역됨",
           bg=P["note_bg"], stroke=P["line"], title_size=15, body_size=13)
    d.save()


def lock_sql():
    rows = [("@Lock(PESSIMISTIC_WRITE) + @Query", "select … where i1_0.id=? for no key update"),
            ("위 + @QueryHints(jakarta.persistence.lock.timeout = 0)", "… for no key update nowait"),
            ("findById 를 재선언하고 @Lock(PESSIMISTIC_WRITE)", "… where i1_0.id=? for no key update"),
            ("파생 쿼리 findByCode(code, Sort) + @Lock(PESSIMISTIC_WRITE)", "… where i1_0.code=? order by i1_0.id for no key update"),
            ("@Lock(PESSIMISTIC_READ) + @Query", "… for share"),
            ("락 어노테이션 없음", "잠금 절 없음")]
    d = matrix("blog-t05-lock-sql", "Spring Data @Lock 이 낸 SQL",
               "(실측: spring-probe, Hibernate 6.6.53 · PostgreSQLDialect, show-sql) FOR UPDATE 가 아니라 FOR NO KEY UPDATE 다 — 이 환경 한정",
               ["PostgreSQL 에 나간 SQL"],
               [(a, [(b, "ok" if "no key" in b else ("a" if "share" in b else "note"))]) for a, b in rows],
               w=1400, first_w=620, row_h=52, size=14)
    d.save()


def rollback_only():
    d = matrix("blog-t05-rollback-only", "예외를 잡고 계속하면 — 세 경로의 결과",
               "(실측: spring-probe) 바깥 @Transactional 메서드가 예외를 잡고 정상 반환 — 같은 트랜잭션에서 앞서 keep 행을 INSERT 해 둔 뒤 실패시킴",
               ["잡은 뒤 Spring 의 상태", "바깥 커밋 결과", "keep 행"],
               [("안쪽이 다른 빈의 @Transactional\n메서드(프록시 경계)에서 예외", [("rollbackOnly = true", "warn"), ("UnexpectedRollbackException", "bad"), ("롤백됨", "bad")]),
                ("EntityManager.flush() 직접 호출에서\n예외 후 catch", [("rollbackOnly = true\n(실패한 엔티티는 컨텍스트에 그대로)", "warn"), ("UnexpectedRollbackException", "bad"), ("롤백됨", "bad")]),
                ("JdbcTemplate 호출에서 예외 후 catch\n(프록시 경계 없음)", [("rollbackOnly = false\nSpring 은 모른다", "note"), ("예외 없이 반환", "bad"), ("롤백됨", "bad")])],
               w=1400, first_w=420, row_h=88, size=14,
               notes="중단된 뒤 다음 쿼리는 전부 25P02 로 실패한다 — JDBC: UncategorizedSQLException · JPA: JpaSystemException")
    d.save()


def silent_rollback():
    d = sequence("blog-t05-silent-rollback", "JDBC 경로의 침묵 롤백",
                 "(실측: spring-probe) 예외를 삼킨 메서드가 정상 반환하고, 호출자는 성공으로 안다",
                 [("서비스 메서드", "a"), ("Spring 트랜잭션 매니저", "b"), ("PostgreSQL", "ok")],
                 [("msg", 0, 2, "1  INSERT keep 행", "a"),
                  ("msg", 0, 2, "2  실패하는 문장 (예: 유니크 위반)", "bad"),
                  ("note", 2, "트랜잭션 중단 (25P02)", "bad"),
                  ("note", 1, "rollbackOnly = false\nSpring 은 모른다", "note"),
                  ("note", 0, "3  catch 하고 정상 반환", "warn"),
                  ("msg", 1, 2, "4  COMMIT", "b"),
                  ("note", 2, "중단된 트랜잭션의 COMMIT 을\n롤백으로 처리 (pgjdbc 는 예외 없음)", "bad"),
                  ("note", 0, "예외 없이 반환 — 호출자는\n성공으로 안다\n그러나 keep 행까지 사라졌다", "bad")],
                 w=1300, pitch=66)
    d.save()


def proxy():
    d = new("blog-t05-proxy", 1400, 620, "self-invocation — 프록시를 지나야 트랜잭션이 열린다",
            "Spring 문서(프록시 모드 기본값): self-invocation 은 @Transactional 이 붙어 있어도 실제 트랜잭션을 만들지 않는다")
    d.card("caller", 40, 150, 260, 120, "호출자", "svc.outerTx()\n또는 svc.innerTx()", bg=P["as_bg"], stroke=P["front"], title_size=16, body_size=14)
    d.card("px", 420, 150, 340, 120, "프록시", "트랜잭션을 열고 닫는다\n(@Transactional 이 동작하는 곳)", bg=P["ok_bg"], stroke=P["green"], title_size=16, body_size=14)
    d.card("tg", 880, 150, 480, 220, "SelfSvc 객체", "outerTx()   @Transactional\ninnerTx()   @Transactional\ninnerNew()  @Transactional(REQUIRES_NEW)\n\nouterTx() 안에서 this.innerNew() 를 부른다", bg=P["note_bg"], stroke=P["muted"], title_size=16, body_size=14)
    d.arrow([(300, 210), (420, 210)], P["front"], "프록시 경유", start="caller", end="px")
    d.arrow([(760, 210), (880, 210)], P["green"], "트랜잭션 열린 뒤", start="px", end="tg")
    d.arrow([(1250, 370), (1250, 430), (1000, 430), (1000, 370)], P["red"], "this.innerNew() — 프록시를 건너뛴다", label_at=(1125, 430), start=None, end=None)
    d.card("res", 40, 480, 1320, 110, "실측 (TransactionSynchronizationManager · txid_current)",
           "같은 클래스에서 this.innerTx() (바깥에 트랜잭션 없음) → active=false name=null — 트랜잭션이 안 열린다\n다른 빈을 거쳐 svc.innerTx() → active=true name=…SelfSvc.innerTx\n@Transactional outerTx() 안에서 this.innerNew() (REQUIRES_NEW) → name=…SelfSvc.outerTx, txid 가 바깥과 같다 — REQUIRES_NEW 도 무시된다",
           bg=P["white"], stroke=P["line"], title_size=15, body_size=14)
    d.save()


def retry_place():
    d = new("blog-t05-retry-place", 1400, 560, "재시도 루프의 위치 (실측: spring-probe)",
            "REPEATABLE READ 에서 먼저 읽고(스냅샷), 다른 연결이 같은 행을 갱신 · 커밋한 뒤 갱신해 첫 시도만 40001 이 나게 했다")
    d.text(40, 106, "트랜잭션 바깥 빈이 @Transactional work() 를 호출 · catch 후 재호출", 16, P["green"], weight=700)
    a = [("시도 1", "txid=861", "a"), ("CannotAcquire\nLockException", "ConcurrencyFailure\nException 으로 catch", "bad"), ("시도 2", "txid=863\n(새 트랜잭션)", "a"), ("성공", "매 시도가 새 트랜잭션", "ok")]
    for i, (t, b, k) in enumerate(a):
        bg, st = kc(k)
        d.card(f"a{i}", 40 + i * 340, 140, 290, 120, t, b, bg=bg, stroke=st, title_size=16, body_size=14)
    for i in range(3):
        d.arrow([(330 + i * 340, 200), (380 + i * 340, 200)], P["muted"], None, start=f"a{i}", end=f"a{i + 1}")
    d.text(40, 306, "@Transactional 메서드 안에서 같은 루프", 16, P["red"], weight=700)
    b = [("시도 1", "실패", "bad"), ("catch", "같은 트랜잭션에서\n계속한다", "warn"), ("시도 2 의 첫 쿼리", "25P02\n(UncategorizedSQLException)", "bad"), ("끝내 실패", "같은 트랜잭션이라\n중단 상태를 못 벗어난다", "bad")]
    for i, (t, bd, k) in enumerate(b):
        bg, st = kc(k)
        d.card(f"b{i}", 40 + i * 340, 340, 290, 120, t, bd, bg=bg, stroke=st, title_size=16, body_size=14)
    for i in range(3):
        d.arrow([(330 + i * 340, 400), (380 + i * 340, 400)], P["muted"], None, start=f"b{i}", end=f"b{i + 1}")
    d.text(40, 490, "재시도할 메서드와 재시도 래퍼를 같은 클래스에 두면 this. 호출이라 트랜잭션이 안 열린다 — 다른 빈이어야 한다", 15, P["muted"])
    d.save()


def retry_which():
    d = matrix("blog-t05-retry-which", "어떤 예외를 재시도하나",
               "상위 갈래로 묶으면 ConcurrencyFailureException(= Pessimistic + Optimistic)이 재시도 후보, DataIntegrityViolationException 은 후보가 아니다",
               ["재시도", "이유"],
               [("40001 직렬화 실패\n(CannotAcquireLockException)", [("예 — 트랜잭션 전체", "ok"), ("PostgreSQL 문서 13.2.2: 중단하고 처음부터 재시도\n(01.01 문서 05)", "w")]),
                ("40P01 데드락", [("예 — 전체 (상한 · 지터)", "ok"), ("다른 트랜잭션이 이겼고 락이 풀렸다 (01.02 문서 05)\n순서 통일로 예방이 먼저", "w")]),
                ("낙관 락 충돌\n(ObjectOptimisticLockingFailure)", [("예 — 다시 읽고 처음부터", "ok"), ("같은 낡은 엔티티로 재시도하면 같은 충돌\n새 트랜잭션에서 재조회", "w")]),
                ("55P03 락 대기 실패", [("상황에 따라", "warn"), ("NOWAIT 는 \"바쁘면 포기 · 나중에\" 설계라 재시도 · 거절은 정책\nlock_timeout 이면 대기열 길이를 본다 (해석)", "w")]),
                ("23505 유니크 위반", [("보통 아니오", "bad"), ("같은 값이면 같은 실패\n멱등 키 충돌이면 \"이미 처리됨\" 으로 응답 (01.03)", "w")])],
               w=1400, first_w=330, row_h=64, size=14, notes="단 55P03 은 JDBC 에서 UncategorizedSQLException 이라 이 갈래에 안 들어온다 (1절)")
    d.save()


if __name__ == "__main__":
    for f in (path, hierarchy, when_thrown, lock_sql, rollback_only, silent_rollback, proxy, retry_place, retry_which):
        f()
    finish()
