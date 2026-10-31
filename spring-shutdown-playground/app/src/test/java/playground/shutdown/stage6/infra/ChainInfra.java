package playground.shutdown.stage6.infra;

import com.rabbitmq.client.Channel;
import com.rabbitmq.client.Connection;
import com.rabbitmq.client.ConnectionFactory;
import io.lettuce.core.RedisClient;
import io.lettuce.core.api.StatefulRedisConnection;
import org.testcontainers.containers.GenericContainer;
import org.testcontainers.containers.PostgreSQLContainer;
import org.testcontainers.containers.RabbitMQContainer;
import org.testcontainers.lifecycle.Startables;
import org.testcontainers.utility.DockerImageName;
import playground.shutdown.stage6.chain.RequestStatus;
import playground.shutdown.stage6.chain.UserJobQueue;

import java.sql.DriverManager;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.function.Function;

/**
 * stage6 의 진짜 자원 세 개(Redis · RabbitMQ · PostgreSQL). 테스트 JVM 하나에 한 벌만 띄워 모든 테스트가 같이 쓴다.
 *
 * <p>종료 뒤 확인({@link #requestStatus} 등)은 컨텍스트와 상관없는 새 연결로 한다 — 컨텍스트의 자원은 이미 닫혔다.
 */
public final class ChainInfra {

    public static final GenericContainer<?> REDIS = new GenericContainer<>(DockerImageName.parse("redis:7-alpine"))
            .withExposedPorts(6379);
    public static final RabbitMQContainer RABBIT = new RabbitMQContainer(DockerImageName.parse("rabbitmq:3.13-management"));
    public static final PostgreSQLContainer<?> POSTGRES = new PostgreSQLContainer<>(DockerImageName.parse("postgres:16-alpine"));

    static {
        Startables.deepStart(REDIS, RABBIT, POSTGRES).join();
    }

    private ChainInfra() {
    }

    /** 테스트마다 빈 상태로 시작한다: 테이블 새로 만들기 · Redis 비우기 · Rabbit 큐 비우기. */
    public static void reset() {
        jdbc(statement -> {
            statement.execute("DROP TABLE IF EXISTS job");
            statement.execute("DROP TABLE IF EXISTS job_request");
            statement.execute("CREATE TABLE job_request (id BIGSERIAL PRIMARY KEY, user_id TEXT NOT NULL, status TEXT NOT NULL, reason TEXT)");
            statement.execute("CREATE TABLE job (id BIGSERIAL PRIMARY KEY, request_id BIGINT NOT NULL REFERENCES job_request (id))");
            return null;
        });
        redis(connection -> connection.sync().flushall());
        rabbit(channel -> {
            channel.queueDeclare(UserJobQueue.RABBIT_QUEUE, true, false, false, null);
            return channel.queuePurge(UserJobQueue.RABBIT_QUEUE);
        });
    }

    /** 종료 뒤 요청 행의 상태. */
    public static RequestStatus requestStatus(long requestId) {
        return jdbc(statement -> {
            try (ResultSet rs = statement.executeQuery("SELECT status FROM job_request WHERE id = " + requestId)) {
                rs.next();
                return RequestStatus.valueOf(rs.getString(1));
            }
        });
    }

    /** 종료 뒤 남은 job 행 수. */
    public static int jobCount(long requestId) {
        return jdbc(statement -> {
            try (ResultSet rs = statement.executeQuery("SELECT count(*) FROM job WHERE request_id = " + requestId)) {
                rs.next();
                return rs.getInt(1);
            }
        });
    }

    /** 종료 뒤 그 사용자의 Redis 대기열 길이. */
    public static long redisLength(String userId) {
        return redis(connection -> connection.sync().llen(UserJobQueue.key(userId)));
    }

    /** 종료 뒤 Rabbit 큐에 쌓인 메시지 수. */
    public static int rabbitDepth() {
        return rabbit(channel -> channel.queueDeclarePassive(UserJobQueue.RABBIT_QUEUE).getMessageCount());
    }

    private interface SqlWork<T> {
        T run(Statement statement) throws SQLException;
    }

    private interface RabbitWork<T> {
        T run(Channel channel) throws Exception;
    }

    private static <T> T jdbc(SqlWork<T> work) {
        try (var connection = DriverManager.getConnection(POSTGRES.getJdbcUrl(), POSTGRES.getUsername(), POSTGRES.getPassword());
             var statement = connection.createStatement()) {
            return work.run(statement);
        } catch (SQLException e) {
            throw new IllegalStateException(e);
        }
    }

    private static <T> T redis(Function<StatefulRedisConnection<String, String>, T> work) {
        RedisClient client = RedisClient.create("redis://" + REDIS.getHost() + ":" + REDIS.getFirstMappedPort());
        try (var connection = client.connect()) {
            return work.apply(connection);
        } finally {
            client.shutdown();
        }
    }

    private static <T> T rabbit(RabbitWork<T> work) {
        ConnectionFactory factory = new ConnectionFactory();
        factory.setHost(RABBIT.getHost());
        factory.setPort(RABBIT.getAmqpPort());
        factory.setUsername(RABBIT.getAdminUsername());
        factory.setPassword(RABBIT.getAdminPassword());
        try (Connection connection = factory.newConnection(); Channel channel = connection.createChannel()) {
            return work.run(channel);
        } catch (Exception e) {
            throw new IllegalStateException(e);
        }
    }
}
