package deepdive.c01.l04;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.SQLException;
import java.util.function.Supplier;

/** 원자적 조건부 UPDATE — 확인과 차감을 SQL 한 문장에. */
public final class AtomicUpdateStockService implements StockService {

    private final Supplier<Connection> db;

    public AtomicUpdateStockService(Supplier<Connection> db) {
        this.db = db;
    }

    /**
     * TODO(구현) 확인과 차감을 한 문장으로 합쳐, 영향 행 수로 성공을 판단한다.
     *
     * <h3>지금 무엇이 문제인가</h3>
     * 지금은 "읽고 → 앱에서 확인 → 계산한 값을 쓰기" 세 단계다. 읽은 뒤 쓰기 전에 다른 구매자가 끼어들면
     * 둘 다 "재고 있네" 를 보고 둘 다 판다 (예측 Q01). {@code StockImplementTest} 가 이걸 잡는다.
     *
     * <h3>할 일</h3>
     * <ol>
     *   <li>한 문장: {@code UPDATE stock SET qty = qty - ? WHERE sku = ? AND qty >= ?}</li>
     *   <li>{@code executeUpdate()} 가 1 이면 true, 0 이면 false (재고 부족 — 예측 Q02)</li>
     *   <li>커넥션은 autocommit 그대로 — 문장 하나가 곧 트랜잭션이다</li>
     * </ol>
     *
     * <h3>헷갈리기 쉬운 곳</h3>
     * <ul>
     *   <li>{@code SET qty = ?} 에 앱이 계산한 값을 넣으면 안 된다 — 반드시 {@code qty - ?} (DB 가 최신 값으로 계산)</li>
     *   <li>조건 {@code qty >= ?} 를 빼면 음수 재고가 생긴다</li>
     *   <li>두 번째 구매자는 첫 번째가 커밋될 때까지 <b>기다렸다가</b> 최신 값으로 조건을 다시 본다 — 그래서 안전하다 (01.01 Q06)</li>
     * </ul>
     */
    @Override
    public boolean reserve(String sku, int qty) {
        try (Connection c = db.get()) {
            StockTable.Row row = StockTable.read(c, sku, false);
            if (row == null || row.qty() < qty) return false;
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
