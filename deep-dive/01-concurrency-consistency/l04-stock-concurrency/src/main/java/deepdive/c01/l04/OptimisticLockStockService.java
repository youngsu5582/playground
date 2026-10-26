package deepdive.c01.l04;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.SQLException;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.function.Supplier;

/** 낙관 락 — "읽은 뒤 아무도 안 고쳤다" 를 version 으로 확인하고, 고쳤으면 처음부터 다시. */
public final class OptimisticLockStockService implements StockService {

    /**
     * 충돌이 계속되면 언젠가는 포기해야 한다.
     * 경합이 심한 행에서 낙관 락이 불리한 이유가 여기 있다 — 진 쪽은 읽기부터 전부 다시 한다.
     *
     * <p>20 의 근거: version 은 판매가 성공할 때만 오르므로, 재고 N 이면 한 구매자는 최대 N 번 진다 (N+1 번째엔 품절을 읽는다).
     * 재고 10 에 구매자 50 인 구현 테스트는 상한에 닿지 않는다. 재고가 충분한 채 몰리면 N 이 커서 상한에 닿을 수 있다 (관찰 표의 '재시도소진').
     */
    public static final int MAX_ATTEMPTS = 20;

    private final Supplier<Connection> db;
    private final Runnable betweenReadAndWrite;
    private final AtomicInteger retries = new AtomicInteger();

    /** @param betweenReadAndWrite 읽기와 쓰기 사이에 실행된다 — 실서비스의 네트워크·로직 시간. 테스트가 여기서 남의 갱신을 끼워 넣는다 */
    public OptimisticLockStockService(Supplier<Connection> db, Runnable betweenReadAndWrite) {
        this.db = db;
        this.betweenReadAndWrite = betweenReadAndWrite;
    }

    public OptimisticLockStockService(Supplier<Connection> db) {
        this(db, () -> {});
    }

    /** 지금까지 version 충돌 때문에 다시 시도한 횟수. 관찰 표에 찍힌다. */
    public int retries() {
        return retries.get();
    }

    /**
     * TODO(구현) version 이 그대로일 때만 쓰고, 충돌하면 읽기부터 다시 한다. 상한을 넘으면 예외로 명확히 실패한다.
     *
     * <h3>지금 무엇이 문제인가</h3>
     * 지금은 version 을 보지 않고 "읽은 값 - qty" 를 그냥 쓴다. 읽은 뒤에 남이 먼저 팔았어도 그 판매를 덮어써 버린다 (갱신 손실).
     * {@code StockImplementTest} 가 초과 판매 · 재시도 소진 두 가지를 잡는다.
     *
     * <h3>할 일</h3>
     * <ol>
     *   <li>{@code StockTable.read(c, sku, false)} 로 qty · version 을 읽는다. 행이 없거나 재고가 모자라면 false</li>
     *   <li>{@code betweenReadAndWrite.run()}</li>
     *   <li>{@code UPDATE stock SET qty = ?, version = version + 1 WHERE sku = ? AND version = ?} — 읽은 version 을 조건으로</li>
     *   <li>영향 행 1 이면 true. 0 이면 누가 먼저 고친 것 → {@code retries} 를 1 올리고 1번부터 다시</li>
     *   <li>{@link #MAX_ATTEMPTS} 번째 시도도 충돌이면 {@code throw new IllegalStateException("…")} — 재고 부족(false)과 구분되어야 한다</li>
     * </ol>
     *
     * <h3>헷갈리기 쉬운 곳</h3>
     * <ul>
     *   <li>다시 할 때는 <b>다시 읽는다</b> — 처음 읽은 qty 로 재계산하면 같은 충돌이 반복된다</li>
     *   <li>재시도 후 다시 읽었더니 재고가 모자라면? 예외가 아니라 false (정상적인 품절)</li>
     *   <li>UPDATE 의 WHERE 에 {@code qty >= ?} 를 더해도 되지만, 이 연습의 요점은 version 이다</li>
     *   <li>READ COMMITTED 에서 쓴다. REPEATABLE READ 면 version 비교 전에 엔진이 40001 로 먼저 막는다 (예측 Q05)</li>
     * </ul>
     */
    @Override
    public boolean reserve(String sku, int qty) {
        try (Connection c = db.get()) {
            StockTable.Row row = StockTable.read(c, sku, false);
            if (row == null || row.qty() < qty) return false;
            betweenReadAndWrite.run();
            try (PreparedStatement ps = c.prepareStatement("UPDATE stock SET qty = ? WHERE sku = ?")) {
                ps.setInt(1, row.qty() - qty);
                ps.setString(2, sku);
                ps.executeUpdate();
            }
            return true;
        } catch (SQLException e) {
            throw new IllegalStateException(e);
        }
    }
}
