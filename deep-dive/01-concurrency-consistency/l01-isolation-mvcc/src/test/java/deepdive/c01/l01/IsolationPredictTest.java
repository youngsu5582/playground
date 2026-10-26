package deepdive.c01.l01;

import deepdive.testkit.PostgresLab;
import deepdive.testkit.Predict;
import deepdive.testkit.Session;
import deepdive.testkit.Session.Pending;
import deepdive.testkit.SqlFailure;
import deepdive.testkit.Timeline;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.time.Duration;

import static deepdive.testkit.Session.Isolation.READ_COMMITTED;
import static deepdive.testkit.Session.Isolation.READ_UNCOMMITTED;
import static deepdive.testkit.Session.Isolation.REPEATABLE_READ;
import static deepdive.testkit.Session.Isolation.SERIALIZABLE;

/**
 * [예측] 각 테스트의 {@code String 예측 = "?";} 를 <b>돌리기 전에</b> 내 답으로 바꾼다.
 * 답 형식은 질문 끝 괄호에 있다 — 숫자는 "50", 예/아니오는 "true"/"false", 결과는 "성공"/"에러 40001" 처럼.
 * 띄어쓰기·대소문자는 상관없다.
 *
 * <p>모든 시나리오는 진짜 PostgreSQL 16 에서 세션 두 개(A, B)로 돈다. 출력에 찍히는 타임라인을 같이 읽는다.
 * 답이 쉽게 안 나오면 README ② 원리 → diagrams/ 그림을 보고 다시.
 *
 * <pre>
 * account(id, balance)        — 계좌 1번, 잔고 100
 * branch_member(name, branch) — seoul 2명
 * on_call(doctor, on_call)    — alice · bob 둘 다 당직
 * </pre>
 */
@DisplayName("[예측] 01.01 격리수준 · MVCC — 10문항")
class IsolationPredictTest {

    static final Duration GRACE = Duration.ofMillis(300);
    final PostgresLab lab = PostgresLab.get();

    @BeforeEach
    void reset() {
        lab.exec(
                "DROP TABLE IF EXISTS account, branch_member, on_call",
                "CREATE TABLE account (id int PRIMARY KEY, balance int NOT NULL)",
                "INSERT INTO account VALUES (1, 100)",
                "CREATE TABLE branch_member (name text PRIMARY KEY, branch text NOT NULL)",
                "INSERT INTO branch_member VALUES ('kim', 'seoul'), ('lee', 'seoul')",
                "CREATE TABLE on_call (doctor text PRIMARY KEY, on_call boolean NOT NULL)",
                "INSERT INTO on_call VALUES ('alice', true), ('bob', true)");
    }

    // ── 1. 읽기 이상 현상 ────────────────────────────────────────

    @Test
    void Q01_READ_COMMITTED_같은_SELECT_를_두_번() {
        Timeline.reset("Q01 READ COMMITTED — 사이에 남이 커밋하면");
        try (Session a = lab.session("A"); Session b = lab.session("B")) {
            a.begin(READ_COMMITTED);
            a.one("SELECT balance FROM account WHERE id = 1");
            b.update("UPDATE account SET balance = 50 WHERE id = 1"); // autocommit
            Object second = a.one("SELECT balance FROM account WHERE id = 1");

            String 예측 = "?";
            Predict.확인("A 의 두 번째 SELECT 결과는? (처음엔 100 · 답: 숫자)", 예측, second);
        }
    }

    @Test
    void Q02_REPEATABLE_READ_같은_SELECT_를_두_번() {
        Timeline.reset("Q02 REPEATABLE READ — 사이에 남이 커밋하면");
        try (Session a = lab.session("A"); Session b = lab.session("B")) {
            a.begin(REPEATABLE_READ);
            a.one("SELECT balance FROM account WHERE id = 1");
            b.update("UPDATE account SET balance = 50 WHERE id = 1");
            Object second = a.one("SELECT balance FROM account WHERE id = 1");

            String 예측 = "?";
            Predict.확인("A 의 두 번째 SELECT 결과는? (처음엔 100 · 답: 숫자)", 예측, second);
        }
    }

    @Test
    void Q03_REPEATABLE_READ_에서_팬텀() {
        Timeline.reset("Q03 REPEATABLE READ — 사이에 새 행이 끼어들면");
        try (Session a = lab.session("A"); Session b = lab.session("B")) {
            a.begin(REPEATABLE_READ);
            a.count("SELECT count(*) FROM branch_member WHERE branch = 'seoul'");
            b.update("INSERT INTO branch_member VALUES ('park', 'seoul')");
            long second = a.count("SELECT count(*) FROM branch_member WHERE branch = 'seoul'");

            String 예측 = "?";
            Predict.확인("A 의 두 번째 count 는? (처음엔 2 · 답: 숫자) — 같은 트랜잭션에서 같은 조건으로 두 번 세고, 그 사이에 B 가 새 행을 커밋했다.", 예측, second);
        }
    }

    @Test
    void Q04_READ_UNCOMMITTED_에서_더티_리드() {
        Timeline.reset("Q04 READ UNCOMMITTED — 남이 아직 커밋 안 한 값");
        try (Session a = lab.session("A"); Session b = lab.session("B")) {
            b.begin(READ_COMMITTED);
            b.update("UPDATE account SET balance = 0 WHERE id = 1"); // 아직 커밋 안 함
            a.begin(READ_UNCOMMITTED);
            Object seen = a.one("SELECT balance FROM account WHERE id = 1");
            b.rollback();

            String 예측 = "?";
            Predict.확인("A 가 READ UNCOMMITTED 로 읽은 잔고는? (B 는 0 으로 바꾸고 아직 커밋 전 · 답: 숫자)", 예측, seen);
        }
    }

    // ── 2. 쓰기 경쟁 ────────────────────────────────────────────

    @Test
    void Q05_READ_COMMITTED_읽고_계산해서_쓰기() {
        Timeline.reset("Q05 READ COMMITTED — 앱에서 읽고 계산해서 쓴다 (read-modify-write)");
        try (Session a = lab.session("A"); Session b = lab.session("B")) {
            a.begin(READ_COMMITTED);
            b.begin(READ_COMMITTED);
            int seenByA = (Integer) a.one("SELECT balance FROM account WHERE id = 1");
            int seenByB = (Integer) b.one("SELECT balance FROM account WHERE id = 1");
            a.update("UPDATE account SET balance = ? WHERE id = 1", seenByA - 30); // 100 - 30
            a.commit();
            b.update("UPDATE account SET balance = ? WHERE id = 1", seenByB - 50); // 100 - 50
            b.commit();
            Object finalBalance = lab.one("SELECT balance FROM account WHERE id = 1");

            String 예측 = "?";
            Predict.확인("두 사람이 30, 50 을 출금했다. 최종 잔고는? (처음 100 · 답: 숫자)", 예측, finalBalance);
        }
    }

    @Test
    void Q06_READ_COMMITTED_원자적_UPDATE_는_기다리나() {
        Timeline.reset("Q06 READ COMMITTED — UPDATE … SET balance = balance - x");
        try (Session a = lab.session("A"); Session b = lab.session("B")) {
            a.begin(READ_COMMITTED);
            b.begin(READ_COMMITTED);
            a.update("UPDATE account SET balance = balance - 30 WHERE id = 1"); // 행 락을 잡은 채 커밋 전
            Pending<Integer> bUpdate = b.updateAsync("UPDATE account SET balance = balance - 50 WHERE id = 1");
            boolean bWaited = bUpdate.isWaiting(GRACE);
            a.commit();
            bUpdate.await(Duration.ofSeconds(5));
            b.commit();
            Object finalBalance = lab.one("SELECT balance FROM account WHERE id = 1");

            String 예측_대기 = "?";
            String 예측_잔고 = "?";
            Predict.확인("A 가 커밋하기 전, B 의 UPDATE 는 기다리나? (답: true / false)", 예측_대기, bWaited);
            Predict.확인("최종 잔고는? (처음 100, 30 과 50 출금 · 답: 숫자)", 예측_잔고, finalBalance);
        }
    }

    @Test
    void Q07_REPEATABLE_READ_스냅샷_이후_바뀐_행을_고치면() {
        Timeline.reset("Q07 REPEATABLE READ — 내 스냅샷 이후 남이 고친 행을 내가 고치면");
        try (Session a = lab.session("A"); Session b = lab.session("B")) {
            a.begin(REPEATABLE_READ);
            a.one("SELECT balance FROM account WHERE id = 1"); // 스냅샷이 여기서 잡힌다
            b.update("UPDATE account SET balance = balance - 50 WHERE id = 1"); // autocommit
            String outcome;
            try {
                a.update("UPDATE account SET balance = balance - 30 WHERE id = 1");
                outcome = "성공";
            } catch (SqlFailure f) {
                outcome = "에러 " + f.sqlState();
            }
            a.rollback();

            String 예측 = "?";
            Predict.확인("A 의 UPDATE 는? (답: \"성공\" 또는 \"에러 \" + SQLState 다섯 글자 — 예: 에러 23505)", 예측, outcome);
        }
    }

    // ── 3. write skew ──────────────────────────────────────────

    @Test
    void Q08_REPEATABLE_READ_당직_두_명이_동시에_빠지면() {
        Timeline.reset("Q08 REPEATABLE READ — 서로 다른 행을 고치는 경쟁 (write skew)");
        try (Session a = lab.session("A"); Session b = lab.session("B")) {
            a.begin(REPEATABLE_READ);
            b.begin(REPEATABLE_READ);
            a.count("SELECT count(*) FROM on_call WHERE on_call"); // 2 → 빠져도 되겠다
            b.count("SELECT count(*) FROM on_call WHERE on_call"); // 2 → 빠져도 되겠다
            a.update("UPDATE on_call SET on_call = false WHERE doctor = 'alice'");
            b.update("UPDATE on_call SET on_call = false WHERE doctor = 'bob'");
            a.commit();
            b.commit();
            Object left = lab.one("SELECT count(*) FROM on_call WHERE on_call");

            String 예측 = "?";
            Predict.확인("남은 당직 수는? (규칙: 항상 1명 이상 · 답: 숫자)", 예측, left);
        }
    }

    @Test
    void Q09_SERIALIZABLE_당직_두_명이_동시에_빠지면() {
        Timeline.reset("Q09 SERIALIZABLE — 같은 경쟁");
        try (Session a = lab.session("A"); Session b = lab.session("B")) {
            a.begin(SERIALIZABLE);
            b.begin(SERIALIZABLE);
            a.count("SELECT count(*) FROM on_call WHERE on_call");
            b.count("SELECT count(*) FROM on_call WHERE on_call");
            a.update("UPDATE on_call SET on_call = false WHERE doctor = 'alice'");
            b.update("UPDATE on_call SET on_call = false WHERE doctor = 'bob'");
            a.commit();
            String bCommit;
            try {
                b.commit();
                bCommit = "성공";
            } catch (SqlFailure f) {
                bCommit = "에러 " + f.sqlState();
            }
            Object left = lab.one("SELECT count(*) FROM on_call WHERE on_call");

            String 예측_B커밋 = "?";
            String 예측_남은당직 = "?";
            Predict.확인("B 의 COMMIT 은? (답: \"성공\" 또는 \"에러 \" + SQLState — 예: 에러 23505)", 예측_B커밋, bCommit);
            Predict.확인("남은 당직 수는? (답: 숫자)", 예측_남은당직, left);
        }
    }

    // ── 4. MVCC 의 정체 ────────────────────────────────────────

    @Test
    void Q10_쓰는_중인_행을_읽으면_기다리나() {
        Timeline.reset("Q10 MVCC — A 가 고치는 중인 행을 B 가 읽는다");
        try (Session a = lab.session("A"); Session b = lab.session("B")) {
            a.begin(READ_COMMITTED);
            Object ctidBefore = a.one("SELECT ctid::text FROM account WHERE id = 1");
            a.update("UPDATE account SET balance = 0 WHERE id = 1"); // 커밋 전
            Object ctidAfter = a.one("SELECT ctid::text FROM account WHERE id = 1");
            b.begin(READ_COMMITTED);
            Pending<Object> bRead = b.async(() -> b.one("SELECT balance FROM account WHERE id = 1"));
            boolean bWaited = bRead.isWaiting(GRACE);
            Object bSaw = bRead.await(Duration.ofSeconds(5));
            a.rollback();
            b.rollback();

            String 예측_대기 = "?";
            String 예측_값 = "?";
            String 예측_ctid = "?";
            Predict.확인("B 의 SELECT 는 A 의 커밋을 기다리나? (답: true / false)", 예측_대기, bWaited);
            Predict.확인("B 가 읽은 잔고는? (A 는 0 으로 바꾸고 커밋 전 · 답: 숫자)", 예측_값, bSaw);
            Predict.확인("A 의 UPDATE 전후 ctid(행의 물리 위치)는? (답: 같다 / 다르다)", 예측_ctid,
                    ctidBefore.equals(ctidAfter) ? "같다" : "다르다");
        }
    }
}
