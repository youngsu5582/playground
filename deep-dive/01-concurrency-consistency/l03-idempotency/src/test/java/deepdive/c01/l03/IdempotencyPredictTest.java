package deepdive.c01.l03;

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
import java.util.List;
import java.util.Map;

import static deepdive.testkit.Session.Isolation.READ_COMMITTED;

/**
 * [예측] 각 테스트의 {@code String 예측 = "?";} 를 <b>돌리기 전에</b> 내 답으로 바꾼다.
 * 답 형식은 질문 끝 괄호에 있다 — 숫자는 "2", 예/아니오는 "true"/"false", 결과는 "성공"/"에러 23505" 처럼.
 * 띄어쓰기·대소문자는 상관없다.
 *
 * <p>모든 시나리오는 진짜 PostgreSQL 16 에서 세션 두 개(A, B)로 돈다. 출력에 찍히는 타임라인을 같이 읽는다.
 * 답이 쉽게 안 나오면 README ② 원리 → diagrams/ 그림을 보고 다시.
 *
 * <pre>
 * loose(key, note)                    — 제약 없는 테이블 (같은 키가 여러 행일 수 있다)
 * idem(key PRIMARY KEY, payload, hits) — 키에 유니크 제약. 처음엔 ('k1', 'first', 1) 한 행
 * </pre>
 */
@DisplayName("[예측] 01.03 멱등성 — 10문항")
class IdempotencyPredictTest {

    static final Duration GRACE = Duration.ofMillis(300);
    final PostgresLab lab = PostgresLab.get();

    @BeforeEach
    void reset() {
        lab.exec(
                "DROP TABLE IF EXISTS loose, idem",
                "CREATE TABLE loose (key text NOT NULL, note text)",
                "CREATE TABLE idem (key text PRIMARY KEY, payload text NOT NULL, hits int NOT NULL DEFAULT 1)",
                "INSERT INTO idem (key, payload) VALUES ('k1', 'first')");
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

    // ── 1. "있나 확인하고 넣는다" 는 왜 깨지나 ──────────────────────

    @Test
    void Q01_확인하고_INSERT_를_교차_실행하면() {
        Timeline.reset("Q01 유니크 제약 없음 — SELECT 로 없음 확인 → INSERT, 두 세션이 교차");
        try (Session a = lab.session("A"); Session b = lab.session("B")) {
            a.begin(READ_COMMITTED);
            b.begin(READ_COMMITTED);
            long seenByA = a.count("SELECT count(*) FROM loose WHERE key = 'pay-1'"); // 0 → 넣어도 되겠다
            long seenByB = b.count("SELECT count(*) FROM loose WHERE key = 'pay-1'"); // 0 → 넣어도 되겠다
            if (seenByA == 0) a.update("INSERT INTO loose (key, note) VALUES ('pay-1', 'from A')");
            if (seenByB == 0) b.update("INSERT INTO loose (key, note) VALUES ('pay-1', 'from B')");
            a.commit();
            b.commit();
            Object rows = lab.one("SELECT count(*) FROM loose WHERE key = 'pay-1'");

            // 두 곳에서 동시에 INSERT 가 발생한다.
            String 예측 = "2";
            Predict.확인("두 세션이 모두 '없네' 를 보고 INSERT 했다. key = 'pay-1' 인 행은 몇 개? (답: 숫자)", 예측, rows);
        }
    }

    @Test
    void Q02_유니크_제약이_있을_때_두_번째_INSERT() {
        Timeline.reset("Q02 유니크 제약 — 이미 있는 키를 한 번 더");
        try (Session a = lab.session("A")) {
            String outcome = outcome(() -> a.update("INSERT INTO idem (key, payload) VALUES ('k1', 'second')")); // autocommit

            // DB 단에서 일관성을 지킨다.
            // 23505 : duplicate key value violates unique constraint ...
            String 예측 = "에러23505";
            Predict.확인("이미 k1 이 있다. 같은 키로 INSERT 하면? (답: \"성공\" 또는 \"에러 \" + SQLState)", 예측, outcome);
        }
    }

    // ── 2. 같은 키가 동시에 오면 ────────────────────────────────
    // B는 A의 결과를 기다린다.
    // PostgreSQL: 유니크 인덱스에 미커밋 + 충돌 행을 발견하면
    // A 트랜잭션 종료를 기다린 뒤 재검사
    // MySQL: A의 INSERT가 유니크 인덱스에 잡은 X lock 때문에
    // B가 대기한다.
    @Test
    void Q03_처리_중인_같은_키를_INSERT_하면_기다리나() {
        Timeline.reset("Q03 A 가 k2 를 INSERT 하고 커밋 전 — B 도 k2 를 INSERT");
        try (Session a = lab.session("A"); Session b = lab.session("B")) {
            a.begin(READ_COMMITTED);
            b.begin(READ_COMMITTED);
            a.update("INSERT INTO idem (key, payload) VALUES ('k2', 'from A')"); // 커밋 전
            Pending<Integer> bInsert = b.updateAsync("INSERT INTO idem (key, payload) VALUES ('k2', 'from B')");
            boolean bWaited = bInsert.isWaiting(GRACE);
            a.commit();
            outcome(() -> bInsert.await(Duration.ofSeconds(5))); // 뒷정리 — 결과는 Q04

            // A가 커밋을 하지 않았어도, INSERT 구문이 들어가고 유니크 인덱스에도 엔트리가 생성된다.
            // 행의 생성 트랜잭션(A) 이 진행 중임을 확인
            // -> 결과를 기다림.
            String 예측 = "true";
            Predict.확인("A 가 커밋하기 전, B 의 INSERT 는 기다리나? 바로 에러가 나나? (답: true = 기다린다 / false)", 예측, bWaited);
        }
    }

    @Test
    void Q04_앞선_쪽이_커밋하면_기다리던_INSERT_는() {
        Timeline.reset("Q04 A 가 k2 INSERT 후 COMMIT — 기다리던 B 의 INSERT 는");
        try (Session a = lab.session("A"); Session b = lab.session("B")) {
            a.begin(READ_COMMITTED);
            b.begin(READ_COMMITTED);
            a.update("INSERT INTO idem (key, payload) VALUES ('k2', 'from A')");
            Pending<Integer> bInsert = b.updateAsync("INSERT INTO idem (key, payload) VALUES ('k2', 'from B')");
            bInsert.isWaiting(GRACE); // B 가 막힌 걸 확인하고 나서
            a.commit();
            String outcome = outcome(() -> bInsert.await(Duration.ofSeconds(5)));

            // A가 성공적으로 커밋 되었으니, B는 에러 처리
            String 예측 = "에러23505";
            Predict.확인("A 가 커밋한 뒤 B 의 INSERT 는? (답: \"성공\" 또는 \"에러 \" + SQLState)", 예측, outcome);
        }
    }

    @Test
    void Q05_앞선_쪽이_롤백하면_기다리던_INSERT_는() {
        Timeline.reset("Q05 A 가 k2 INSERT 후 ROLLBACK — 기다리던 B 의 INSERT 는");
        try (Session a = lab.session("A"); Session b = lab.session("B")) {
            a.begin(READ_COMMITTED);
            b.begin(READ_COMMITTED);
            a.update("INSERT INTO idem (key, payload) VALUES ('k2', 'from A')");
            Pending<Integer> bInsert = b.updateAsync("INSERT INTO idem (key, payload) VALUES ('k2', 'from B')");
            bInsert.isWaiting(GRACE);
            a.rollback();
            String outcome = outcome(() -> bInsert.await(Duration.ofSeconds(5)));
            b.commit();
            Object payload = lab.one("SELECT payload FROM idem WHERE key = 'k2'");

            String 예측_결과 = "성공";
            String 예측_내용 = "from B";
            Predict.확인("A 가 롤백한 뒤 B 의 INSERT 는? (답: \"성공\" 또는 \"에러 \" + SQLState)", 예측_결과, outcome);
            Predict.확인("B 가 커밋한 뒤 k2 의 payload 는? (답: from A / from B)", 예측_내용, payload);
        }
    }

    // ── 3. ON CONFLICT 가 보장하는 것 ───────────────────────────

    @Test
    void Q06_ON_CONFLICT_DO_NOTHING_의_영향_행_수() {
        Timeline.reset("Q06 INSERT … ON CONFLICT DO NOTHING — 이미 있는 키");
        try (Session a = lab.session("A")) {
            int affected = a.update("INSERT INTO idem (key, payload) VALUES ('k1', 'second') ON CONFLICT (key) DO NOTHING");
            List<Map<String, Object>> returned =
                    a.query("INSERT INTO idem (key, payload) VALUES ('k1', 'third') ON CONFLICT (key) DO NOTHING RETURNING key");

            // DO NOTHING 은 아무것도 하지 않는다.
            // 영향을 받은게 없으므로, 0을 반환
            String 예측_영향 = "0";
            String 예측_반환 = "0";
            Predict.확인("이미 k1 이 있다. DO NOTHING 으로 INSERT 하면 영향 행 수는? (답: 숫자)", 예측_영향, affected);
            Predict.확인("같은 INSERT 에 RETURNING key 를 붙이면 돌려받는 행은 몇 개? (답: 숫자)", 예측_반환, returned.size());
        }
    }

    @Test
    void Q07_처리_중인_키에_DO_NOTHING_을_걸면() {
        Timeline.reset("Q07 A 가 k2 INSERT 커밋 전 — B 는 ON CONFLICT DO NOTHING 으로 INSERT");
        try (Session a = lab.session("A"); Session b = lab.session("B")) {
            a.begin(READ_COMMITTED);
            b.begin(READ_COMMITTED);
            a.update("INSERT INTO idem (key, payload) VALUES ('k2', 'from A')"); // 커밋 전
            Pending<Integer> bInsert = b.updateAsync(
                    "INSERT INTO idem (key, payload) VALUES ('k2', 'from B') ON CONFLICT (key) DO NOTHING");
            boolean bWaited = bInsert.isWaiting(GRACE);
            a.commit();
            int affected = bInsert.await(Duration.ofSeconds(5));
            b.commit();

            // DO NOTHING 이더라도, 트랜잭션은 대기한다.
            String 예측_대기 = "true";
            String 예측_영향 = "0";
            Predict.확인("A 가 커밋하기 전, B 의 DO NOTHING INSERT 는 기다리나? (DO NOTHING 이니 바로 0행?) (답: true / false)", 예측_대기, bWaited);
            Predict.확인("A 가 커밋한 뒤, B 의 영향 행 수는? (답: 숫자)", 예측_영향, affected);
        }
    }

    @Test
    void Q08_ON_CONFLICT_DO_UPDATE_RETURNING_은_무엇을_돌려주나() {
        Timeline.reset("Q08 INSERT … ON CONFLICT (key) DO UPDATE SET hits = hits + 1 RETURNING …");
        try (Session a = lab.session("A")) {
            List<Map<String, Object>> rows = a.query("""
                    INSERT INTO idem (key, payload) VALUES ('k1', 'second')
                    ON CONFLICT (key) DO UPDATE SET hits = idem.hits + 1
                    RETURNING payload, hits""");
            Object payload = rows.getFirst().get("payload");
            Object hits = rows.getFirst().get("hits");

            // 충돌 시, 기존 행에 변경을 적용하진 않고 - second
            // hits + 1 UPDATE 만 수행한다.
            String 예측_내용 = "first";
            String 예측_횟수 = "2";
            Predict.확인("k1 은 ('first', hits 1) 이다. RETURNING payload 는? (답: first / second)", 예측_내용, payload);
            Predict.확인("RETURNING hits 는? (답: 숫자)", 예측_횟수, hits);
        }
    }

    // ── 4. 트랜잭션 안에서 23505 를 만나면 ───────────────────────

    @Test
    void Q09_23505_를_받은_트랜잭션의_다음_문장() {
        Timeline.reset("Q09 트랜잭션 안에서 23505 를 만난 뒤 — 다음 문장");
        try (Session a = lab.session("A")) {
            a.begin(READ_COMMITTED);
            outcome(() -> a.update("INSERT INTO idem (key, payload) VALUES ('k1', 'second')")); // 23505
            String next = outcome(() -> a.one("SELECT payload FROM idem WHERE key = 'k1'"));
            a.rollback();

            // 이미 23505 로 충돌 발생
            // -> 트랜잭션이 aborted 로 기록, 이후 select 도 에러 발생
            String 예측 = "에러" + "25P02";
            Predict.확인("에러를 잡고 같은 트랜잭션에서 SELECT 를 이어서 하면? (답: \"성공\" 또는 \"에러 \" + SQLState)", 예측, next);
        }
    }

    @Test
    void Q10_SAVEPOINT_로_감싸면() {
        Timeline.reset("Q10 SAVEPOINT 로 감싼 INSERT 가 23505 를 낸 뒤 — ROLLBACK TO SAVEPOINT 하고 다음 문장");
        try (Session a = lab.session("A")) {
            a.begin(READ_COMMITTED);
            a.update("SAVEPOINT sp");
            outcome(() -> a.update("INSERT INTO idem (key, payload) VALUES ('k1', 'second')")); // 23505
            a.update("ROLLBACK TO SAVEPOINT sp");
            String next = outcome(() -> a.one("SELECT payload FROM idem WHERE key = 'k1'"));
            a.rollback();

            // save point 까지만 롤백하고, 그 다음 쿼리는 정상적 진행
            String 예측 = "성공";
            Predict.확인("ROLLBACK TO SAVEPOINT 뒤에 SELECT 를 이어서 하면? (답: \"성공\" 또는 \"에러 \" + SQLState)", 예측, next);
        }
    }
}
