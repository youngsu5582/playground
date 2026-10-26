package deepdive.c01.l04;

import deepdive.testkit.ConcurrencyHarness;
import deepdive.testkit.ConcurrencyHarness.Outcome;
import deepdive.testkit.PostgresLab;
import deepdive.testkit.Timeline;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.function.Supplier;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.catchThrowable;
import static org.assertj.core.api.Assertions.fail;

/**
 * [구현] 세 {@link StockService} 구현의 {@code reserve} 를 채우면 초록이 된다. 진짜 PostgreSQL 위에서 진짜 동시성으로 돈다.
 * 결과 검사 셋(전략마다 재고 10 · 구매자 50) + 재고 부족 가드 + 낙관 락 전용 둘.
 */
@DisplayName("[구현] 01.04 StockService#reserve — 재고 10 · 구매자 50 동시에 초과 판매 막기")
class StockImplementTest {

    static final int STOCK = 10;
    static final int BUYERS = 50;
    static final int ROUNDS = 5;

    final PostgresLab lab = PostgresLab.get();

    @BeforeEach
    void reset() {
        lab.exec("DROP TABLE IF EXISTS stock",
                "CREATE TABLE stock (sku text PRIMARY KEY, qty int NOT NULL, version int NOT NULL DEFAULT 0)");
    }

    void stockOf(int qty) {
        lab.exec("DELETE FROM stock", "INSERT INTO stock VALUES ('A', " + qty + ", 0)");
    }

    int qtyNow() {
        return ((Number) lab.one("SELECT qty FROM stock WHERE sku = 'A'")).intValue();
    }

    /** 재고 10 에 구매자 50 이 같은 순간에 1개씩. 경쟁은 확률적이라 5회 돈다. */
    void assertNoOversell(String 전략, String 고칠곳, Supplier<StockService> factory) {
        for (int round = 1; round <= ROUNDS; round++) {
            Timeline.reset("구현 확인 " + 전략 + " " + round + "회차 — 재고 " + STOCK + " · 구매자 " + BUYERS);
            stockOf(STOCK);
            StockService service = factory.get();
            Outcome<Boolean> outcome = ConcurrencyHarness.runConcurrently(BUYERS, () -> service.reserve("A", 1));
            long sold = outcome.successes().stream().filter(ok -> ok).count();
            int left = qtyNow();
            if (!outcome.failures().isEmpty()) {
                fail("""

                        예외가 났다: %d회차 — %s
                          고칠 곳: %s""".formatted(round, outcome.failures().getFirst(), 고칠곳));
            }
            if (sold > STOCK) {
                fail("""

                        정합성 깨짐: %d회차 — 재고 %d개를 %d명에게 팔았다 (초과 판매 %d) · 최종 재고 %d.
                          읽고-확인-쓰기 사이의 틈에 다른 구매자가 끼어들어, 모두 "재고 있네" 를 보고 팔았다.
                          고칠 곳: %s""".formatted(round, STOCK, sold, sold - STOCK, left, 고칠곳));
            }
            if (sold != STOCK || left != 0) {
                fail("""

                        정합성 깨짐: %d회차 — 성공 %d명 · 최종 재고 %d (기대: 성공 %d · 재고 0).
                          팔린 만큼 재고가 줄지 않았거나(갱신 손실), 재고가 있는데 거절했다.
                          고칠 곳: %s""".formatted(round, sold, left, STOCK, 고칠곳));
            }
        }
    }

    // ── 결과 검사: 전략마다 ───────────────────────────────────

    @Test
    void 원자_UPDATE_는_50명이_동시에_사도_정확히_10개만_팔린다() {
        assertNoOversell("원자 UPDATE", "AtomicUpdateStockService#reserve — 확인과 차감을 UPDATE 한 문장으로",
                () -> new AtomicUpdateStockService(lab::connect));
    }

    @Test
    void 낙관_락은_50명이_동시에_사도_정확히_10개만_팔린다() {
        assertNoOversell("낙관 락", "OptimisticLockStockService#reserve — UPDATE … WHERE version = ? 의 영향 행 수를 보고 다시",
                () -> new OptimisticLockStockService(lab::connect));
    }

    @Test
    void 비관_락은_50명이_동시에_사도_정확히_10개만_팔린다() {
        assertNoOversell("비관 락", "PessimisticLockStockService#reserve — 트랜잭션 안에서 SELECT … FOR UPDATE",
                () -> new PessimisticLockStockService(lab::connect));
    }

    // ── 가드: 빈칸 상태에서도 초록이어야 한다 ─────────────────────

    @Test
    void 재고가_모자라면_세_전략_모두_거절하고_재고는_그대로다() {
        List<StockService> strategies = List.of(
                new AtomicUpdateStockService(lab::connect),
                new OptimisticLockStockService(lab::connect),
                new PessimisticLockStockService(lab::connect));
        for (StockService s : strategies) {
            stockOf(2);
            assertThat(s.reserve("A", 3)).as("%s: 재고 2 에 3개는 거절", s.getClass().getSimpleName()).isFalse();
            assertThat(qtyNow()).as("%s: 거절하면 재고는 그대로", s.getClass().getSimpleName()).isEqualTo(2);
            assertThat(s.reserve("A", 2)).as("%s: 재고 2 에 2개는 성공", s.getClass().getSimpleName()).isTrue();
            assertThat(qtyNow()).isZero();
        }
    }

    // ── 낙관 락 전용 ────────────────────────────────────────

    @Test
    void 낙관_락_재시도_상한을_넘으면_명확히_실패한다() {
        stockOf(5);
        AtomicInteger attempts = new AtomicInteger();
        // 읽을 때마다 다른 누군가가 version 만 올린다 — 영원히 충돌
        var service = new OptimisticLockStockService(lab::connect, () -> {
            attempts.incrementAndGet();
            lab.exec("UPDATE stock SET version = version + 1 WHERE sku = 'A'");
        });
        Timeline.reset("구현 확인 — 읽을 때마다 version 이 올라가는 낙관 락");
        Throwable thrown = catchThrowable(() -> service.reserve("A", 1));
        assertThat(thrown)
                .as("""

                        재시도 상한을 넘었는데 예외가 없다 — 계속 충돌하면 무한히 돌지 말고 예외로 명확히 실패해야 한다.
                          재고가 모자라 false 를 돌려주는 것과 구분되어야 한다 (재고는 5 개 남아 있다).
                          고칠 곳: OptimisticLockStockService#reserve — MAX_ATTEMPTS 번째 충돌이면 IllegalStateException""")
                .isInstanceOf(IllegalStateException.class);
        assertThat(attempts.get())
                .as("상한(MAX_ATTEMPTS)만큼 시도하고 포기해야 한다")
                .isEqualTo(OptimisticLockStockService.MAX_ATTEMPTS);
        assertThat(qtyNow()).as("실패했으면 재고는 그대로").isEqualTo(5);
    }

    /** 방법 검사 — 충돌을 만나면 "다시 읽고" 시도한다. 결과 검사는 위의 50명 테스트가 맡는다. */
    @Test
    void 방법_검사_낙관_락은_충돌을_만나면_다시_읽고_다시_쓴다() {
        stockOf(5);
        AtomicInteger calls = new AtomicInteger();
        // 첫 시도에서만 다른 구매자가 1개 먼저 판다
        var service = new OptimisticLockStockService(lab::connect, () -> {
            if (calls.incrementAndGet() == 1) {
                lab.exec("UPDATE stock SET qty = qty - 1, version = version + 1 WHERE sku = 'A'");
            }
        });
        Timeline.reset("구현 확인 — 첫 시도에서 남이 먼저 1개 팔았다");
        assertThat(service.reserve("A", 1)).isTrue();
        assertThat(qtyNow())
                .as("5 - 남이 판 1 - 내가 판 1 = 3 이어야 한다. 4 라면 남의 판매를 덮어썼다 (version 을 안 봤다)")
                .isEqualTo(3);
        assertThat(service.retries()).as("충돌 1번 → 재시도 1번").isEqualTo(1);
    }
}
