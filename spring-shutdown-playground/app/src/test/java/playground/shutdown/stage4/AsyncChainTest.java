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
import playground.shutdown.support.Order;
import playground.shutdown.support.Outcome;
import playground.shutdown.support.ScenarioConfig;
import playground.shutdown.support.Shutdown;
import playground.shutdown.support.Submission;
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
 * stage4: 풀 안의 작업이 종료 도중 같은 풀에 "다음 작업" 을 넘기면 어떻게 되는지 예측한다.
 *
 * <h2>무엇을 하나</h2>
 * <pre>
 * pool-a 에서 작업 A 가 돈다
 *   A 는 테스트마다 정한 이벤트(= 풀이 기다리기 시작한 순간)까지 기다렸다가
 *   같은 pool-a 에 작업 B 를 넘긴다 (submit("B"))
 *     B 는 300ms 일한 뒤 Redis 를 써 본다 (result("B redis"))
 * </pre>
 * 실서비스의 CreateTask(@Async) → 커밋 → ProduceTask(@Async) 체인을 줄인 것이다.
 * 풀·자원 구성은 stage2·stage3 머리말과 같다.
 *
 * <h2>질문이 가리키는 타임라인 이벤트</h2>
 * <pre>
 * "  submit B" / "  submit B 거절됨"   A 가 B 를 넘긴 때 / 거절된 때
 * "  B redis → …"                      B 가 Redis 를 써 본 결과
 * "② redis(phase 0) stop"              Redis 가 멈춘 때
 * </pre>
 *
 * <p>규칙: 실행하기 전에 {@code todo()} 를 내 예측으로 바꾼다. 보기는 {@link Submission} · {@link Outcome} · {@link Order} enum 이다.
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
        // 상황: waitForTasksToCompleteOnShutdown(true) 풀. A 는 ③ 에서 pool-a 가 shutdown() 된 직후에 B 를 넘긴다
        runChain(WaitForTasksConfig.class, "③ pool-a destroy 시작");

        assertThat(submit("B")).isEqualTo(Submission.REJECTED);   // Q1 B 는
        assertThat(result("B redis")).isEqualTo(Outcome.NOT_ATTEMPTED);   // Q2 B 의 Redis 호출은
    }

    @Test
    @DisplayName("T-08b ShutdownFirstDrain: drain 이 접수를 닫은 뒤 넘긴 B 는")
    void shutdownFirstDrainRejectsChainedTask() throws InterruptedException {
        // 상황: drain 이 풀을 shutdown() 한 직후에 A 가 B 를 넘긴다
        runChain(ShutdownFirstDrainConfig.class, "② drain(shutdown 먼저) 접수 마감");

        assertThat(submit("B")).isEqualTo(Submission.REJECTED);   // Q1 B 는
    }

    @Test
    @DisplayName("T-08c IdleDrain: drain 이 풀을 비우는 도중 넘긴 B 는 (IdleDrainLifecycle 을 구현해야 통과한다)")
    void idleDrainRunsChainedTask() throws InterruptedException {
        // 상황: drain 이 시작된 직후에 A 가 B 를 넘긴다
        runChain(IdleDrainConfig.class, "② drain(idle 대기) 시작");

        assertThat(submit("B")).isEqualTo(Submission.ACCEPTED);   // Q1 B 는
        assertThat(result("B redis")).isEqualTo(Outcome.SUCCESS);   // Q2 B 의 Redis 호출은
        assertThat(order("  B redis", "② redis(phase 0) stop")).isEqualTo(Order.BEFORE);   // Q3 B 의 Redis 호출은 Redis 가 멈추기 전인가 후인가
    }

    @Test
    @DisplayName("T-08d 기본값: ② 에서 pool-a 의 stop 이 시작된 뒤 넘긴 B 는")
    void defaultModeDoesNotWaitForChainedTask() throws InterruptedException {
        // 상황: 기본값 풀. A 는 "② pool-a lifecycle stop 시작" 직후에 B 를 넘기고 끝난다
        runChain(DefaultConfig.class, "② pool-a lifecycle stop 시작");

        assertThat(submit("B")).isEqualTo(Submission.ACCEPTED);   // Q1 B 는
        assertThat(result("B redis")).isEqualTo(Outcome.NOT_ATTEMPTED);   // Q2 B 의 Redis 호출은 (lifecycle 이 B 까지 기다려 주나)
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
