package playground.shutdown.stage4;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.context.annotation.AnnotationConfigApplicationContext;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import playground.shutdown.drain.IdleDrainLifecycle;
import playground.shutdown.drain.ShutdownFirstDrainLifecycle;
import playground.shutdown.executor.Pools;
import playground.shutdown.executor.Tasks;
import playground.shutdown.executor.TracingThreadPoolTaskExecutor;
import playground.shutdown.resource.FakeRedisConnectionFactory;
import playground.shutdown.support.ScenarioConfig;
import playground.shutdown.support.Shutdown;
import playground.shutdown.timeline.Timeline;

import java.time.Duration;
import java.util.List;
import java.util.function.BooleanSupplier;

import static org.assertj.core.api.Assertions.assertThat;
import static playground.shutdown.support.Predict.todo;
import static playground.shutdown.support.TimelineQuery.order;
import static playground.shutdown.support.TimelineQuery.result;
import static playground.shutdown.support.TimelineQuery.submit;

/**
 * stage4: 풀 안의 작업 A 가 종료 도중 같은 풀에 다음 작업 B 를 넘긴다. B 는 300ms 뒤 Redis 를 쓴다.
 * 실서비스의 CreateTask(@Async) → 커밋 → ProduceTask(@Async) 체인을 줄인 것이다.
 *
 * <pre>
 * 보기: submit → "접수" "거절" · result → "성공" "실패" "없음"(시도조차 못 함) · order → "먼저" "나중"
 * </pre>
 *
 * <p>규칙: 실행하기 전에 {@code todo()} 를 내 예측값으로 바꾼다. 답지는 docs/05 와 git 이전 커밋에 있다.
 */
class AsyncChainTest {

    private static final Duration WAIT = Duration.ofSeconds(5);

    @BeforeEach
    void setUp() {
        Timeline.reset();
    }

    @Test
    @DisplayName("T-08a PR 설정: 풀이 ③ 에서 접수를 닫은 뒤 넘긴 B 는")
    void waitForTasksRejectsChainedTask() throws InterruptedException {
        runChain(WaitForTasksConfig.class, "③ pool-a destroy 시작");

        assertThat(submit("B")).isEqualTo("거절");   // Q1
        assertThat(result("B redis")).isEqualTo("없음");   // Q2
    }

    @Test
    @DisplayName("T-08b ShutdownFirstDrain: drain 이 비우는 도중 넘긴 B 는")
    void shutdownFirstDrainRejectsChainedTask() throws InterruptedException {
        runChain(ShutdownFirstDrainConfig.class, "② drain(shutdown 먼저) 접수 마감");

        assertThat(submit("B")).isEqualTo("거절");   // Q1
    }

    @Test
    @DisplayName("T-08c IdleDrain: drain 이 비우는 도중 넘긴 B 는 (IdleDrainLifecycle 을 구현해야 통과한다)")
    void idleDrainRunsChainedTask() throws InterruptedException {
        runChain(IdleDrainConfig.class, "② drain(idle 대기) 시작");

        assertThat(submit("B")).isEqualTo("접수");   // Q1
        assertThat(result("B redis")).isEqualTo("성공");   // Q2
        assertThat(order("  B redis", "② redis(phase 0) stop")).isEqualTo("먼저");   // Q3 B 의 Redis 호출은 Redis 가 멈추기 먼저인가 나중인가
    }

    @Test
    @DisplayName("T-08d 기본값: ② MAX/2 가 시작된 뒤 넘긴 B 는")
    void defaultModeDoesNotWaitForChainedTask() throws InterruptedException {
        runChain(DefaultConfig.class, "② pool-a lifecycle stop 시작");

        assertThat(submit("B")).isEqualTo("접수");   // Q1
        assertThat(result("B redis")).isEqualTo("없음");   // Q2 B 는 Redis 까지 가나 (lifecycle 이 B 를 기다려 주나)
    }

    /**
     * pool-a 에서 A 를 실행한다. A 는 waitForEvent 가 찍히고 (PR 설정이면 풀이 실제로 닫힐 때까지) 기다린 뒤 B 를 넘긴다.
     */
    private static void runChain(Class<?> config, String waitForEvent) throws InterruptedException {
        AnnotationConfigApplicationContext context = new AnnotationConfigApplicationContext(config);
        TracingThreadPoolTaskExecutor poolA = context.getBean("poolA", TracingThreadPoolTaskExecutor.class);
        FakeRedisConnectionFactory redis = context.getBean(FakeRedisConnectionFactory.class);

        Runnable taskB = () -> {
            Timeline.record("  task B 시작");
            if (Tasks.sleepQuietly(300)) {
                Tasks.attempt("B redis", () -> redis.get("k"));
            } else {
                Timeline.record("  task B interrupt 됨");
            }
        };
        Runnable taskA = () -> {
            Timeline.record("  task A 시작");
            try {
                Timeline.awaitEvent(waitForEvent, WAIT);
                // PR 설정은 "destroy 시작" 을 찍은 뒤에 shutdown() 이 불린다. 실제로 닫힐 때까지 기다려 경합을 없앤다
                if (config == WaitForTasksConfig.class) {
                    awaitUntil(() -> poolA.getThreadPoolExecutor().isShutdown());
                }
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                return;
            }
            Tasks.submit(poolA, "B", taskB);
            Timeline.record("  task A 끝");
        };
        Tasks.submit(poolA, "A", taskA);
        Timeline.awaitEvent("  task A 시작", WAIT);

        Shutdown.closeAndSettle(context);
    }

    private static void awaitUntil(BooleanSupplier condition) throws InterruptedException {
        long deadline = System.nanoTime() + WAIT.toNanos();
        while (!condition.getAsBoolean() && System.nanoTime() < deadline) {
            Thread.sleep(1);
        }
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
}
