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
import playground.shutdown.support.Order;
import playground.shutdown.support.Outcome;
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
 * stage3: 풀이 남은 작업을 기다리기 시작한 순간에, 그 작업이 쓰는 자원이 아직 살아 있는가를 예측한다.
 *
 * <h2>무엇을 하나</h2>
 * pool-a 에 probe 작업 하나를 넣고 close() 를 부른다. probe 는 테스트마다 정한 이벤트(= 풀이 기다리기 시작한 순간)가 찍힐 때까지
 * 기다렸다가, 200ms 일한 뒤 Redis·MQ·DB 를 한 번씩 써 본다. 결과는 {@code result("redis")} 처럼 꺼낸다.
 *
 * <h2>자원 — 종료 단계는 stage2 머리말과 {@link playground.shutdown.support.Stage} 참고</h2>
 * <pre>
 * redis       SmartLifecycle phase 0. ② 에서 멈추고, 그 뒤로는 연결을 거절한다 (Lettuce 흉내)
 * mq          SmartLifecycle phase MIN. ② 에서 연결을 끊지만, 다음 요청이 오면 다시 연결한다. 자기 destroy 뒤로는 거부 (Rabbit 흉내)
 * dataSource  Lifecycle 없음. ③ 에서 close() 로만 닫힌다 (Hikari 흉내)
 * 풀          ThreadPoolTaskExecutor phase MAX/2. 설정에 따라 ② 또는 ③ 에서 기다린다 (stage2)
 * 만든 순서   redis · mq · dataSource → pool-a → pool-b → destroyMarker   (T-07c 만 다르다)
 * </pre>
 *
 * <h2>질문이 가리키는 타임라인 이벤트</h2>
 * <pre>
 * "  mq 재연결"               mq 가 끊긴 연결을 다시 맺은 때
 * "③ db close"                dataSource 가 닫힌 때
 * "③ pool-a destroy 시작"     ③ 에서 pool-a 의 destroy() 가 불린 때
 * "  probe 끝"                probe 가 자원을 다 써 본 때
 * "② redis(phase 0) stop"     Redis 가 멈춘 때
 * </pre>
 *
 * <p>규칙: 실행하기 전에 {@code todo()} 를 내 예측으로 바꾼다. 보기는 {@link Outcome} · {@link Order} enum 이다.
 */
class ResourcesDuringShutdownTest {

    private static final Duration WAIT = Duration.ofSeconds(5);

    @BeforeEach
    void setUp() {
        Timeline.reset();
    }

    @Test
    @DisplayName("T-07a 기본값: 풀이 ② 에서 기다리기 시작한 순간 자원은")
    void defaultMode() throws InterruptedException {
        // 상황: 기본값 pool-a 에 자원 확인 작업(probe)을 미리 실행해 둔 뒤 context.close() 를 호출한다.
        // probe 는 "② pool-a lifecycle stop 시작" 이벤트를 기다렸다가, 200ms 후 Redis·MQ·DB 를 차례로 호출한다.
        // result("redis") 는 그 호출의 성공/실패/미시도 여부다. Redis 자체의 종료 상태를 직접 조회하는 것은 아니다.
        runProbe(DefaultConfig.class, "② pool-a lifecycle stop 시작");

        // Q1, Q2, Q3 pool-a 가 redis, mq, db 에 의존하므로
        // pool-a 가 destroy 되는 시점에는 모두 살아있으므로 성공한다.
        assertThat(result("redis")).isEqualTo(Outcome.SUCCESS);
        assertThat(result("mq")).isEqualTo(Outcome.SUCCESS);
        assertThat(result("db")).isEqualTo(Outcome.SUCCESS);
    }

    @Test
    @DisplayName("T-07b PR 설정: 풀이 ③ 에서 기다리기 시작한 순간 자원은")
    void waitForTasksMode() throws InterruptedException {
        // 상황: waitForTasksToCompleteOnShutdown(true) 풀. probe 는 "③ pool-a destroy 시작" 에서 깨어난다
        runProbe(WaitForTasksConfig.class, "③ pool-a destroy 시작");

        // Q1 redis 는 기다리지 않고, 종료 lifecycle 을 진행한다.
        assertThat(result("redis")).isEqualTo(Outcome.FAILURE);   // Q1 Redis 는
        // Q2 mq 는 SmartLifeCycle 을 통해 stop 까지만 진행되어, 요청을 접수한다.
        assertThat(result("mq")).isEqualTo(Outcome.SUCCESS);
        // Q4 DB 는 SmartLifeCycle 을 구현하지 않아, destroy 로 처리된다.
        assertThat(result("db")).isEqualTo(Outcome.SUCCESS);

        // Q3 MQ 는 재연결을 하진 않는다.
        // publish 메서드 참고, 닫혀있으면 재연결
        assertThat(happened("  mq 재연결")).isEqualTo(true);
    }

    @Test
    @DisplayName("T-07c PR 설정 + DataSource 를 풀보다 늦게 만들면 자원은")
    void waitForTasksModeWithDataSourceCreatedLater() throws InterruptedException {
        // 상황: T-07b 와 같지만 만든 순서가 redis · mq → pool-a → dataSource 다
        runProbe(DataSourceCreatedLaterConfig.class, "③ pool-a destroy 시작");

        // datasource 가 pool-a 에 의존중이다.
        // pool-a 가 생성된 후, datasource 생성

        // Q1 DB 가 닫히는 건 pool-a 의 destroy 보다 먼저된다. (생성의 역순)
        assertThat(order("③ db close", "③ pool-a destroy 시작")).isEqualTo(Order.BEFORE);

        // Q2 DB 는 destroy 되었으므로, 실패한다.
        assertThat(result("db")).isEqualTo(Outcome.FAILURE);

        // Q3 Redis 는 smart lifecycle 로 이미 닫혀있는 상태이므로, 실패한다.
        assertThat(result("redis")).isEqualTo(Outcome.FAILURE);
    }

    @Test
    @DisplayName("T-07d PR 플래그 + ShutdownFirstDrain: drain 이 풀을 비우는 순간 자원은")
    void shutdownFirstDrain() throws InterruptedException {
        // 상황: 풀은 awaitTermination 없음 + ② 의 MAX/2-1 에 drain 이 있다.
        // probe 는 drain 이 접수를 닫은 순간 깨어난다
        runProbe(ShutdownFirstDrainConfig.class, "② drain(shutdown 먼저) 접수 마감");

        // Q1, Q2, Q3 Redis, MQ, DB 는 모두 켜져있는 상태이므로 성공한다.
        assertThat(result("redis")).isEqualTo(Outcome.SUCCESS);
        assertThat(result("mq")).isEqualTo(Outcome.SUCCESS);
        assertThat(result("db")).isEqualTo(Outcome.SUCCESS);
    }

    @Test
    @DisplayName("T-07e PR 플래그 + IdleDrain: drain 이 풀을 비우는 순간 자원은 (IdleDrainLifecycle 을 구현해야 통과한다)")
    void idleDrain() throws InterruptedException {
        // 상황: T-07d 와 같지만 drain 이 IdleDrain 이다. probe 는 "② drain(idle 대기) 시작" 에서 깨어난다
        runProbe(IdleDrainConfig.class, "② drain(idle 대기) 시작");

        assertThat(result("redis")).isEqualTo(Outcome.SUCCESS);   // Q1 Redis 는
//        assertThat(order("  probe 끝", "② redis(phase 0) stop")).isEqualTo(todo());   // Q2 probe 가 끝나는 건 Redis 가 멈추기 전인가 후인가
    }

    /**
     * 종료 중에도 실행 중인 비동기 작업이 Redis·MQ·DB 를 사용할 수 있는지 확인하는 공통 시나리오.
     *
     * <ol>
     * <li>config 로 컨텍스트를 만들고, pool-a 와 Redis·MQ·DB 빈을 가져온다.</li>
     * <li>pool-a 에 probe 작업을 제출한다. probe 는 waitForEvent 가 기록될 때까지 기다린다.</li>
     * <li>테스트 스레드는 "probe 대기" 기록을 확인한 뒤 context.close() 로 종료 절차를 시작한다.</li>
     * <li>probe 는 해당 이벤트를 확인하면 200ms 후 Redis get → MQ publish → DB query 를 호출하고,
     * 각 호출의 성공/실패를 타임라인에 기록한다. 이벤트 대기 중 interrupt 되면 호출 없이 끝난다.</li>
     * <li>closeAndSettle 은 close() 후에도 남은 풀 스레드의 종료를 기다려 타임라인을 수집한다.
     * 호출자는 result("redis"), result("mq"), result("db") 로 결과를 검증한다.</li>
     * </ol>
     *
     * <p>waitForEvent 는 작업을 재개할 기준이다. 실제 자원 접근은 이벤트 직후가 아니라 200ms 뒤에 일어난다.
     */
    private static void runProbe(Class<?> config, String waitForEvent) throws InterruptedException {
        AnnotationConfigApplicationContext context = new AnnotationConfigApplicationContext(config);
        TracingThreadPoolTaskExecutor poolA = context.getBean("poolA", TracingThreadPoolTaskExecutor.class);
        Runnable probe = Probe.afterEvent(waitForEvent,
                context.getBean(FakeRedisConnectionFactory.class),
                context.getBean(FakeMqConnectionFactory.class),
                context.getBean(FakeDataSource.class));
        Tasks.submit(poolA, "probe", probe);
        // 작업이 시작되어 대기 진입을 기록한 뒤 종료한다. 종료 이벤트 뒤에 작업을 새로 제출하는 실험이 아니다.
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

    /**
     * 수정안: PR 플래그는 두고 awaitTermination 은 빼고, 비우는 일은 drain 이 맡는다.
     */
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

    /**
     * ScenarioConfig 와 같지만 DataSource 를 풀보다 늦게 만든다. destroy 는 생성 역순이라 DataSource 가 풀보다 먼저 닫힌다.
     */
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
