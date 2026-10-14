package playground.shutdown.stage3;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.context.annotation.AnnotationConfigApplicationContext;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.DependsOn;
import org.springframework.context.support.DefaultLifecycleProcessor;
import playground.shutdown.drain.IdleDrainLifecycle;
import playground.shutdown.drain.ShutdownFirstDrainLifecycle;
import playground.shutdown.executor.Pools;
import playground.shutdown.executor.Tasks;
import playground.shutdown.executor.TracingThreadPoolTaskExecutor;
import playground.shutdown.resource.FakeDataSource;
import playground.shutdown.resource.FakeMqConnectionFactory;
import playground.shutdown.resource.FakeRedisConnectionFactory;
import playground.shutdown.support.Probe;
import playground.shutdown.support.ScenarioConfig;
import playground.shutdown.support.Shutdown;
import playground.shutdown.timeline.Timeline;

import java.time.Duration;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static playground.shutdown.support.Predict.todo;
import static playground.shutdown.support.TimelineQuery.happened;
import static playground.shutdown.support.TimelineQuery.order;
import static playground.shutdown.support.TimelineQuery.result;

/**
 * stage3: 풀이 남은 작업을 처리하는 시점에, 그 작업이 쓰는 자원이 아직 살아 있는가를 예측한다.
 * probe 는 "풀이 기다리기 시작한 순간" 에 Redis·MQ·DB 를 한 번씩 쓴다.
 *
 * <pre>
 * Redis(Lettuce 흉내)   SmartLifecycle phase 0 에서 멈춤, 이후 거절
 * MQ(Rabbit 흉내)       SmartLifecycle phase MIN 에서 끊음, 다음 요청 때 재연결, 자기 destroy 뒤 거부
 * DB(Hikari 흉내)       Lifecycle 없음, ③ destroy 에서만 닫힘
 *
 * 보기: result → "성공" "실패" "없음" · order → "먼저" "나중" · happened → true/false
 * </pre>
 *
 * <p>규칙: 실행하기 전에 {@code todo()} 를 내 예측값으로 바꾼다. 답지는 docs/04 와 git 이전 커밋에 있다.
 */
class ResourcesDuringShutdownTest {

    private static final Duration WAIT = Duration.ofSeconds(5);

    @BeforeEach
    void setUp() {
        Timeline.reset();
    }

    @Test
    @DisplayName("T-07a 기본값: 풀이 ② MAX/2 에서 기다리는 순간 자원은")
    void defaultMode() throws InterruptedException {
        runProbe(DefaultConfig.class, "② pool-a lifecycle stop 시작");

        assertThat(result("redis")).isEqualTo("성공");   // Q1
        assertThat(result("mq")).isEqualTo("성공");   // Q2
        assertThat(result("db")).isEqualTo("성공");   // Q3
    }

    @Test
    @DisplayName("T-07b PR 설정: 풀이 ③ destroy 에서 기다리는 순간 자원은")
    void waitForTasksMode() throws InterruptedException {
        runProbe(WaitForTasksConfig.class, "③ pool-a destroy 시작");

        assertThat(result("redis")).isEqualTo("실패");   // Q1
        assertThat(result("mq")).isEqualTo("성공");   // Q2
        assertThat(happened("  mq 재연결")).isEqualTo(true);   // Q3 mq 는 재연결을 하나
        assertThat(result("db")).isEqualTo("성공");   // Q4
    }

    @Test
    @DisplayName("T-07c PR 설정 + DataSource 를 풀보다 늦게 만들면 자원은")
    void waitForTasksModeWithDataSourceCreatedLater() throws InterruptedException {
        runProbe(DataSourceCreatedLaterConfig.class, "③ pool-a destroy 시작");

        assertThat(order("③ db close", "③ pool-a destroy 시작")).isEqualTo("먼저");   // Q1 DB 가 닫히는 건 풀 destroy 보다 먼저인가 나중인가
        assertThat(result("db")).isEqualTo("실패");   // Q2
        assertThat(result("redis")).isEqualTo("실패");   // Q3
    }

    @Test
    @DisplayName("T-07d PR 플래그 + ShutdownFirstDrain: drain 이 비우는 순간 자원은")
    void shutdownFirstDrain() throws InterruptedException {
        runProbe(ShutdownFirstDrainConfig.class, "② drain(shutdown 먼저) 접수 마감");

        assertThat(result("redis")).isEqualTo("성공");   // Q1
        assertThat(result("mq")).isEqualTo("성공");   // Q2
        assertThat(result("db")).isEqualTo("성공");   // Q3
    }

    @Test
    @DisplayName("T-07e PR 플래그 + IdleDrain: drain 이 비우는 순간 자원은 (IdleDrainLifecycle 을 구현해야 통과한다)")
    void idleDrain() throws InterruptedException {
        runProbe(IdleDrainConfig.class, "② drain(idle 대기) 시작");

        assertThat(result("redis")).isEqualTo("성공");   // Q1
        assertThat(order("  probe 끝", "② redis(phase 0) stop")).isEqualTo("먼저");   // Q2 probe 가 끝나는 건 Redis 가 멈추기 먼저인가 나중인가
    }

    /** pool-a 에 probe 를 넣고 컨텍스트를 닫는다. probe 는 waitForEvent 시점에 자원을 써 본다. */
    private static void runProbe(Class<?> config, String waitForEvent) throws InterruptedException {
        AnnotationConfigApplicationContext context = new AnnotationConfigApplicationContext(config);
        TracingThreadPoolTaskExecutor poolA = context.getBean("poolA", TracingThreadPoolTaskExecutor.class);
        Runnable probe = Probe.afterEvent(waitForEvent,
                context.getBean(FakeRedisConnectionFactory.class),
                context.getBean(FakeMqConnectionFactory.class),
                context.getBean(FakeDataSource.class));
        Tasks.submit(poolA, "probe", probe);
        Timeline.awaitEvent("  probe 대기", WAIT);

        Shutdown.closeAndSettle(context);
    }

    // ---------------------------------------------------------------- 구성

    @Configuration
    static class DefaultConfig extends ScenarioConfig {
        @Override
        protected Pools.Mode mode() {
            return Pools.Mode.DEFAULT;
        }
    }

    @Configuration
    static class WaitForTasksConfig extends ScenarioConfig {
        @Override
        protected Pools.Mode mode() {
            return Pools.Mode.WAIT_FOR_TASKS;
        }
    }

    /** 수정안: PR 플래그는 두고 awaitTermination 은 빼고, 비우는 일은 drain 이 맡는다. */
    @Configuration
    static class ShutdownFirstDrainConfig extends ScenarioConfig {
        @Override
        protected Pools.Mode mode() {
            return Pools.Mode.WAIT_FOR_TASKS;
        }

        @Override
        protected Duration awaitTermination() {
            return Duration.ZERO;
        }

        @Bean
        public ShutdownFirstDrainLifecycle drain() {
            return new ShutdownFirstDrainLifecycle(List.of(poolA(), poolB()), Duration.ofSeconds(5));
        }
    }

    @Configuration
    static class IdleDrainConfig extends ScenarioConfig {
        @Override
        protected Pools.Mode mode() {
            return Pools.Mode.WAIT_FOR_TASKS;
        }

        @Override
        protected Duration awaitTermination() {
            return Duration.ZERO;
        }

        @Bean
        public IdleDrainLifecycle drain() {
            return new IdleDrainLifecycle(List.of(poolA(), poolB()), Duration.ofSeconds(5));
        }
    }

    /** ScenarioConfig 와 같지만 DataSource 를 풀보다 늦게 만든다. destroy 는 생성 역순이라 DataSource 가 풀보다 먼저 닫힌다. */
    @Configuration
    static class DataSourceCreatedLaterConfig {

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
        @DependsOn({"redis", "mq"})
        public TracingThreadPoolTaskExecutor poolA() {
            return Pools.create("pool-a", Pools.Mode.WAIT_FOR_TASKS, Duration.ofSeconds(1));
        }

        @Bean
        @DependsOn("poolA")
        public FakeDataSource dataSource() {
            return new FakeDataSource();
        }
    }
}
