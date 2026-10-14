package playground.shutdown.stage5;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.context.annotation.AnnotationConfigApplicationContext;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.DependsOn;
import org.springframework.context.support.DefaultLifecycleProcessor;
import org.springframework.data.redis.connection.RedisStandaloneConfiguration;
import org.springframework.data.redis.connection.lettuce.LettuceConnectionFactory;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.testcontainers.containers.GenericContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;
import org.testcontainers.utility.DockerImageName;
import playground.shutdown.drain.IdleDrainLifecycle;
import playground.shutdown.executor.Pools;
import playground.shutdown.executor.Tasks;
import playground.shutdown.executor.TracingThreadPoolTaskExecutor;
import playground.shutdown.support.Shutdown;
import playground.shutdown.timeline.Timeline;

import java.time.Duration;
import java.util.List;

import static playground.shutdown.support.TimelineAssert.happened;

/**
 * stage5: 가짜가 아니라 진짜 LettuceConnectionFactory 와 Redis 컨테이너로 stage3 의 Redis 결과를 확인한다.
 * Docker 가 없으면 건너뛴다.
 */
@Testcontainers(disabledWithoutDocker = true)
class RealLettuceTest {

    @Container
    static final GenericContainer<?> REDIS = new GenericContainer<>(DockerImageName.parse("redis:7-alpine"))
            .withExposedPorts(6379);

    @BeforeEach
    void setUp() {
        Timeline.reset();
    }

    @Test
    @DisplayName("T-09a PR 설정 + 진짜 Lettuce: ③ destroy 에서 Redis 를 쓰면 'LettuceConnectionFactory has been STOPPED'")
    void waitForTasksWithRealLettuce() throws InterruptedException {
        runProbe(WaitForTasksConfig.class, "③ pool-a destroy 시작");

        happened("  real redis → 실패 IllegalStateException: LettuceConnectionFactory has been STOPPED");
    }

    @Test
    @DisplayName("T-09b IdleDrain + 진짜 Lettuce: Redis 가 멈추기 전에 비우므로 성공한다")
    void idleDrainWithRealLettuce() throws InterruptedException {
        runProbe(IdleDrainConfig.class, "② drain(idle 대기) 시작");

        happened("  real redis → 성공");
    }

    private static void runProbe(Class<?> config, String waitForEvent) throws InterruptedException {
        AnnotationConfigApplicationContext context = new AnnotationConfigApplicationContext(config);
        TracingThreadPoolTaskExecutor poolA = context.getBean("poolA", TracingThreadPoolTaskExecutor.class);
        StringRedisTemplate redisTemplate = context.getBean(StringRedisTemplate.class);
        redisTemplate.opsForValue().set("k", "v");

        Tasks.submit(poolA, "probe", () -> {
            Timeline.record("  probe 대기: [" + waitForEvent + "] 까지");
            try {
                Timeline.awaitEvent(waitForEvent, Duration.ofSeconds(5));
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                return;
            }
            Tasks.attempt("real redis", () -> redisTemplate.opsForValue().get("k"));
        });
        Timeline.awaitEvent("  probe 대기", Duration.ofSeconds(5));

        Shutdown.closeAndSettle(context);
    }

    // ---------------------------------------------------------------- 구성

    abstract static class RealRedisConfig {

        protected abstract Duration awaitTermination();

        @Bean(name = "lifecycleProcessor")
        public DefaultLifecycleProcessor lifecycleProcessor() {
            DefaultLifecycleProcessor processor = new DefaultLifecycleProcessor();
            processor.setTimeoutPerShutdownPhase(1000);
            return processor;
        }

        @Bean
        public LettuceConnectionFactory redisConnectionFactory() {
            return new LettuceConnectionFactory(new RedisStandaloneConfiguration(REDIS.getHost(), REDIS.getFirstMappedPort()));
        }

        @Bean
        public StringRedisTemplate redisTemplate(LettuceConnectionFactory redisConnectionFactory) {
            return new StringRedisTemplate(redisConnectionFactory);
        }

        @Bean
        @DependsOn("redisConnectionFactory")
        public TracingThreadPoolTaskExecutor poolA() {
            return Pools.create("pool-a", Pools.Mode.WAIT_FOR_TASKS, awaitTermination());
        }
    }

    @Configuration
    static class WaitForTasksConfig extends RealRedisConfig {
        @Override
        protected Duration awaitTermination() {
            return Duration.ofSeconds(1);
        }
    }

    @Configuration
    static class IdleDrainConfig extends RealRedisConfig {
        @Override
        protected Duration awaitTermination() {
            return Duration.ZERO;
        }

        @Bean
        public IdleDrainLifecycle drain() {
            return new IdleDrainLifecycle(List.of(poolA()), Duration.ofSeconds(5));
        }
    }
}
