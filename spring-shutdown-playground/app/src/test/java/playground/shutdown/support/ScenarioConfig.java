package playground.shutdown.support;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.DependsOn;
import org.springframework.context.support.DefaultLifecycleProcessor;
import playground.shutdown.executor.Pools;
import playground.shutdown.executor.TracingThreadPoolTaskExecutor;
import playground.shutdown.resource.FakeDataSource;
import playground.shutdown.resource.FakeMqConnectionFactory;
import playground.shutdown.resource.FakeRedisConnectionFactory;

import java.time.Duration;

/**
 * stage2~4 가 공유하는 컨텍스트 구성. 하위 @Configuration 이 풀의 종료 설정만 바꾼다.
 *
 * <pre>
 * 생성 순서: redis · mq · dataSource → poolA → poolB → destroyMarker
 * destroy 순서는 그 역순: destroyMarker → poolB → poolA → (자원들)
 * </pre>
 */
public abstract class ScenarioConfig {

    protected abstract Pools.Mode mode();

    /** WAIT_FOR_TASKS 일 때 풀마다 destroy 에서 기다리는 상한. */
    protected Duration awaitTermination() {
        return Duration.ofSeconds(1);
    }

    /** spring.lifecycle.timeout-per-shutdown-phase 에 해당한다. 테스트가 빨리 끝나게 1초로 둔다. */
    @Bean(name = "lifecycleProcessor")
    public DefaultLifecycleProcessor lifecycleProcessor() {
        DefaultLifecycleProcessor processor = new DefaultLifecycleProcessor();
        processor.setTimeoutPerShutdownPhase(1000);
        return processor;
    }

    @Bean
    public FakeRedisConnectionFactory redis() {
        return new FakeRedisConnectionFactory();
    }

    @Bean
    public FakeMqConnectionFactory mq() {
        return new FakeMqConnectionFactory();
    }

    @Bean
    public FakeDataSource dataSource() {
        return new FakeDataSource();
    }

    @Bean
    @DependsOn({"redis", "mq", "dataSource"})
    public TracingThreadPoolTaskExecutor poolA() {
        return Pools.create("pool-a", mode(), awaitTermination());
    }

    @Bean
    @DependsOn("poolA")
    public TracingThreadPoolTaskExecutor poolB() {
        return Pools.create("pool-b", mode(), awaitTermination());
    }

    @Bean
    @DependsOn({"poolA", "poolB"})
    public DestroyMarker destroyMarker() {
        return new DestroyMarker();
    }
}
