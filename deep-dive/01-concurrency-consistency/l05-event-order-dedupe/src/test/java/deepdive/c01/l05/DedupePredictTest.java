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

import static deepdive.testkit.Session.Isolation.READ_COMMITTED;

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
@DisplayName("[예측] 01.05 이벤트 중복 · 순서 — 9문항")
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

    // ── 1. 막지 않으면 ──────────────────────────────────────────

    @Test
    void Q01_같은_이벤트가_두_번_도착하면() {
        Timeline.reset("Q01 inbox 없음 — 같은 이벤트(SHIPPED v1)가 두 번 도착한다");
        try (Session a = lab.session("A")) {
            a.update(BLIND.formatted(1, "SHIPPED"));
            a.update(BLIND.formatted(1, "SHIPPED")); // 브로커의 재전달
            Object count = a.one("SELECT change_count FROM shipment WHERE id = 's1'");

            String 예측 = "?";
            Predict.확인("알림 발송 같은 부수 효과는 change_count 로 센다. 같은 이벤트를 두 번 반영한 뒤의 change_count 는? (답: 숫자)", 예측, count);
        }
    }

    @Test
    void Q02_늦게_온_과거_이벤트() {
        Timeline.reset("Q02 version 비교 없음 — DELIVERED(v3) 다음에 IN_TRANSIT(v2) 가 늦게 도착한다");
        try (Session a = lab.session("A")) {
            a.update(BLIND.formatted(3, "DELIVERED"));
            a.update(BLIND.formatted(2, "IN_TRANSIT")); // 재시도 큐에서 늦게 흘러온 과거
            Object status = a.one("SELECT status FROM shipment WHERE id = 's1'");

            String 예측 = "?";
            Predict.확인("최종 status 는? (답: READY / IN_TRANSIT / DELIVERED 중 하나)", 예측, status);
        }
    }

    // ── 2. version 과 inbox 로 막기 ─────────────────────────────

    @Test
    void Q03_조건부_UPDATE_로_과거와_같은_버전을_보내면() {
        Timeline.reset("Q03 WHERE version < :v — v3 가 반영된 뒤 v2 와 v3 가 또 온다");
        try (Session a = lab.session("A")) {
            a.update(CONDITIONAL.formatted(3, "DELIVERED", 3));
            int staleRows = a.update(CONDITIONAL.formatted(2, "IN_TRANSIT", 2));
            int sameRows = a.update(CONDITIONAL.formatted(3, "DELIVERED", 3));

            String 예측_과거 = "?";
            String 예측_같은버전 = "?";
            Predict.확인("v3 가 이미 반영돼 있다. v2 를 보내는 UPDATE 의 영향 행 수는? (답: 숫자)", 예측_과거, staleRows);
            Predict.확인("같은 v3 를 한 번 더 보내는 UPDATE 의 영향 행 수는? (답: 숫자)", 예측_같은버전, sameRows);
        }
    }

    @Test
    void Q04_같은_messageId_를_inbox_에_두_번() {
        Timeline.reset("Q04 INSERT INTO inbox … ON CONFLICT DO NOTHING — 같은 messageId 두 번");
        try (Session a = lab.session("A")) {
            int first = a.update("INSERT INTO inbox (message_id) VALUES ('m-1') ON CONFLICT DO NOTHING");
            int second = a.update("INSERT INTO inbox (message_id) VALUES ('m-1') ON CONFLICT DO NOTHING");

            String 예측_첫번째 = "?";
            String 예측_두번째 = "?";
            Predict.확인("첫 번째 INSERT 의 영향 행 수는? (답: 숫자)", 예측_첫번째, first);
            Predict.확인("두 번째 INSERT 의 영향 행 수는? (에러가 아니다 · 답: 숫자)", 예측_두번째, second);
        }
    }

    // ── 3. 기록과 반영이 갈라지면 ───────────────────────────────

    @Test
    void Q05_inbox_를_먼저_커밋하고_반영에서_실패하면() {
        Timeline.reset("Q05 inbox 기록과 반영이 다른 트랜잭션 — 그 사이에 반영이 실패한다");
        try (Session a = lab.session("A")) {
            a.update("INSERT INTO inbox (message_id) VALUES ('m-9') ON CONFLICT DO NOTHING"); // autocommit — 여기서 이미 커밋
            lab.exec("ALTER TABLE shipment ADD CONSTRAINT maintenance CHECK (status <> 'DELIVERED')"); // 반영 쪽 장애
            try {
                a.update(BLIND.formatted(1, "DELIVERED"));
            } catch (SqlFailure expected) {
                Timeline.note("반영 실패 " + expected.sqlState() + " — 메시지는 이미 '처리됨' 으로 남았다");
            }
            lab.exec("ALTER TABLE shipment DROP CONSTRAINT maintenance"); // 장애가 풀렸다

            // 브로커가 같은 메시지를 다시 보낸다 — 앱은 inbox 가 0행이면 "이미 처리했다" 며 건너뛴다
            int redelivered = a.update("INSERT INTO inbox (message_id) VALUES ('m-9') ON CONFLICT DO NOTHING");
            if (redelivered == 1) a.update(BLIND.formatted(1, "DELIVERED"));
            Object status = a.one("SELECT status FROM shipment WHERE id = 's1'");

            String 예측_재전달 = "?";
            String 예측_상태 = "?";
            Predict.확인("재전달된 메시지의 inbox INSERT 영향 행 수는? (답: 숫자)", 예측_재전달, redelivered);
            Predict.확인("재전달을 처리한 뒤 shipment.status 는? (이벤트는 DELIVERED 를 말한다 · 답: READY / DELIVERED 중 하나)", 예측_상태, status);
        }
    }

    @Test
    void Q06_inbox_와_반영을_한_트랜잭션으로_묶으면() {
        Timeline.reset("Q06 inbox 기록과 반영이 한 트랜잭션 — 반영이 실패하면");
        try (Session a = lab.session("A")) {
            a.begin(READ_COMMITTED);
            a.update("INSERT INTO inbox (message_id) VALUES ('m-9') ON CONFLICT DO NOTHING");
            lab.exec("ALTER TABLE shipment ADD CONSTRAINT maintenance CHECK (status <> 'DELIVERED')");
            try {
                a.update(BLIND.formatted(1, "DELIVERED"));
            } catch (SqlFailure expected) {
                Timeline.note("반영 실패 " + expected.sqlState() + " — 앱은 롤백하고 예외를 던진다");
            }
            a.rollback();
            lab.exec("ALTER TABLE shipment DROP CONSTRAINT maintenance");

            a.begin(READ_COMMITTED);
            int redelivered = a.update("INSERT INTO inbox (message_id) VALUES ('m-9') ON CONFLICT DO NOTHING");
            if (redelivered == 1) a.update(BLIND.formatted(1, "DELIVERED"));
            a.commit();
            Object status = a.one("SELECT status FROM shipment WHERE id = 's1'");

            String 예측_재전달 = "?";
            String 예측_상태 = "?";
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
            a.update(CONDITIONAL.formatted(3, "DELIVERED", 3));
            Pending<Integer> bUpdate = b.updateAsync(CONDITIONAL.formatted(2, "IN_TRANSIT", 2));
            boolean bWaited = bUpdate.isWaiting(GRACE);
            a.commit();
            int bRows = bUpdate.await(Duration.ofSeconds(5));
            b.commit();
            Object version = lab.one("SELECT version FROM shipment WHERE id = 's1'");

            String 예측_대기 = "?";
            String 예측_B영향행 = "?";
            String 예측_최종버전 = "?";
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
            a.update(CONDITIONAL.formatted(2, "IN_TRANSIT", 2));
            Pending<Integer> bUpdate = b.updateAsync(CONDITIONAL.formatted(3, "DELIVERED", 3));
            boolean bWaited = bUpdate.isWaiting(GRACE);
            a.commit();
            int bRows = bUpdate.await(Duration.ofSeconds(5));
            b.commit();
            Object version = lab.one("SELECT version FROM shipment WHERE id = 's1'");

            String 예측_대기 = "?";
            String 예측_B영향행 = "?";
            String 예측_최종버전 = "?";
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
            a.update("INSERT INTO inbox (message_id) VALUES ('m-1') ON CONFLICT DO NOTHING");
            Pending<Integer> bInsert = b.updateAsync("INSERT INTO inbox (message_id) VALUES ('m-1') ON CONFLICT DO NOTHING");
            boolean bWaited = bInsert.isWaiting(GRACE);
            a.rollback(); // A 의 반영이 실패해 전체가 롤백됐다
            int bRows = bInsert.await(Duration.ofSeconds(5));
            b.commit();

            String 예측_대기 = "?";
            String 예측_B영향행 = "?";
            Predict.확인("A 가 끝나기 전, B 의 INSERT 는 기다리나? (답: true / false)", 예측_대기, bWaited);
            Predict.확인("A 가 롤백한 뒤 풀려난 B 의 INSERT 영향 행 수는? (답: 숫자)", 예측_B영향행, bRows);
        }
    }
}
