package deepdive.c01.l06;

import deepdive.testkit.PostgresLab;
import deepdive.testkit.Predict;
import deepdive.testkit.Session;
import deepdive.testkit.SqlFailure;
import deepdive.testkit.Timeline;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

/**
 * [예측] 각 테스트의 {@code String 예측 = "?";} 를 <b>돌리기 전에</b> 내 답으로 바꾼다.
 * 답 형식은 질문 끝 괄호에 있다 — 숫자는 "1.01" · "3", 예/아니오는 "true"/"false", 결과는 "성공"/"에러 23505" 처럼.
 * 띄어쓰기·대소문자는 상관없다.
 *
 * <p>모든 시나리오는 진짜 PostgreSQL 16 에서 돈다. 출력에 찍히는 타임라인을 같이 읽는다.
 * 스키마는 {@code src/main/resources/ledger-schema.sql} — 제약 · 트리거를 먼저 읽고 예측한다.
 *
 * <pre>
 * account(id, balance numeric(20,2) CHECK balance >= 0)   — 1 번 계좌 잔고 100.00
 * ledger(txn_id, account_id, amount)                       — 거래 D1: 계좌 0 에서 -100, 계좌 1 에 +100
 * posted_txn(txn_id)                                       — D1
 * money_box(v numeric(12,2))                               — 비어 있다 (Q02 · Q03)
 * </pre>
 */
@DisplayName("[예측] 01.06 원장과 대사 — 10문항")
class LedgerPredictTest {

    final PostgresLab lab = PostgresLab.get();

    @BeforeEach
    void reset() {
        lab.exec(LedgerSchema.DROP, LedgerSchema.sql(),
                "CREATE TABLE money_box (v numeric(12,2))",
                "INSERT INTO account VALUES (0, -100.00), (1, 100.00)",
                "INSERT INTO ledger (txn_id, account_id, amount) VALUES ('D1', 0, -100.00), ('D1', 1, 100.00)",
                "INSERT INTO posted_txn VALUES ('D1')");
    }

    /** 문장을 실행해 성공이면 "성공", 에러면 "에러 " + SQLState. */
    static String outcome(Runnable statement) {
        try {
            statement.run();
            return "성공";
        } catch (SqlFailure f) {
            return "에러 " + f.sqlState();
        }
    }

    // ── 1. 금액을 어떤 타입에 담나 ───────────────────────────────

    @Test
    void Q01_float8_와_numeric_의_0_1_더하기_0_2() {
        Timeline.reset("Q01 0.1 + 0.2 = 0.3 ? — float8 (실수) 와 numeric (십진 고정)");
        try (Session a = lab.session("A")) {
            Object floatEqual = a.one("SELECT 0.1::float8 + 0.2::float8 = 0.3::float8");
            Object numericEqual = a.one("SELECT 0.1::numeric + 0.2::numeric = 0.3::numeric");

            String 예측_float = "?";
            String 예측_numeric = "?";
            Predict.확인("float8 로 0.1 + 0.2 = 0.3 은 참인가? (답: true / false)", 예측_float, floatEqual);
            Predict.확인("numeric 으로 0.1 + 0.2 = 0.3 은 참인가? (답: true / false)", 예측_numeric, numericEqual);
        }
    }

    @Test
    void Q02_numeric_12_2_에_소수_셋째_자리를_넣으면() {
        Timeline.reset("Q02 numeric(12,2) 에 1.005 와 -1.005 를 넣으면");
        try (Session a = lab.session("A")) {
            a.update("INSERT INTO money_box VALUES (1.005)");
            a.update("INSERT INTO money_box VALUES (-1.005)");
            Object positive = a.one("SELECT v FROM money_box WHERE v > 0");
            Object negative = a.one("SELECT v FROM money_box WHERE v < 0");

            String 예측_양수 = "?";
            String 예측_음수 = "?";
            Predict.확인("1.005 를 넣고 읽으면 저장된 값은? (오류 없이 들어간다 · 답: 숫자 그대로, 예 1.23)", 예측_양수, positive);
            Predict.확인("-1.005 를 넣고 읽으면 저장된 값은? (답: 숫자 그대로)", 예측_음수, negative);
        }
    }

    @Test
    void Q03_numeric_12_2_의_자릿수를_넘기면() {
        Timeline.reset("Q03 numeric(12,2) — 정수부는 최대 10 자리");
        try (Session a = lab.session("A")) {
            String 열_자리 = outcome(() -> a.update("INSERT INTO money_box VALUES (9999999999.99)"));
            String 열한_자리 = outcome(() -> a.update("INSERT INTO money_box VALUES (10000000000)"));

            String 예측_열자리 = "?";
            String 예측_열한자리 = "?";
            Predict.확인("9999999999.99 (정수부 10 자리) 를 넣으면? (답: \"성공\" 또는 \"에러 \" + SQLState)", 예측_열자리, 열_자리);
            Predict.확인("10000000000 (정수부 11 자리) 를 넣으면? (답: \"성공\" 또는 \"에러 \" + SQLState)", 예측_열한자리, 열한_자리);
        }
    }

    // ── 2. 규칙을 언제 검사하나 ──────────────────────────────────

    @Test
    void Q04_CHECK_잔고_0_이상_위반() {
        Timeline.reset("Q04 CHECK (balance >= 0) — 잔고 100 에서 150 을 빼면");
        try (Session a = lab.session("A")) {
            a.begin(Session.Isolation.READ_COMMITTED);
            String update = outcome(() -> a.update("UPDATE account SET balance = balance - 150 WHERE id = 1"));
            String next = outcome(() -> a.one("SELECT balance FROM account WHERE id = 1"));

            String 예측_UPDATE = "?";
            String 예측_다음문장 = "?";
            Predict.확인("트랜잭션 안에서 이 UPDATE 를 실행하면? (답: \"성공\" 또는 \"에러 \" + SQLState)", 예측_UPDATE, update);
            Predict.확인("에러를 받은 그 트랜잭션에서 SELECT 를 이어서 하면? (답: \"성공\" 또는 \"에러 \" + SQLState)", 예측_다음문장, next);
        }
    }

    @Test
    void Q05_지연_제약_트리거_한_다리만_넣고_커밋() {
        Timeline.reset("Q05 DEFERRABLE INITIALLY DEFERRED — 거래 T1 의 다리를 한쪽만 넣고 커밋");
        try (Session a = lab.session("A")) {
            a.begin(Session.Isolation.READ_COMMITTED);
            String insert = outcome(() -> a.update("INSERT INTO ledger (txn_id, account_id, amount) VALUES ('T1', 1, 50.00)"));
            String commit = outcome(a::commit);
            Object rows = a.one("SELECT count(*) FROM ledger WHERE txn_id = 'T1'");

            String 예측_INSERT = "?";
            String 예측_COMMIT = "?";
            String 예측_행수 = "?";
            Predict.확인("+50 한 줄만 INSERT 하면? (한 거래의 다리 합이 0 이어야 한다는 지연 제약 트리거가 있다 · 답: \"성공\" 또는 \"에러 \" + SQLState)", 예측_INSERT, insert);
            Predict.확인("이어서 COMMIT 하면? (답: \"성공\" 또는 \"에러 \" + SQLState)", 예측_COMMIT, commit);
            Predict.확인("그 뒤 ledger 에 txn_id = 'T1' 인 행은 몇 개? (답: 숫자)", 예측_행수, rows);
        }
    }

    @Test
    void Q06_SET_CONSTRAINTS_IMMEDIATE_로_검사_시점_앞당기기() {
        Timeline.reset("Q06 SET CONSTRAINTS ALL IMMEDIATE — 검사 시점을 커밋에서 문장으로");
        try (Session a = lab.session("A"); Session b = lab.session("B")) {
            a.begin(Session.Isolation.READ_COMMITTED);
            a.update("INSERT INTO ledger (txn_id, account_id, amount) VALUES ('T1', 1, 50.00)");
            String setNow = outcome(() -> a.update("SET CONSTRAINTS ALL IMMEDIATE"));
            a.rollback();

            b.begin(Session.Isolation.READ_COMMITTED);
            b.update("SET CONSTRAINTS ALL IMMEDIATE");
            String insertNow = outcome(() -> b.update("INSERT INTO ledger (txn_id, account_id, amount) VALUES ('T2', 1, 50.00)"));

            String 예측_SET = "?";
            String 예측_INSERT = "?";
            Predict.확인("A: 한 줄만 INSERT 한 뒤 SET CONSTRAINTS ALL IMMEDIATE 를 실행하면? (답: \"성공\" 또는 \"에러 \" + SQLState)", 예측_SET, setNow);
            Predict.확인("B: 먼저 SET CONSTRAINTS ALL IMMEDIATE 를 하고 한 줄만 INSERT 하면, 그 INSERT 는? (답: \"성공\" 또는 \"에러 \" + SQLState)", 예측_INSERT, insertNow);
        }
    }

    // ── 3. 원장은 쌓기만 한다 · 같은 거래는 한 번만 ───────────────

    @Test
    void Q07_원장_append_only_UPDATE_와_TRUNCATE() {
        Timeline.reset("Q07 원장 append-only — UPDATE 는 막고 TRUNCATE 는?");
        try (Session a = lab.session("A")) {
            String update = outcome(() -> a.update("UPDATE ledger SET amount = 999.00 WHERE txn_id = 'D1' AND account_id = 1"));
            String truncate = outcome(() -> a.update("TRUNCATE ledger"));
            Object rows = a.one("SELECT count(*) FROM ledger");

            String 예측_UPDATE = "?";
            String 예측_TRUNCATE = "?";
            String 예측_행수 = "?";
            Predict.확인("ledger 에 BEFORE UPDATE OR DELETE 행 트리거가 있다. UPDATE 를 하면? (답: \"성공\" 또는 \"에러 \" + SQLState)", 예측_UPDATE, update);
            Predict.확인("같은 테이블을 TRUNCATE 하면? (답: \"성공\" 또는 \"에러 \" + SQLState)", 예측_TRUNCATE, truncate);
            Predict.확인("그 뒤 ledger 의 행 수는? (처음엔 2 · 답: 숫자)", 예측_행수, rows);
        }
    }

    @Test
    void Q08_같은_거래를_두_번_기록하면() {
        Timeline.reset("Q08 같은 거래 id D1 을 또 올린다 — posted_txn 에 이미 D1 이 있다");
        try (Session a = lab.session("A")) {
            int skipped = a.update("INSERT INTO posted_txn (txn_id) VALUES ('D1') ON CONFLICT DO NOTHING");
            String plain = outcome(() -> a.update("INSERT INTO posted_txn (txn_id) VALUES ('D1')"));
            String legs = outcome(() -> a.update("INSERT INTO ledger (txn_id, account_id, amount) VALUES ('D1', 1, 100.00), ('D1', 0, -100.00)"));

            String 예측_충돌무시 = "?";
            String 예측_그냥 = "?";
            String 예측_원장 = "?";
            Predict.확인("ON CONFLICT DO NOTHING 으로 D1 을 넣으면 영향 행 수는? (답: 숫자)", 예측_충돌무시, skipped);
            Predict.확인("ON CONFLICT 없이 D1 을 넣으면? (답: \"성공\" 또는 \"에러 \" + SQLState)", 예측_그냥, plain);
            Predict.확인("선점 없이 원장에 D1 의 두 다리를 또 넣으면? ledger 에는 UNIQUE (txn_id, account_id) 가 있다 (답: \"성공\" 또는 \"에러 \" + SQLState)", 예측_원장, legs);
        }
    }

    // ── 4. 대사 ─────────────────────────────────────────────────

    @Test
    void Q09_float8_로_모은_합은_1_과_같은가() {
        Timeline.reset("Q09 0.1 을 열 번 더하면 — float8 vs numeric");
        try (Session a = lab.session("A")) {
            Object floatTotal = a.one("SELECT sum(0.1::float8) = 1 FROM generate_series(1, 10)");
            Object numericTotal = a.one("SELECT sum(0.1::numeric) = 1 FROM generate_series(1, 10)");

            String 예측_float = "?";
            String 예측_numeric = "?";
            Predict.확인("0.1 (float8) 을 열 번 더한 합은 1 과 같은가? (대사에서 '합이 맞나' 를 = 로 비교한다면 · 답: true / false)", 예측_float, floatTotal);
            Predict.확인("0.1 (numeric) 을 열 번 더한 합은 1 과 같은가? (답: true / false)", 예측_numeric, numericTotal);
        }
    }

    @Test
    void Q10_대사_쿼리가_찾는_어긋남_건수() {
        Timeline.reset("Q10 대사 쿼리 — 계좌 잔고 vs 계좌별 원장 합");
        try (Session a = lab.session("A")) {
            // 계좌: 0(-145) 1(100) 2(50) 3(10) 5(0) — 4 번 계좌는 없다.  원장: D1 0/1 100 · D2 0/2 40 · D4 0/4 5
            a.update("DELETE FROM account");
            a.update("INSERT INTO account VALUES (0, -145.00), (1, 100.00), (2, 50.00), (3, 10.00), (5, 0.00)");
            a.update("TRUNCATE ledger");
            a.update("INSERT INTO ledger (txn_id, account_id, amount) VALUES "
                    + "('D1', 0, -100.00), ('D1', 1, 100.00), ('D2', 0, -40.00), ('D2', 2, 40.00), ('D4', 0, -5.00), ('D4', 4, 5.00)");
            Object inner = a.one("""
                    SELECT count(*) FROM account a
                    JOIN (SELECT account_id, sum(amount) AS s FROM ledger GROUP BY account_id) l ON l.account_id = a.id
                    WHERE a.balance <> l.s""");
            Object full = a.one("""
                    SELECT count(*) FROM account a
                    FULL OUTER JOIN (SELECT account_id, sum(amount) AS s FROM ledger GROUP BY account_id) l ON l.account_id = a.id
                    WHERE a.id IS NULL OR a.balance <> COALESCE(l.s, 0)""");

            String 예측_INNER = "?";
            String 예측_FULL = "?";
            Predict.확인("INNER JOIN 으로 \"잔고 <> 원장 합\" 인 계좌를 세면 몇 건? (답: 숫자)", 예측_INNER, inner);
            Predict.확인("FULL OUTER JOIN + COALESCE(합, 0) 으로 (계좌가 없는 경우 포함) 세면 몇 건? (답: 숫자)", 예측_FULL, full);
        }
    }
}
