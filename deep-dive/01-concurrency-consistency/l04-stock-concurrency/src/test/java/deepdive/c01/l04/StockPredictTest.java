package deepdive.c01.l04;

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
import static deepdive.testkit.Session.Isolation.REPEATABLE_READ;

/**
 * [예측] 각 테스트의 {@code String 예측 = "?";} 를 <b>돌리기 전에</b> 내 답으로 바꾼다.
 * 답 형식은 질문 끝 괄호에 있다 — 숫자는 "1", 예/아니오는 "true"/"false", 결과는 "성공"/"에러 40001" 처럼.
 * 띄어쓰기·대소문자는 상관없다.
 *
 * <p>모든 시나리오는 진짜 PostgreSQL 16 에서 세션 두 개(A, B)로 돈다. 출력에 찍히는 타임라인을 같이 읽는다.
 * 세 전략(원자 UPDATE · 낙관 락 · 비관 락)이 "읽고-확인-쓰기 사이의 틈" 을 각각 어떻게 닫는지가 주제다.
 *
 * <pre>
 * stock(sku, qty, version) — sku 'A' 재고 1, version 0 (Q08 만 'B' 도 있다)
 * </pre>
 */
@DisplayName("[예측] 01.04 재고 동시 차감 — 8문항")
class StockPredictTest {

    static final Duration GRACE = Duration.ofMillis(300);
    final PostgresLab lab = PostgresLab.get();

    @BeforeEach
    void reset() {
        lab.exec(
                "DROP TABLE IF EXISTS stock",
                "CREATE TABLE stock (sku text PRIMARY KEY, qty int NOT NULL, version int NOT NULL DEFAULT 0)",
                "INSERT INTO stock VALUES ('A', 1, 0), ('B', 1, 0)");
    }

    // ── 1. 틈 ────────────────────────────────────────────────

    @Test
    void Q01_순진한_읽고_확인하고_쓰기() {
        Timeline.reset("Q01 읽고-확인-쓰기 — 둘 다 재고 1 을 읽고 각자 차감한다");
        try (Session a = lab.session("A"); Session b = lab.session("B")) {
            int seenByA = (Integer) a.one("SELECT qty FROM stock WHERE sku = 'A'");
            int seenByB = (Integer) b.one("SELECT qty FROM stock WHERE sku = 'A'");
            a.update("UPDATE stock SET qty = ? WHERE sku = 'A'", seenByA - 1); // 1 - 1
            b.update("UPDATE stock SET qty = ? WHERE sku = 'A'", seenByB - 1); // 1 - 1
            Object finalQty = lab.one("SELECT qty FROM stock WHERE sku = 'A'");

            String 예측 = "?";
            Predict.확인("A 도 B 도 \"성공\" 을 받았다 (2개 팔림). 최종 재고는? (처음 1 · 답: 숫자)", 예측, finalQty);
        }
    }

    // ── 2. 원자적 조건부 UPDATE ───────────────────────────────

    @Test
    void Q02_원자적_UPDATE_A_가_커밋하면() {
        Timeline.reset("Q02 UPDATE … WHERE qty >= 1 — A 가 커밋하면 B 는");
        try (Session a = lab.session("A"); Session b = lab.session("B")) {
            a.begin(READ_COMMITTED);
            b.begin(READ_COMMITTED);
            a.update("UPDATE stock SET qty = qty - 1 WHERE sku = 'A' AND qty >= 1"); // 행 락을 잡은 채 커밋 전
            Pending<Integer> bUpdate = b.updateAsync("UPDATE stock SET qty = qty - 1 WHERE sku = 'A' AND qty >= 1");
            boolean bWaited = bUpdate.isWaiting(GRACE);
            a.commit();
            int bRows = bUpdate.await(Duration.ofSeconds(5));
            b.commit();

            String 예측_대기 = "?";
            String 예측_행수 = "?";
            Predict.확인("A 가 커밋하기 전, B 의 UPDATE 는 기다리나? (답: true / false)", 예측_대기, bWaited);
            Predict.확인("A 커밋 뒤 B 의 UPDATE 영향 행 수는? (재고는 1 이었고 A 가 가져갔다 · 답: 숫자)", 예측_행수, bRows);
        }
    }

    @Test
    void Q03_원자적_UPDATE_A_가_롤백하면() {
        Timeline.reset("Q03 UPDATE … WHERE qty >= 1 — A 가 롤백하면 B 는");
        try (Session a = lab.session("A"); Session b = lab.session("B")) {
            a.begin(READ_COMMITTED);
            b.begin(READ_COMMITTED);
            a.update("UPDATE stock SET qty = qty - 1 WHERE sku = 'A' AND qty >= 1");
            Pending<Integer> bUpdate = b.updateAsync("UPDATE stock SET qty = qty - 1 WHERE sku = 'A' AND qty >= 1");
            bUpdate.isWaiting(GRACE);
            a.rollback();
            int bRows = bUpdate.await(Duration.ofSeconds(5));
            b.commit();
            Object finalQty = lab.one("SELECT qty FROM stock WHERE sku = 'A'");

            String 예측_행수 = "?";
            String 예측_재고 = "?";
            Predict.확인("A 가 커밋 대신 ROLLBACK 하면 B 의 UPDATE 영향 행 수는? (답: 숫자)", 예측_행수, bRows);
            Predict.확인("최종 재고는? (답: 숫자)", 예측_재고, finalQty);
        }
    }

    // ── 3. 낙관 락 ──────────────────────────────────────────

    @Test
    void Q04_낙관_락_두_번째_쪽은() {
        Timeline.reset("Q04 낙관 락 — 둘 다 version 0 을 읽고 UPDATE … WHERE version = 0");
        try (Session a = lab.session("A"); Session b = lab.session("B")) {
            a.begin(READ_COMMITTED);
            b.begin(READ_COMMITTED);
            a.one("SELECT qty, version FROM stock WHERE sku = 'A'"); // qty 1, version 0
            b.one("SELECT qty, version FROM stock WHERE sku = 'A'"); // qty 1, version 0
            a.update("UPDATE stock SET qty = 0, version = version + 1 WHERE sku = 'A' AND version = 0");
            Pending<Integer> bUpdate = b.updateAsync("UPDATE stock SET qty = 0, version = version + 1 WHERE sku = 'A' AND version = 0");
            boolean bWaited = bUpdate.isWaiting(GRACE);
            a.commit();
            int bRows = bUpdate.await(Duration.ofSeconds(5));
            b.commit();

            String 예측_대기 = "?";
            String 예측_행수 = "?";
            Predict.확인("A 가 커밋하기 전, B 의 UPDATE 는 기다리나? (답: true / false)", 예측_대기, bWaited);
            Predict.확인("A 커밋 뒤 B 의 UPDATE 영향 행 수는? (답: 숫자)", 예측_행수, bRows);
        }
    }

    @Test
    void Q05_낙관_락을_REPEATABLE_READ_에서_쓰면() {
        Timeline.reset("Q05 낙관 락 + REPEATABLE READ — B 의 스냅샷 이후 A 가 고쳤다");
        try (Session a = lab.session("A"); Session b = lab.session("B")) {
            b.begin(REPEATABLE_READ);
            b.one("SELECT qty, version FROM stock WHERE sku = 'A'"); // B 의 스냅샷이 여기서 잡힌다
            a.update("UPDATE stock SET qty = 0, version = version + 1 WHERE sku = 'A' AND version = 0"); // autocommit
            String outcome;
            try {
                b.update("UPDATE stock SET qty = 0, version = version + 1 WHERE sku = 'A' AND version = 0");
                outcome = "성공";
            } catch (SqlFailure f) {
                outcome = "에러 " + f.sqlState();
            }
            b.rollback();

            String 예측 = "?";
            Predict.확인("B 의 UPDATE 는? (0행이 아니라…? · 답: \"성공\" 또는 \"에러 \" + SQLState 다섯 글자)", 예측, outcome);
        }
    }

    // ── 4. 비관 락 ──────────────────────────────────────────

    @Test
    void Q06_FOR_UPDATE_두_번째_쪽은() {
        Timeline.reset("Q06 SELECT … FOR UPDATE — A 가 잠근 행을 B 도 FOR UPDATE 로 읽는다");
        try (Session a = lab.session("A"); Session b = lab.session("B")) {
            a.begin(READ_COMMITTED);
            b.begin(READ_COMMITTED);
            a.one("SELECT qty FROM stock WHERE sku = 'A' FOR UPDATE");
            Pending<Object> bRead = b.async(() -> b.one("SELECT qty FROM stock WHERE sku = 'A' FOR UPDATE"));
            boolean bWaited = bRead.isWaiting(GRACE);
            a.update("UPDATE stock SET qty = 0 WHERE sku = 'A'");
            a.commit();
            Object bSaw = bRead.await(Duration.ofSeconds(5));
            b.rollback();

            String 예측_대기 = "?";
            String 예측_값 = "?";
            Predict.확인("A 가 커밋하기 전, B 의 SELECT … FOR UPDATE 는 기다리나? (답: true / false)", 예측_대기, bWaited);
            Predict.확인("A 가 qty 를 0 으로 바꾸고 커밋한 뒤, B 가 읽은 qty 는? (처음 1 · 답: 숫자)", 예측_값, bSaw);
        }
    }

    @Test
    void Q07_FOR_UPDATE_중인_행을_그냥_SELECT_하면() {
        Timeline.reset("Q07 FOR UPDATE 로 잠근 행을 평범한 SELECT 로 읽는다");
        try (Session a = lab.session("A"); Session b = lab.session("B")) {
            a.begin(READ_COMMITTED);
            a.one("SELECT qty FROM stock WHERE sku = 'A' FOR UPDATE");
            a.update("UPDATE stock SET qty = 0 WHERE sku = 'A'"); // 커밋 전
            b.begin(READ_COMMITTED);
            Pending<Object> bRead = b.async(() -> b.one("SELECT qty FROM stock WHERE sku = 'A'"));
            boolean bWaited = bRead.isWaiting(GRACE);
            Object bSaw = bRead.await(Duration.ofSeconds(5));
            a.rollback();
            b.rollback();

            String 예측_대기 = "?";
            String 예측_값 = "?";
            Predict.확인("B 의 평범한 SELECT 는 A 의 락을 기다리나? (답: true / false)", 예측_대기, bWaited);
            Predict.확인("B 가 읽은 qty 는? (A 는 0 으로 바꾸고 커밋 전 · 답: 숫자)", 예측_값, bSaw);
        }
    }

    // ── 5. 락의 단위 ────────────────────────────────────────

    @Test
    void Q08_다른_SKU_는_서로_기다리나() {
        Timeline.reset("Q08 행 락의 단위 — 다른 SKU 끼리");
        try (Session a = lab.session("A"); Session b = lab.session("B")) {
            a.begin(READ_COMMITTED);
            b.begin(READ_COMMITTED);
            a.update("UPDATE stock SET qty = qty - 1 WHERE sku = 'A' AND qty >= 1"); // 커밋 전
            Pending<Integer> bUpdate = b.updateAsync("UPDATE stock SET qty = qty - 1 WHERE sku = 'B' AND qty >= 1");
            boolean bWaited = bUpdate.isWaiting(GRACE);
            a.rollback();
            b.rollback();

            String 예측 = "?";
            Predict.확인("A 는 SKU 'A' 를, B 는 SKU 'B' 를 차감한다. B 의 UPDATE 는 기다리나? (답: true / false)", 예측, bWaited);
        }
    }
}
