package deepdive.testkit;

import org.testcontainers.containers.PostgreSQLContainer;
import org.testcontainers.utility.DockerImageName;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;

/**
 * 진짜 PostgreSQL 16 컨테이너. 테스트 JVM 하나에 하나만 띄워 모든 테스트 클래스가 같이 쓴다 (기동 1회 ≈ 2~3초).
 *
 * <p>흉내 내지 않는다 — 락 대기 · 직렬화 실패(40001) · 데드락 감지는 진짜 엔진이 내는 결과다.
 * 데드락 감지를 기다리지 않도록 deadlock_timeout 만 200ms 로 줄였다 (기본 1s).
 */
public final class PostgresLab {

    private static final PostgreSQLContainer<?> PG = new PostgreSQLContainer<>(DockerImageName.parse("postgres:16-alpine"))
            .withDatabaseName("lab")
            .withUsername("lab")
            .withPassword("lab")
            .withCommand("postgres", "-c", "deadlock_timeout=200ms", "-c", "log_lock_waits=on");

    private static PostgresLab instance;

    private PostgresLab() {}

    public static synchronized PostgresLab get() {
        if (instance == null) {
            PG.start();
            instance = new PostgresLab();
            System.out.printf("%n[PostgresLab] %s 기동 — psql 로 붙어 보려면: psql '%s' (user/pw = lab/lab)%n%n",
                    PG.getDockerImageName(), PG.getJdbcUrl().replace("jdbc:", ""));
        }
        return instance;
    }

    public Connection connect() {
        try {
            return DriverManager.getConnection(PG.getJdbcUrl(), PG.getUsername(), PG.getPassword());
        } catch (SQLException e) {
            throw new IllegalStateException(e);
        }
    }

    /** 이름 붙은 세션 — 타임라인에 "A", "B" 로 찍힌다. */
    public Session session(String name) {
        return new Session(name, connect(), this::connect);
    }

    /** 준비용 SQL (autocommit). 테이블 초기화 등. */
    public void exec(String... statements) {
        try (Connection c = connect(); Statement st = c.createStatement()) {
            for (String sql : statements) st.execute(sql);
        } catch (SQLException e) {
            throw new IllegalStateException(e);
        }
    }

    /** 첫 행 첫 열 (autocommit). 검증용. */
    public Object one(String sql) {
        try (Connection c = connect(); Statement st = c.createStatement(); ResultSet rs = st.executeQuery(sql)) {
            return rs.next() ? rs.getObject(1) : null;
        } catch (SQLException e) {
            throw new IllegalStateException(e);
        }
    }

    public String jdbcUrl() {
        return PG.getJdbcUrl();
    }

    public String user() {
        return PG.getUsername();
    }

    public String password() {
        return PG.getPassword();
    }
}
