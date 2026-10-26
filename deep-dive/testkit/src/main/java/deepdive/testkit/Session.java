package deepdive.testkit;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.ResultSetMetaData;
import java.sql.SQLException;
import java.time.Duration;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.Callable;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;

/**
 * psql 터미널 하나 = Session 하나. 두 세션을 번갈아 조작하며 무엇이 보이고, 무엇이 막히고, 무엇이 실패하는지 본다.
 *
 * <pre>
 * [  +0ms] A  BEGIN ISOLATION LEVEL REPEATABLE READ
 * [  +3ms] A  SELECT balance FROM account WHERE id = 1      → 100
 * [  +5ms] B  UPDATE account SET balance = 50 WHERE id = 1  → 1행
 * [ +12ms] B  ⏳ 대기 중 …                                     (락을 기다리면 이렇게 보인다)
 * [ +40ms] A  UPDATE …                                      → ✗ 40001 could not serialize access …
 * </pre>
 *
 * <p>막히는 문장은 {@link #async} 로 보낸다. 다른 스레드에서 실행되고, {@link Pending#isWaiting} 으로 "아직 대기 중인가"를 볼 수 있다.
 */
public final class Session implements AutoCloseable {

    /** 격리수준 — JDBC 상수 대신 이름으로. */
    public enum Isolation {
        READ_UNCOMMITTED(Connection.TRANSACTION_READ_UNCOMMITTED, "READ UNCOMMITTED"),
        READ_COMMITTED(Connection.TRANSACTION_READ_COMMITTED, "READ COMMITTED"),
        REPEATABLE_READ(Connection.TRANSACTION_REPEATABLE_READ, "REPEATABLE READ"),
        SERIALIZABLE(Connection.TRANSACTION_SERIALIZABLE, "SERIALIZABLE");

        final int jdbc;
        final String sql;

        Isolation(int jdbc, String sql) {
            this.jdbc = jdbc;
            this.sql = sql;
        }
    }

    private final String name;
    private final Connection conn;
    private final ExecutorService worker;
    private final List<Future<?>> submitted = new java.util.concurrent.CopyOnWriteArrayList<>();

    private final java.util.function.Supplier<Connection> monitorFactory;
    private final int pid;
    private Connection monitor; // 대기 판정용 별도 연결 — 필요할 때 연다

    Session(String name, Connection conn, java.util.function.Supplier<Connection> monitorFactory) {
        this.name = name;
        this.conn = conn;
        this.monitorFactory = monitorFactory;
        this.pid = backendPid(conn);
        this.worker = Executors.newSingleThreadExecutor(r -> {
            Thread t = new Thread(r, "session-" + name);
            t.setDaemon(true);
            return t;
        });
    }

    public String name() {
        return name;
    }

    public Connection connection() {
        return conn;
    }

    // ── 트랜잭션 ─────────────────────────────────────────────

    public Session begin(Isolation level) {
        try {
            conn.setAutoCommit(false);
            conn.setTransactionIsolation(level.jdbc);
            Timeline.log(name, "BEGIN ISOLATION LEVEL " + level.sql, "");
            return this;
        } catch (SQLException e) {
            throw SqlFailure.of(name, "BEGIN", e);
        }
    }

    public void commit() {
        try {
            conn.commit();
            Timeline.log(name, "COMMIT", "");
        } catch (SQLException e) {
            Timeline.log(name, "COMMIT", "✗ " + e.getSQLState() + " " + firstLine(e));
            throw SqlFailure.of(name, "COMMIT", e);
        }
    }

    public void rollback() {
        try {
            conn.rollback();
            Timeline.log(name, "ROLLBACK", "");
        } catch (SQLException e) {
            throw SqlFailure.of(name, "ROLLBACK", e);
        }
    }

    // ── 문장 ────────────────────────────────────────────────

    /** INSERT · UPDATE · DELETE · DDL — 영향 받은 행 수. */
    public int update(String sql, Object... params) {
        try (PreparedStatement ps = prepare(sql, params)) {
            int n = ps.executeUpdate();
            Timeline.log(name, sql, "→ " + n + "행");
            return n;
        } catch (SQLException e) {
            Timeline.log(name, sql, "→ ✗ " + e.getSQLState() + " " + firstLine(e));
            throw SqlFailure.of(name, sql, e);
        }
    }

    public List<Map<String, Object>> query(String sql, Object... params) {
        try (PreparedStatement ps = prepare(sql, params); ResultSet rs = ps.executeQuery()) {
            List<Map<String, Object>> rows = new ArrayList<>();
            ResultSetMetaData md = rs.getMetaData();
            while (rs.next()) {
                Map<String, Object> row = new LinkedHashMap<>();
                for (int i = 1; i <= md.getColumnCount(); i++) row.put(md.getColumnLabel(i), rs.getObject(i));
                rows.add(row);
            }
            Timeline.log(name, sql, "→ " + (rows.size() == 1 && rows.getFirst().size() == 1
                    ? String.valueOf(rows.getFirst().values().iterator().next()) : rows));
            return rows;
        } catch (SQLException e) {
            Timeline.log(name, sql, "→ ✗ " + e.getSQLState() + " " + firstLine(e));
            throw SqlFailure.of(name, sql, e);
        }
    }

    /** 첫 행 첫 열. 없으면 null. */
    public Object one(String sql, Object... params) {
        List<Map<String, Object>> rows = query(sql, params);
        return rows.isEmpty() ? null : rows.getFirst().values().iterator().next();
    }

    public long count(String sql, Object... params) {
        return ((Number) one(sql, params)).longValue();
    }

    /** 이 세션의 서버 프로세스 id — pg_locks · pg_stat_activity 에서 찾을 때. */
    public int pid() {
        return pid;
    }

    // ── 막힐 수 있는 문장 ─────────────────────────────────────

    /** 다른 스레드에서 실행한다. 락을 기다리는 동안 이 메서드는 바로 돌아온다. */
    public <T> Pending<T> async(Callable<T> work) {
        Future<T> f = worker.submit(work);
        submitted.add(f);
        return new Pending<>(name, f, this::lockWait);
    }

    /** 엔진이 보는 이 세션의 대기: 락을 기다리면 "Lock/transactionid" 같은 문자열, 아니면 null. */
    private synchronized String lockWait() {
        try {
            if (monitor == null || monitor.isClosed()) monitor = monitorFactory.get();
            try (PreparedStatement ps = monitor.prepareStatement(
                    "SELECT wait_event_type, wait_event FROM pg_stat_activity WHERE pid = ?")) {
                ps.setInt(1, pid);
                try (ResultSet rs = ps.executeQuery()) {
                    if (rs.next() && "Lock".equals(rs.getString(1))) return "Lock/" + rs.getString(2);
                    return null;
                }
            }
        } catch (SQLException e) {
            return null;
        }
    }

    private static int backendPid(Connection c) {
        try (PreparedStatement ps = c.prepareStatement("SELECT pg_backend_pid()"); ResultSet rs = ps.executeQuery()) {
            rs.next();
            return rs.getInt(1);
        } catch (SQLException e) {
            throw new IllegalStateException(e);
        }
    }

    public Pending<Integer> updateAsync(String sql, Object... params) {
        return async(() -> update(sql, params));
    }

    /** 비동기로 보낸 문장의 핸들. */
    public static final class Pending<T> {
        /** grace 가 지나도 안 끝났는데 락 대기도 아니면(그냥 느림) 이만큼 더 지켜본다. */
        private static final Duration SLOW_CAP = Duration.ofSeconds(10);

        private final String session;
        private final Future<T> future;
        private final java.util.function.Supplier<String> lockWait;

        Pending(String session, Future<T> future, java.util.function.Supplier<String> lockWait) {
            this.session = session;
            this.future = future;
            this.lockWait = lockWait;
        }

        /**
         * 이 문장이 <b>락을 기다리고 있나</b>. 시간이 아니라 엔진(pg_stat_activity)에게 묻는다.
         *
         * <ol>
         *   <li>grace 안에 끝나면 → false</li>
         *   <li>grace 가 지나도 안 끝났고 엔진이 "Lock 대기" 라고 하면 → true</li>
         *   <li>안 끝났는데 락 대기도 아니면(머신이 바빠서 느릴 뿐) → 끝나거나 락에 걸릴 때까지 더 지켜본다</li>
         * </ol>
         * 그래서 바쁜 머신에서 "느림"을 "대기"로 착각하지 않는다. true 는 항상 최소 grace 만큼 지난 뒤에 나온다.
         */
        public boolean isWaiting(Duration grace) {
            if (finishedWithin(grace)) return false;
            long deadline = System.nanoTime() + SLOW_CAP.toNanos();
            while (System.nanoTime() < deadline) {
                String wait = lockWait.get();
                if (wait != null) {
                    Timeline.log(session, "⏳ 락 대기 중 …", "(엔진 확인: " + wait + ")");
                    return true;
                }
                if (finishedWithin(Duration.ofMillis(20))) return false;
            }
            throw new IllegalStateException(session + " 가 " + SLOW_CAP.toSeconds() + "초 동안 끝나지도, 락을 기다리지도 않는다");
        }

        private boolean finishedWithin(Duration d) {
            try {
                future.get(d.toMillis(), TimeUnit.MILLISECONDS);
                return true;
            } catch (TimeoutException e) {
                return false;
            } catch (ExecutionException e) {
                return true; // 실패로 끝났다 — 대기는 아니다
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                throw new IllegalStateException(e);
            }
        }

        public T await(Duration timeout) {
            try {
                return future.get(timeout.toMillis(), TimeUnit.MILLISECONDS);
            } catch (ExecutionException e) {
                if (e.getCause() instanceof RuntimeException re) throw re;
                throw new IllegalStateException(e.getCause());
            } catch (TimeoutException e) {
                throw new IllegalStateException(session + " 가 " + timeout + " 안에 끝나지 않았다", e);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                throw new IllegalStateException(e);
            }
        }
    }

    // ── 내부 ────────────────────────────────────────────────

    private PreparedStatement prepare(String sql, Object... params) throws SQLException {
        PreparedStatement ps = conn.prepareStatement(sql);
        for (int i = 0; i < params.length; i++) ps.setObject(i + 1, params[i]);
        return ps;
    }

    private static String firstLine(SQLException e) {
        String m = String.valueOf(e.getMessage());
        int nl = m.indexOf('\n');
        return nl < 0 ? m : m.substring(0, nl);
    }

    /**
     * 닫는다. 아직 락을 기다리며 실행 중인 문장({@link #async})이 있으면 먼저 <b>서버에 취소를 요청</b>한다.
     * 그러지 않으면 그 문장이 JDBC 커넥션을 쥔 채 서버 락을 기다리고, rollback 은 그 커넥션을 기다려
     * 테스트가 빨간불 대신 영원히 멈춘다 (구현이 틀려 대기가 풀리지 않는 경우).
     */
    @Override
    public void close() {
        try {
            if (monitor != null) monitor.close();
        } catch (SQLException ignored) {
            // 대기 판정용 연결 — 닫기 실패는 무시
        }
        boolean busy = submitted.stream().anyMatch(f -> !f.isDone());
        if (busy) {
            try {
                conn.unwrap(org.postgresql.PGConnection.class).cancelQuery(); // 실행 중인 문장 → 57014 로 끝난다
            } catch (SQLException ignored) {
                // 취소 요청 실패 — 아래 abort 가 마지막 수단
            }
        }
        worker.shutdownNow();
        try {
            if (!worker.awaitTermination(3, TimeUnit.SECONDS)) {
                conn.abort(Runnable::run); // 그래도 안 끝나면 연결을 끊는다 (서버가 트랜잭션을 롤백한다)
                return;
            }
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        } catch (SQLException ignored) {
            return;
        }
        try {
            if (!conn.isClosed()) {
                if (!conn.getAutoCommit()) conn.rollback();
                conn.close();
            }
        } catch (SQLException ignored) {
            // 이미 끊긴 세션
        }
    }
}
