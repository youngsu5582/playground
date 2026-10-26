package deepdive.c01.l04;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.SQLException;
import java.util.function.Supplier;

/** 비관 락 — 읽을 때부터 행을 잠가서, 판단하는 동안 아무도 못 고치게. */
public final class PessimisticLockStockService implements StockService {

    private final Supplier<Connection> db;

    public PessimisticLockStockService(Supplier<Connection> db) {
        this.db = db;
    }

    /**
     * TODO(구현) 트랜잭션 안에서 행을 {@code FOR UPDATE} 로 잠그고 읽은 뒤 확인하고 쓴다.
     *
     * <h3>지금 무엇이 문제인가</h3>
     * 지금은 autocommit 으로 평범한 SELECT 를 한다 — 읽기는 락을 잡지 않으므로(MVCC) 다른 구매자가 얼마든지 끼어든다 (예측 Q07).
     * {@code StockImplementTest} 가 초과 판매를 잡는다.
     *
     * <h3>할 일</h3>
     * <ol>
     *   <li>{@code c.setAutoCommit(false)}</li>
     *   <li>{@code StockTable.read(c, sku, true)} — 이 순간 행 락을 잡는다. 두 번째 구매자는 여기서 기다린다 (예측 Q06)</li>
     *   <li>행이 없거나 재고가 모자라면 {@code c.rollback()} 하고 false</li>
     *   <li>{@code UPDATE stock SET qty = ? WHERE sku = ?} → {@code c.commit()} → true</li>
     *   <li>{@code SQLException} 이 나면 {@code c.rollback()} 후 {@code IllegalStateException}</li>
     * </ol>
     *
     * <h3>헷갈리기 쉬운 곳</h3>
     * <ul>
     *   <li>락은 commit/rollback 때 풀린다 — 어느 경로로 나가든 둘 중 하나를 명시한다. 이 코드는 커넥션을 닫으면 서버가 정리하지만, 커넥션 풀에 트랜잭션이 열린 채 돌려주면 락이 남아 다음 구매자가 기다린다</li>
     *   <li>이 트랜잭션 안에서 외부 API 를 부르면 그동안 모든 구매자가 줄을 선다</li>
     *   <li>기다렸던 구매자가 읽는 qty 는 앞사람이 커밋한 <b>최신 값</b>이다 — 그래서 확인이 틀리지 않는다</li>
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
