package playground.shutdown.stage6.infra;

import com.zaxxer.hikari.HikariDataSource;
import org.springframework.amqp.rabbit.connection.CachingConnectionFactory;
import org.springframework.data.redis.connection.RedisStandaloneConfiguration;
import org.springframework.data.redis.connection.lettuce.LettuceConnectionFactory;
import org.springframework.jdbc.datasource.DataSourceTransactionManager;
import org.springframework.transaction.support.DefaultTransactionStatus;
import playground.shutdown.timeline.Timeline;

import javax.sql.DataSource;

/**
 * 진짜 자원 클래스에 타임라인 기록만 붙인다 ({@code TracingThreadPoolTaskExecutor} 와 같은 방식).
 * 모든 메서드가 super 를 그대로 부르므로 종료 동작은 원래 클래스와 같다.
 */
public final class TracedResources {

    private TracedResources() {
    }

    /** LettuceConnectionFactory: SmartLifecycle phase 0 + DisposableBean. */
    public static class Redis extends LettuceConnectionFactory {

        /** destroy() 가 안에서 stop() 을 한 번 더 부른다. 그 호출은 ② 가 아니므로 남기지 않는다. */
        private volatile boolean destroying;

        public Redis(RedisStandaloneConfiguration configuration) {
            super(configuration);
        }

        @Override
        public void stop() {
            if (!destroying) {
                Timeline.record("② redis(phase " + getPhase() + ") stop");
            }
            super.stop();
        }

        @Override
        public void destroy() {
            destroying = true;
            Timeline.record("③ redis destroy");
            super.destroy();
        }
    }

    /** CachingConnectionFactory: SmartLifecycle phase MIN + DisposableBean. destroy() 는 final 이라 ② 만 남긴다. */
    public static class Rabbit extends CachingConnectionFactory {

        public Rabbit(String host, int port) {
            super(host, port);
        }

        @Override
        public void stop() {
            Timeline.record("② rabbit(phase MIN) stop");
            super.stop();
        }
    }

    /** HikariDataSource: Closeable 만. ③ 에서 close(). */
    public static class Db extends HikariDataSource {

        @Override
        public void close() {
            Timeline.record("③ db close");
            super.close();
        }
    }

    /** 커밋이 끝난 순간을 남긴다. 그 뒤에 커밋 후 콜백(AFTER_COMMIT 리스너)이 돈다. */
    public static class TxManager extends DataSourceTransactionManager {

        public TxManager(DataSource dataSource) {
            super(dataSource);
        }

        @Override
        protected void doCommit(DefaultTransactionStatus status) {
            super.doCommit(status);
            Timeline.record("  tx 커밋 완료");
        }
    }
}
