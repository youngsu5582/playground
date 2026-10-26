package deepdive.c01.l04;

import deepdive.testkit.ConcurrencyHarness;
import deepdive.testkit.ConcurrencyHarness.Outcome;
import deepdive.testkit.PostgresLab;
import deepdive.testkit.Timeline;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.util.function.Function;

/**
 * [관찰] 단언하지 않는다 — 세 전략의 걸린 시간 · 재시도 수가 표로 찍힌다. 숫자는 실행마다 다르다.
 * 찍힌 숫자를 NOTES.md 에 옮겨 적고, 왜 그런 모양인지 한두 줄로 해석한다 (README ③).
 *
 * <p>실행: {@code ./gradlew :01-concurrency-consistency:l04-stock-concurrency:test --tests '*Observation*'}
 */
@DisplayName("[관찰] 01.04 세 전략의 걸린 시간 · 재시도 수")
class StockObservationTest {

    final PostgresLab lab = PostgresLab.get();

    @BeforeEach
    void reset() {
        lab.exec("DROP TABLE IF EXISTS stock",
                "CREATE TABLE stock (sku text PRIMARY KEY, qty int NOT NULL, version int NOT NULL DEFAULT 0)");
    }

    @Test
    void 경합_세기별_걸린_시간과_재시도_수() {
        Timeline.reset("관찰 — 전략 × 경합 세기");
        Timeline.raw("");
        Timeline.raw(String.format("  %-26s %-9s %6s %6s %8s %8s %8s %9s", "시나리오", "전략", "성공", "품절", "재시도소진", "남은재고", "재시도", "걸린ms"));
        scenario("경합 낮음 (구매자 4 · 재고 충분)", 4, 1000);
        scenario("경합 높음 (구매자 50 · 재고 충분)", 50, 1000);
        scenario("품절 경쟁 (구매자 50 · 재고 10)", 50, 10);
        Timeline.raw("");
    }

    void scenario(String label, int buyers, int stock) {
        run(label, "원자 UPDATE", buyers, stock, db -> new AtomicUpdateStockService(db), s -> "-");
        run(label, "낙관 락", buyers, stock, db -> new OptimisticLockStockService(db),
                s -> String.valueOf(((OptimisticLockStockService) s).retries()));
        run(label, "비관 락", buyers, stock, db -> new PessimisticLockStockService(db), s -> "-");
    }

    void run(String label, String strategy, int buyers, int stock,
             Function<java.util.function.Supplier<java.sql.Connection>, StockService> factory, Function<StockService, String> retries) {
        lab.exec("DELETE FROM stock", "INSERT INTO stock VALUES ('A', " + stock + ", 0)");
        StockService service = factory.apply(lab::connect);
        Outcome<Boolean> outcome = ConcurrencyHarness.runConcurrently(buyers, () -> service.reserve("A", 1));
        long sold = outcome.successes().stream().filter(ok -> ok).count();
        long soldOut = outcome.successes().size() - sold;
        Object left = lab.one("SELECT qty FROM stock WHERE sku = 'A'");
        Timeline.raw(String.format("  %-26s %-9s %6d %6d %8d %8s %8s %9d",
                label, strategy, sold, soldOut, outcome.failures().size(), left, retries.apply(service), outcome.elapsed().toMillis()));
    }
}
