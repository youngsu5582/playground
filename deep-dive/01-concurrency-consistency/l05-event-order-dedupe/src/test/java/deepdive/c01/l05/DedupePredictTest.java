package deepdive.c01.l05;

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
import java.util.function.Supplier;

import static deepdive.testkit.Session.Isolation.READ_COMMITTED;
import static deepdive.testkit.Session.Isolation.REPEATABLE_READ;

/**
 * [예측] 각 테스트의 {@code String 예측 = "?";} 를 <b>돌리기 전에</b> 내 답으로 바꾼다.
 * 답 형식은 질문 끝 괄호에 있다 — 숫자는 "2", 예/아니오는 "true"/"false", 상태 이름은 "SHIPPED" 처럼.
 * 띄어쓰기·대소문자는 상관없다.
 *
 * <p>모든 시나리오는 진짜 PostgreSQL 16 에서 세션 두 개(A, B)로 돈다. 출력에 찍히는 타임라인을 같이 읽는다.
 * "이벤트가 DB 에 도착한 순간" 만 다룬다 — 브로커(Kafka)는 02.03 에서.
 *
 * <pre>
 * shipment(id, version, status, change_count) — s1 하나. 처음엔 version 0 · READY · 반영 0회
 * inbox(message_id)                           — 처리한 메시지의 기록. 처음엔 비어 있다
 * </pre>
 */
@DisplayName("[예측] 01.05 이벤트 중복 · 순서 — 10문항")
class DedupePredictTest {

    static final Duration GRACE = Duration.ofMillis(300);
    final PostgresLab lab = PostgresLab.get();

    @BeforeEach
    void reset() {
        lab.exec(
                "DROP TABLE IF EXISTS shipment, inbox",
                "CREATE TABLE shipment (id text PRIMARY KEY, version int NOT NULL, status text NOT NULL, change_count int NOT NULL)",
                "INSERT INTO shipment VALUES ('s1', 0, 'READY', 0)",
                "CREATE TABLE inbox (message_id text PRIMARY KEY)");
    }

    /** 이벤트를 version 확인 없이 그대로 덮어쓴다 (반영 횟수 +1). */
    static final String BLIND = "UPDATE shipment SET version = %d, status = '%s', change_count = change_count + 1 WHERE id = 's1'";

    /** version 이 더 클 때만 덮어쓴다 (반영 횟수 +1). */
    static final String CONDITIONAL = "UPDATE shipment SET version = %d, status = '%s', change_count = change_count + 1 WHERE id = 's1' AND version < %d";

    /**
     * 실제 MQ 호출이 아니라, 전달된 메시지를 소비자 핸들러가 처리하는 흐름을 시뮬레이션한다.
     * MQ는 SQL을 실행하지 않고 {@code consumerHandler}를 호출하며, 핸들러가 DB 작업을 수행한다.
     */
    private static <T> T mqDelivers(String delivery, Supplier<T> consumerHandler) {
        Timeline.note("MQ 전달(시뮬레이션): " + delivery);
        try {
            return consumerHandler.get();
        } catch (RuntimeException failure) {
            mqNacks(delivery);
            throw failure;
        }
    }

    /** 소비자 핸들러가 DB 반영까지 끝낸 뒤 브로커에 성공 처리를 알린다. */
    private static void mqAcks(String delivery) {
        Timeline.note("MQ ACK(시뮬레이션): " + delivery);
    }

    /** 소비자 핸들러가 실패하거나 DB를 롤백해 브로커에 재전달을 요청한다. */
    private static void mqNacks(String delivery) {
        Timeline.note("MQ NACK / 재전달 대상(시뮬레이션): " + delivery);
    }

    // ── 1. 막지 않으면 ──────────────────────────────────────────

    @Test
    void Q01_같은_이벤트가_두_번_도착하면() {
        Timeline.reset("Q01 inbox 없음 — 같은 이벤트(SHIPPED v1)가 두 번 도착한다");
        try (Session a = lab.session("A")) {
            mqDelivers("shipment s1 v1 / SHIPPED", () -> a.update(BLIND.formatted(1, "SHIPPED")));
            mqAcks("shipment s1 v1 / SHIPPED");
            mqDelivers("shipment s1 v1 / SHIPPED (재전달)", () -> a.update(BLIND.formatted(1, "SHIPPED")));
            mqAcks("shipment s1 v1 / SHIPPED (재전달)");
            Object count = a.one("SELECT change_count FROM shipment WHERE id = 's1'");

            // 같은 이벤트가 두번 전달된다.
            String 예측 = "2";
            Predict.확인("알림 발송 같은 부수 효과는 change_count 로 센다. 같은 이벤트를 두 번 반영한 뒤의 change_count 는? (답: 숫자)", 예측, count);
        }
    }

    @Test
    void Q02_늦게_온_과거_이벤트() {
        Timeline.reset("Q02 version 비교 없음 — DELIVERED(v3) 다음에 IN_TRANSIT(v2) 가 늦게 도착한다");
        try (Session a = lab.session("A")) {
            mqDelivers("shipment s1 v3 / DELIVERED", () -> a.update(BLIND.formatted(3, "DELIVERED")));
            mqAcks("shipment s1 v3 / DELIVERED");
            mqDelivers("shipment s1 v2 / IN_TRANSIT (늦은 도착)", () -> a.update(BLIND.formatted(2, "IN_TRANSIT")));
            mqAcks("shipment s1 v2 / IN_TRANSIT (늦은 도착)");
            Object status = a.one("SELECT status FROM shipment WHERE id = 's1'");

            // Queue Publisher 를 사용 시, 순서가 역전될 수 있다.
            // DELIVERED -> IN_TRANSIT 로 처리된다.
            String 예측 = "IN_TRANSIT";
            Predict.확인("최종 status 는? (답: READY / IN_TRANSIT / DELIVERED 중 하나)", 예측, status);
        }
    }

    // ── 2. version 과 inbox 로 막기 ─────────────────────────────

    @Test
    void Q03_조건부_UPDATE_로_과거와_같은_버전을_보내면() {
        Timeline.reset("Q03 WHERE version < :v — v3 가 반영된 뒤 v2 와 v3 가 또 온다");
        try (Session a = lab.session("A")) {
            mqDelivers("shipment s1 v3 / DELIVERED", () -> a.update(CONDITIONAL.formatted(3, "DELIVERED", 3)));
            mqAcks("shipment s1 v3 / DELIVERED");
            int staleRows = mqDelivers("shipment s1 v2 / IN_TRANSIT (늦은 도착)", () -> a.update(CONDITIONAL.formatted(2, "IN_TRANSIT", 2)));
            mqAcks("shipment s1 v2 / IN_TRANSIT (늦은 도착)");
            int sameRows = mqDelivers("shipment s1 v3 / DELIVERED (중복 전달)", () -> a.update(CONDITIONAL.formatted(3, "DELIVERED", 3)));
            mqAcks("shipment s1 v3 / DELIVERED (중복 전달)");

            // v2 는 이미, v3 보다 조건문이 아래이므로 처리되지 않는다.
            String 예측_과거 = "0";
            // v3 는 이미, 처리되었으므로 v3 < v3 을 만족하지 않아 처리되지 않는다.
            String 예측_같은버전 = "0";
            Predict.확인("v3 가 이미 반영돼 있다. v2 를 보내는 UPDATE 의 영향 행 수는? (답: 숫자)", 예측_과거, staleRows);
            Predict.확인("같은 v3 를 한 번 더 보내는 UPDATE 의 영향 행 수는? (답: 숫자)", 예측_같은버전, sameRows);
        }
    }

    @Test
    void Q04_같은_messageId_를_inbox_에_두_번() {
        Timeline.reset("Q04 INSERT INTO inbox … ON CONFLICT DO NOTHING — 같은 messageId 두 번");
        try (Session a = lab.session("A")) {
            int first = mqDelivers("messageId=m-1", () -> a.update("INSERT INTO inbox (message_id) VALUES ('m-1') ON CONFLICT DO NOTHING"));
            mqAcks("messageId=m-1");
            int second = mqDelivers("messageId=m-1 (재전달)", () -> a.update("INSERT INTO inbox (message_id) VALUES ('m-1') ON CONFLICT DO NOTHING"));
            mqAcks("messageId=m-1 (재전달)");

            // 처음에만 수행되고, 두번째는 수행되지 않아서 0을 반환한다.
            String 예측_첫번째 = "1";
            String 예측_두번째 = "0";
            Predict.확인("첫 번째 INSERT 의 영향 행 수는? (답: 숫자)", 예측_첫번째, first);
            Predict.확인("두 번째 INSERT 의 영향 행 수는? (에러가 아니다 · 답: 숫자)", 예측_두번째, second);
        }
    }

    // ── 3. 기록과 반영이 갈라지면 ───────────────────────────────

    @Test
    void Q05_inbox_를_먼저_커밋하고_반영에서_실패하면() {
        Timeline.reset("Q05 inbox 기록과 반영이 다른 트랜잭션 — 그 사이에 반영이 실패한다");
        try (Session a = lab.session("A")) {
            try {
                mqDelivers("messageId=m-9", () -> {
                    // [DB TX #1] begin()이 없으므로 이 INSERT 하나가 autocommit으로 확정된다.
                    a.update("INSERT INTO inbox (message_id) VALUES ('m-9') ON CONFLICT DO NOTHING");

                    // [DB TX #2] inbox와 별개의 autocommit 문장. 도메인 반영만 실패한다.
                    // 이 DDL은 실제 소비자 로직이 아니라, 테스트가 주입하는 장애다.
                    lab.exec("ALTER TABLE shipment ADD CONSTRAINT maintenance CHECK (status <> 'DELIVERED')");
                    return a.update(BLIND.formatted(1, "DELIVERED"));
                });
            } catch (SqlFailure expected) {
                Timeline.note("반영 실패 " + expected.sqlState() + " — inbox는 이미 커밋됐고 소비자는 NACK 한다");
            }
            lab.exec("ALTER TABLE shipment DROP CONSTRAINT maintenance"); // 장애가 풀렸다

            int redelivered = mqDelivers("messageId=m-9 (재전달)", () -> {
                // inbox가 0행이면 앱은 이미 처리했다고 판단해 도메인 반영을 건너뛴다.
                int inboxRows = a.update("INSERT INTO inbox (message_id) VALUES ('m-9') ON CONFLICT DO NOTHING");
                if (inboxRows == 1) a.update(BLIND.formatted(1, "DELIVERED"));
                return inboxRows;
            });
            mqAcks("messageId=m-9 (재전달)");
            Object status = a.one("SELECT status FROM shipment WHERE id = 's1'");

            // 이미 처리된 상태여서 0이다.
            String 예측_재전달 = "0";
            // inbox는 이미 커밋됐지만 shipment 반영이 실패했고, 재전달도 건너뛰어 READY다.
            String 예측_상태 = "READY";
            Predict.확인("재전달된 메시지의 inbox INSERT 영향 행 수는? (답: 숫자)", 예측_재전달, redelivered);
            Predict.확인("재전달을 처리한 뒤 shipment.status 는? (이벤트는 DELIVERED 를 말한다 · 답: READY / DELIVERED 중 하나)", 예측_상태, status);
        }
    }

    @Test
    void Q06_inbox_와_반영을_한_트랜잭션으로_묶으면() {
        Timeline.reset("Q06 inbox 기록과 반영이 한 트랜잭션 — 반영이 실패하면");
        try (Session a = lab.session("A")) {
            try {
                mqDelivers("messageId=m-9", () -> {
                    a.begin(READ_COMMITTED);
                    try {
                        // 같은 DB 트랜잭션: 처리 기록과 도메인 반영은 함께 커밋하거나 함께 롤백한다.
                        a.update("INSERT INTO inbox (message_id) VALUES ('m-9') ON CONFLICT DO NOTHING");
                        // 이 DDL은 실제 소비자 로직이 아니라, 테스트가 주입하는 장애다.
                        lab.exec("ALTER TABLE shipment ADD CONSTRAINT maintenance CHECK (status <> 'DELIVERED')");
                        a.update(BLIND.formatted(1, "DELIVERED"));
                        a.commit();
                        return null;
                    } catch (SqlFailure failure) {
                        a.rollback();
                        Timeline.note("DB ROLLBACK — inbox와 shipment 반영을 함께 취소한다");
                        throw failure;
                    }
                });
            } catch (SqlFailure expected) {
                Timeline.note("소비자 실패 " + expected.sqlState() + " — 브로커가 재전달할 수 있다");
            }
            lab.exec("ALTER TABLE shipment DROP CONSTRAINT maintenance");

            int redelivered = mqDelivers("messageId=m-9 (재전달)", () -> {
                a.begin(READ_COMMITTED);
                int inboxRows = a.update("INSERT INTO inbox (message_id) VALUES ('m-9') ON CONFLICT DO NOTHING");
                if (inboxRows == 1) a.update(BLIND.formatted(1, "DELIVERED"));
                a.commit();
                return inboxRows;
            });
            mqAcks("messageId=m-9 (재전달)");
            Object status = a.one("SELECT status FROM shipment WHERE id = 's1'");

            // 롤백이 되었으므로, 다시 반영이 된다 -> 1 반환
            String 예측_재전달 = "1";
            String 예측_상태 = "DELIVERED";
            Predict.확인("재전달된 메시지의 inbox INSERT 영향 행 수는? (답: 숫자)", 예측_재전달, redelivered);
            Predict.확인("재전달을 처리한 뒤 shipment.status 는? (답: READY / DELIVERED 중 하나)", 예측_상태, status);
        }
    }

    // ── 4. 동시에 오면 ──────────────────────────────────────────

    @Test
    void Q07_두_세션이_같은_키에_v3_와_v2_를_동시에() {
        Timeline.reset("Q07 조건부 UPDATE — A 가 v3 를 반영하는 중(커밋 전)에 B 가 v2 를 보낸다");
        try (Session a = lab.session("A"); Session b = lab.session("B")) {
            a.begin(READ_COMMITTED);
            b.begin(READ_COMMITTED);
            mqDelivers("A 소비자: shipment s1 v3 / DELIVERED", () -> a.update(CONDITIONAL.formatted(3, "DELIVERED", 3)));
            Pending<Integer> bUpdate = mqDelivers("B 소비자: shipment s1 v2 / IN_TRANSIT (동시 전달)", () -> b.updateAsync(CONDITIONAL.formatted(2, "IN_TRANSIT", 2)));
            boolean bWaited = bUpdate.isWaiting(GRACE);
            a.commit();
            mqAcks("A 소비자: shipment s1 v3 / DELIVERED");
            int bRows = bUpdate.await(Duration.ofSeconds(5));
            b.commit();
            mqAcks("B 소비자: shipment s1 v2 / IN_TRANSIT (동시 전달)");
            Object version = lab.one("SELECT version FROM shipment WHERE id = 's1'");

            // B는 where 문으로 인해 대기한다.
            String 예측_대기 = "true";
            // B는 version 을 만족하지 못하기 때문에 0
            String 예측_B영향행 = "0";
            // 3 으로 갱신된다.
            String 예측_최종버전 = "3";
            Predict.확인("A 가 커밋하기 전, B 의 UPDATE(v2) 는 기다리나? (답: true / false)", 예측_대기, bWaited);
            Predict.확인("A 가 커밋한 뒤 풀려난 B 의 UPDATE 영향 행 수는? (답: 숫자)", 예측_B영향행, bRows);
            Predict.확인("최종 version 은? (답: 숫자)", 예측_최종버전, version);
        }
    }

    @Test
    void Q08_두_세션이_같은_키에_v2_와_v3_를_반대_순서로() {
        Timeline.reset("Q08 조건부 UPDATE — A 가 v2 를 반영하는 중(커밋 전)에 B 가 v3 를 보낸다");
        try (Session a = lab.session("A"); Session b = lab.session("B")) {
            a.begin(READ_COMMITTED);
            b.begin(READ_COMMITTED);
            mqDelivers("A 소비자: shipment s1 v2 / IN_TRANSIT", () -> a.update(CONDITIONAL.formatted(2, "IN_TRANSIT", 2)));
            Pending<Integer> bUpdate = mqDelivers("B 소비자: shipment s1 v3 / DELIVERED (동시 전달)", () -> b.updateAsync(CONDITIONAL.formatted(3, "DELIVERED", 3)));
            boolean bWaited = bUpdate.isWaiting(GRACE);
            a.commit();
            mqAcks("A 소비자: shipment s1 v2 / IN_TRANSIT");
            int bRows = bUpdate.await(Duration.ofSeconds(5));
            b.commit();
            mqAcks("B 소비자: shipment s1 v3 / DELIVERED (동시 전달)");
            Object version = lab.one("SELECT version FROM shipment WHERE id = 's1'");

            // B가 대기한다.
            // where 문은 다르지만, A가 조건을 만족해서 먼저 점유하기 때문에 대기
            String 예측_대기 = "true";

            // B는 version 조건을 만족하기 때문에 1
            String 예측_B영향행 = "1";
            // version 갱신
            String 예측_최종버전 = "3";
            Predict.확인("A 가 커밋하기 전, B 의 UPDATE(v3) 는 기다리나? (답: true / false)", 예측_대기, bWaited);
            Predict.확인("A 가 커밋한 뒤 풀려난 B 의 UPDATE 영향 행 수는? (답: 숫자)", 예측_B영향행, bRows);
            Predict.확인("최종 version 은? (Q07 과 같은가 · 답: 숫자)", 예측_최종버전, version);
        }
    }

    @Test
    void Q09_같은_messageId_가_동시에_오고_먼저_온_쪽이_롤백하면() {
        Timeline.reset("Q09 inbox INSERT … ON CONFLICT DO NOTHING — A 가 넣는 중(커밋 전)에 B 가 같은 messageId 를 넣는다");
        try (Session a = lab.session("A"); Session b = lab.session("B")) {
            a.begin(READ_COMMITTED);
            b.begin(READ_COMMITTED);
            mqDelivers("A 소비자: messageId=m-1", () -> a.update("INSERT INTO inbox (message_id) VALUES ('m-1') ON CONFLICT DO NOTHING"));
            Pending<Integer> bInsert = mqDelivers("B 소비자: messageId=m-1 (동시 전달)", () -> b.updateAsync("INSERT INTO inbox (message_id) VALUES ('m-1') ON CONFLICT DO NOTHING"));
            boolean bWaited = bInsert.isWaiting(GRACE);
            a.rollback(); // A 소비자의 이후 반영 실패를 가정해 inbox INSERT도 함께 롤백한다.
            mqNacks("A 소비자: messageId=m-1 (DB ROLLBACK)");
            int bRows = bInsert.await(Duration.ofSeconds(5));
            b.commit();
            mqAcks("B 소비자: messageId=m-1 (동시 전달)");

            // 아직 없지만, UNIQUE INDEX 이므로 B는 대기를 하게 된다.
            String 예측_대기 = "true";
            // 롤백이 되었으므로, 1이 된다.
            String 예측_B영향행 = "1";
            Predict.확인("A 가 끝나기 전, B 의 INSERT 는 기다리나? (답: true / false)", 예측_대기, bWaited);
            Predict.확인("A 가 롤백한 뒤 풀려난 B 의 INSERT 영향 행 수는? (답: 숫자)", 예측_B영향행, bRows);
        }
    }

    @Test
    void Q10_REPEATABLE_READ_에서_동시_이벤트를_반영하면() {
        Timeline.reset("Q10 REPEATABLE READ — A 가 v3 반영 중일 때 B 가 더 최신 v4 를 반영한다");
        try (Session a = lab.session("A"); Session b = lab.session("B")) {
            a.begin(READ_COMMITTED);
            b.begin(REPEATABLE_READ);

            mqDelivers("A 소비자: shipment s1 v3 / IN_TRANSIT", () -> a.update(CONDITIONAL.formatted(3, "IN_TRANSIT", 3)));
            // B의 첫 실제 SQL이다. 여기서 고정 스냅샷이 잡히고, A의 미커밋 v3는 보이지 않는다.
            Pending<Integer> bUpdate = mqDelivers("B 소비자: shipment s1 v4 / DELIVERED (REPEATABLE READ)", () -> b.updateAsync(CONDITIONAL.formatted(4, "DELIVERED", 4)));
            boolean bWaited = bUpdate.isWaiting(GRACE);
            a.commit();
            mqAcks("A 소비자: shipment s1 v3 / IN_TRANSIT");

            String bOutcome;
            try {
                bUpdate.await(Duration.ofSeconds(5));
                b.commit();
                mqAcks("B 소비자: shipment s1 v4 / DELIVERED (REPEATABLE READ)");
                bOutcome = "성공";
            } catch (SqlFailure failure) {
                b.rollback();
                Timeline.note("B DB ROLLBACK — REPEATABLE READ 스냅샷 충돌");
                mqNacks("B 소비자: shipment s1 v4 / DELIVERED (REPEATABLE READ)");
                bOutcome = "에러 " + failure.sqlState();
            }
            Object version = lab.one("SELECT version FROM shipment WHERE id = 's1'");

            // B는 Q07과 동일하게 A가 커밋할 때까지 대기한다.
            String 예측_대기 = "true";
            // B의 스냅샷에는 version=0이 보이지만, 대기 후 실제 행은 A가 version=3으로 바꿨다.
            // B가 더 최신 v4를 반영하려 해도, REPEATABLE READ에서는 과거 스냅샷 이후 변경된 행을 갱신할 수 없다.
            // -> 40001 ERROR: could not serialize access due to concurrent update
            String 예측_B결과 = "에러 40001";

            // A만 반영된다. READ COMMITTED였다면 B(v4)가 이어서 반영됐을 것이다.
            String 예측_최종버전 = "3";
            Predict.확인("A 가 커밋하기 전, B 의 UPDATE(v4) 는 기다리나? (답: true / false)", 예측_대기, bWaited);
            Predict.확인("A 가 커밋한 뒤 B 의 UPDATE(v4) 는? (성공할 수 있을 만큼 새 이벤트인데도…? · 답: \"성공\" 또는 \"에러 \" + SQLState)", 예측_B결과, bOutcome);
            Predict.확인("B 롤백 뒤 최종 version 은? (답: 숫자)", 예측_최종버전, version);
        }
    }
}
