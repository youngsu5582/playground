package deepdive.testkit;

import java.sql.SQLException;

/**
 * SQL 실패. 핵심은 {@link #sqlState()} — 무엇 때문에 실패했는지 엔진이 붙여 준 코드.
 *
 * <pre>
 * 40001  serialization_failure   직렬화 실패 — 다시 시도하면 성공할 수 있다
 * 40P01  deadlock_detected       데드락 — 엔진이 한쪽을 희생시켰다
 * 23505  unique_violation        유니크 제약 위반
 * 55P03  lock_not_available      NOWAIT 로 락을 못 잡음
 * </pre>
 */
public final class SqlFailure extends RuntimeException {

    private final String sqlState;

    private SqlFailure(String message, String sqlState, SQLException cause) {
        super(message, cause);
        this.sqlState = sqlState;
    }

    static SqlFailure of(String session, String sql, SQLException e) {
        return new SqlFailure(session + " │ " + sql + " → " + e.getSQLState() + " " + e.getMessage(), e.getSQLState(), e);
    }

    public String sqlState() {
        return sqlState;
    }

    /** 다른 SQLException 을 감쌀 때 (레슨 코드에서 JDBC 를 직접 쓰는 경우). */
    public static String stateOf(Throwable t) {
        for (Throwable c = t; c != null; c = c.getCause()) {
            if (c instanceof SqlFailure f) return f.sqlState;
            if (c instanceof SQLException s) return s.getSQLState();
        }
        return null;
    }
}
