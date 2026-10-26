package deepdive.c01.l06;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.SQLException;
import java.util.function.Supplier;

/**
 * 이체를 원장에 올린다 — 거래 한 건이 원장 두 줄(차변 -금액 · 대변 +금액)과 두 계좌 잔고 변경이 되고, 전부 한 트랜잭션이다.
 * 이 레슨의 스키마는 {@code ledger-schema.sql}: 한 거래의 다리 합이 0 이 아니면 커밋 때 DB 가 거절한다.
 */
public final class LedgerService {

    private static final String CHECK_VIOLATION = "23514";

    private final Supplier<Connection> db;

    public LedgerService(Supplier<Connection> db) {
        this.db = db;
    }

    /**
     * TODO(구현) 같은 거래 id 는 한 번만, 두 다리 + 두 잔고를 한 트랜잭션에서 원자적으로 반영한다.
     *
     * <h3>지금 무엇이 문제인가</h3>
     * 지금은 "잔고를 읽고 → 앱에서 double 로 계산해 → 덮어쓰고 → 원장을 쌓는다". 같은 거래를 두 번 올리면 두 번 반영되고(예측 Q08),
     * 동시에 이체하면 읽고-계산해서-쓰기의 틈에서 갱신이 사라지거나 데드락이 나며(01.04),
     * 큰 금액은 double 에서 센트가 깨진다(예측 Q01). {@code LedgerImplementTest} 가 이걸 잡는다.
     *
     * <h3>할 일</h3>
     * <ol>
     *   <li>커넥션을 {@code setAutoCommit(false)} 로 — 이후가 한 트랜잭션</li>
     *   <li>멱등 선점: {@code INSERT INTO posted_txn (txn_id) VALUES (?) ON CONFLICT DO NOTHING} 의 영향 행이 0 이면
     *       이미 반영된 거래 → 롤백하고 {@link PostResult#DUPLICATE}</li>
     *   <li>두 계좌의 잔고를 <b>DB 안에서</b> 갱신: {@code UPDATE account SET balance = balance + ? WHERE id = ?}
     *       (보내는 쪽은 {@code amount.negate()}). 영향 행이 1 이 아니면 없는 계좌 → {@link IllegalArgumentException}</li>
     *   <li>원장 두 줄: {@code (txnId, from, -amount)} · {@code (txnId, to, +amount)} — {@code setBigDecimal} 로</li>
     *   <li>커밋하고 {@link PostResult#POSTED}</li>
     *   <li>잔고가 모자라면 {@code CHECK (balance >= 0)} 가 SQLState 23514 로 거절한다 (예측 Q04) —
     *       롤백하고 {@link PostResult#INSUFFICIENT}. 선점 행도 같이 사라져야 한다</li>
     * </ol>
     *
     * <h3>헷갈리기 쉬운 곳</h3>
     * <ul>
     *   <li>두 계좌를 갱신하는 <b>순서</b>를 계좌 id 순으로 고정한다 — 서로 반대 방향 이체가 락을 엇갈려 잡으면 데드락이다 (01.02)</li>
     *   <li>금액을 {@code double} 로 바꾸지 않는다 — {@code setBigDecimal} / {@code getBigDecimal}</li>
     *   <li>멱등 선점을 맨 앞에 둔다 — 같은 거래가 동시에 오면 두 번째는 첫 번째가 끝날 때까지 기다렸다가 0 행을 받는다 (01.03)</li>
     *   <li>원장 두 줄은 {@code INSERT} 두 번이어도 되고 한 번이어도 된다 — 합이 0 인지는 커밋 때 본다 (예측 Q05)</li>
     * </ul>
     */
    public PostResult post(Transfer t) {
        try (Connection c = db.get()) {
            c.setAutoCommit(false);
            double fromBalance = balanceOf(c, t.from());
            double toBalance = balanceOf(c, t.to());
            double amount = t.amount().doubleValue();
            if (t.from() != 0 && fromBalance < amount) return PostResult.INSUFFICIENT;
            setBalance(c, t.from(), fromBalance - amount);
            setBalance(c, t.to(), toBalance + amount);
            insertLegs(c, t);
            c.commit();
            return PostResult.POSTED;
        } catch (SQLException e) {
            throw new IllegalStateException(e);
        }
    }

    private static double balanceOf(Connection c, int account) throws SQLException {
        try (PreparedStatement ps = c.prepareStatement("SELECT balance FROM account WHERE id = ?")) {
            ps.setInt(1, account);
            try (java.sql.ResultSet rs = ps.executeQuery()) {
                rs.next();
                return rs.getDouble(1);
            }
        }
    }
    
    private static void setBalance(Connection c, int account, double balance) throws SQLException {
        try (PreparedStatement ps = c.prepareStatement("UPDATE account SET balance = ? WHERE id = ?")) {
            ps.setDouble(1, balance);
            ps.setInt(2, account);
            ps.executeUpdate();
        }
    }

    private static void insertLegs(Connection c, Transfer t) throws SQLException {
        try (PreparedStatement ps = c.prepareStatement(
                "INSERT INTO ledger (txn_id, account_id, amount) VALUES (?, ?, ?), (?, ?, ?)")) {
            ps.setString(1, t.txnId());
            ps.setInt(2, t.from());
            ps.setBigDecimal(3, t.amount().negate());
            ps.setString(4, t.txnId());
            ps.setInt(5, t.to());
            ps.setBigDecimal(6, t.amount());
            ps.executeUpdate();
        }
    }
}
