package deepdive.c01.l02;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.SQLException;
import java.time.Duration;
import java.util.function.Supplier;

/**
 * 계좌 이체 — 두 행을 한 트랜잭션에서 고친다.
 *
 * <pre>
 * CREATE TABLE account (id int PRIMARY KEY, balance bigint NOT NULL CHECK (balance >= 0));
 * </pre>
 *
 * 먼저 두 행을 잠그고(출금 쪽 · 입금 쪽) 그다음 고친다. 잠그는 <b>순서</b>가 이 클래스의 전부다.
 * 고칠 곳은 {@link #transfer} 의 두 줄.
 */
public final class TransferService {

    private final Supplier<Connection> db;
    private final Duration thinkTime;

    /** @param thinkTime 첫 락과 둘째 락 사이의 지연 — 경쟁이 일어날 창을 넓힌다 (실서비스의 네트워크·로직 시간) */
    public TransferService(Supplier<Connection> db, Duration thinkTime) {
        this.db = db;
        this.thinkTime = thinkTime;
    }

    /**
     * TODO(구현) {@code from} 에서 {@code to} 로 {@code amount} 를 옮긴다. 잔고가 모자라면 아무것도 바꾸지 않고 false.
     *
     * <h3>지금 무엇이 문제인가</h3>
     * 지금은 인자 순서대로 잠근다 (from 먼저, to 나중). 1→2 이체와 2→1 이체가 동시에 돌면
     * 하나는 1번 다음 2번, 하나는 2번 다음 1번을 잠그려 한다 — 서로가 가진 걸 기다리는 순환, 데드락이다 (예측 Q09).
     * 엔진이 한쪽을 40P01 로 끊어 주지만, 끊긴 이체는 호출자에게 에러로 샌다.
     * {@code TransferImplementTest} 가 이걸 잡는다.
     *
     * <h3>할 일</h3>
     * <ol>
     *   <li>{@code first} · {@code second} 를 <b>from · to 의 방향과 상관없이</b> 항상 같은 순서가 되게 정한다 — 작은 id 먼저</li>
     * </ol>
     *
     * <h3>헷갈리기 쉬운 곳</h3>
     * <ul>
     *   <li>순서를 정하는 대상은 "누가 보내는가" 가 아니라 "어느 행인가" 다. 방향은 아래 UPDATE 두 문장에만 남는다</li>
     *   <li>이건 <b>예방</b>이다. 40P01 을 받고 재시도하는 것(01.01 의 Tx.serializable 같은)은 사후 대응이고, 여기서는 아예 안 나게 한다</li>
     * </ul>
     *
     * @return 이체했으면 true, 잔고가 모자라 거절했으면 false
     */
    public boolean transfer(long from, long to, long amount) {
        try (Connection c = db.get()) {
            c.setAutoCommit(false);
            long first = from;
            long second = to;
            lock(c, first);
            pause();
            lock(c, second);
            if (update(c, "UPDATE account SET balance = balance - ? WHERE id = ? AND balance >= ?", amount, from, amount) == 0) {
                c.rollback();
                return false;
            }
            update(c, "UPDATE account SET balance = balance + ? WHERE id = ?", amount, to);
            c.commit();
            return true;
        } catch (SQLException e) {
            throw new IllegalStateException("이체 실패: " + e.getMessage(), e);
        }
    }

    private static void lock(Connection c, long id) throws SQLException {
        try (PreparedStatement ps = c.prepareStatement("SELECT id FROM account WHERE id = ? FOR UPDATE")) {
            ps.setLong(1, id);
            ps.executeQuery().close();
        }
    }

    private static int update(Connection c, String sql, long... params) throws SQLException {
        try (PreparedStatement ps = c.prepareStatement(sql)) {
            for (int i = 0; i < params.length; i++) ps.setLong(i + 1, params[i]);
            return ps.executeUpdate();
        }
    }

    private void pause() {
        try {
            Thread.sleep(thinkTime.toMillis());
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }
}
