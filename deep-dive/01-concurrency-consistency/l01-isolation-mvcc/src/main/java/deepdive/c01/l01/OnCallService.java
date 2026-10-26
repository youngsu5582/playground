package deepdive.c01.l01;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.time.Duration;
import java.util.function.Supplier;

/**
 * 당직표 — write skew 의 교과서 예제 (DDIA 7장).
 *
 * <p>규칙: <b>당직은 항상 1명 이상</b>. 그래서 빠지기 전에 "지금 당직이 2명 이상인가"를 확인한다.
 * 두 사람이 동시에 확인하면? 둘 다 "2명이네" 를 보고 둘 다 빠진다. 서로 <b>다른 행</b>을 고쳤으니 행 락으로는 안 막힌다.
 *
 * <pre>
 * CREATE TABLE on_call (doctor text PRIMARY KEY, on_call boolean NOT NULL);
 * </pre>
 *
 * 이 클래스는 손대지 않는다. 고칠 곳은 {@link Tx#serializable}.
 */
public final class OnCallService {

    private final Supplier<Connection> db;
    private final Duration thinkTime;

    /** @param thinkTime 확인과 갱신 사이의 지연 — 경쟁이 일어날 창을 넓힌다 (실서비스의 네트워크·로직 시간) */
    public OnCallService(Supplier<Connection> db, Duration thinkTime) {
        this.db = db;
        this.thinkTime = thinkTime;
    }

    /** @return 빠졌으면 true, 마지막 한 명이라 거절됐으면 false */
    public boolean goOffCall(String doctor) {
        return Tx.serializable(db, c -> {
            long onCall = count(c);
            if (onCall < 2) return false;
            pause();
            try (PreparedStatement ps = c.prepareStatement("UPDATE on_call SET on_call = false WHERE doctor = ?")) {
                ps.setString(1, doctor);
                ps.executeUpdate();
            }
            return true;
        });
    }

    private static long count(Connection c) throws SQLException {
        try (PreparedStatement ps = c.prepareStatement("SELECT count(*) FROM on_call WHERE on_call");
             ResultSet rs = ps.executeQuery()) {
            rs.next();
            return rs.getLong(1);
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
