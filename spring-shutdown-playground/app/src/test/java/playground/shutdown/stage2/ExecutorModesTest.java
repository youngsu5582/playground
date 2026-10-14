package playground.shutdown.stage2;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.springframework.context.annotation.AnnotationConfigApplicationContext;
import org.springframework.context.annotation.Configuration;
import playground.shutdown.executor.Pools;
import playground.shutdown.executor.Tasks;
import playground.shutdown.executor.TracingThreadPoolTaskExecutor;
import playground.shutdown.support.ScenarioConfig;
import playground.shutdown.support.Shutdown;
import playground.shutdown.timeline.Timeline;

import java.time.Duration;

import static org.assertj.core.api.Assertions.assertThat;
import static playground.shutdown.support.Predict.todo;
import static playground.shutdown.support.TimelineQuery.happened;
import static playground.shutdown.support.TimelineQuery.order;
import static playground.shutdown.support.TimelineQuery.secondsBetween;
import static playground.shutdown.support.TimelineQuery.stageOf;
import static playground.shutdown.support.TimelineQuery.submit;
import static playground.shutdown.support.TimelineQuery.threadOf;

/**
 * stage2: 풀 2개(pool-a, pool-b)의 종료 설정만 바꿔 가며, 남은 작업이 언제·어떻게 끝나는지 예측한다.
 * 각 풀은 스레드 1개 + 대기열 10칸, phase timeout 은 1초다 (구성은 {@link ScenarioConfig}).
 *
 * <p>규칙: 실행하기 전에 {@code todo()} 를 내 예측값으로 바꾼다. 한 번에 테스트 하나씩 돌린다.
 * 답지는 docs/03 과 git 이전 커밋에 있다.
 *
 * <pre>
 * 보기: stageOf → "종료 전" "①" "②" "③" · order → "먼저" "나중" · submit → "접수" "거절"
 *       secondsBetween → 정수 초(long) · happened → true/false · threadOf → "Test worker" "pool-a-1" …
 * </pre>
 */
class ExecutorModesTest {

    private static final Duration WAIT = Duration.ofSeconds(5);

    @BeforeEach
    void setUp() {
        Timeline.reset();
    }

    @Nested
    @DisplayName("기본값 (아무것도 설정하지 않음)")
    class DefaultMode {

        @Test
        @DisplayName("T-04a 실행 중인 작업(500ms)은 기다려 주나, 기다린다면 어디서")
        void waitsForRunningTaskInLifecycle() throws InterruptedException {
            AnnotationConfigApplicationContext context = new AnnotationConfigApplicationContext(DefaultConfig.class);
            TracingThreadPoolTaskExecutor poolA = context.getBean("poolA", TracingThreadPoolTaskExecutor.class);
            Tasks.submit(poolA, "a1", Tasks.sleeping("a1", 500));
            Timeline.awaitEvent("  task a1 시작", WAIT);

            Shutdown.closeAndSettle(context);

            assertThat(stageOf("  task a1 끝")).isEqualTo(todo());   // Q1 a1 은 어느 단계 안에서 끝나나
            assertThat(order("  task a1 끝", "② redis(phase 0) stop")).isEqualTo(todo());   // Q2 a1 이 끝나는 건 Redis 가 멈추기 먼저인가 나중인가
            assertThat(threadOf("② pool-a lifecycle stop 완료")).isEqualTo(todo());   // Q3 pool-a 의 lifecycle stop 을 '완료' 시키는 스레드는
        }

        @Test
        @DisplayName("T-04b 스레드 1개에 a1(200ms) 실행 중 + a2(1500ms) 대기열 — a2 도 기다려 주나")
        void doesNotWaitForQueuedTask() throws InterruptedException {
            AnnotationConfigApplicationContext context = new AnnotationConfigApplicationContext(DefaultConfig.class);
            TracingThreadPoolTaskExecutor poolA = context.getBean("poolA", TracingThreadPoolTaskExecutor.class);
            Tasks.submit(poolA, "a1", Tasks.sleeping("a1", 200));
            Tasks.submit(poolA, "a2", Tasks.sleeping("a2", 1500));   // 스레드가 1개라 대기열에 쌓인다
            Timeline.awaitEvent("  task a1 시작", WAIT);

            Shutdown.closeAndSettle(context);

            assertThat(secondsBetween("  task a1 시작", "② pool-a lifecycle stop 완료")).isEqualTo(todo());   // Q1 lifecycle stop 이 완료되기까지 몇 초 걸리나 (a2 까지 기다리면 2초)
            assertThat(happened("  task a2 끝")).isEqualTo(todo());   // Q2 대기열의 a2 는 끝까지 실행되나
        }

        @Test
        @DisplayName("T-04c phase timeout(1초)보다 긴 작업(3초)은 어떻게 되나")
        void interruptsTaskLongerThanPhaseTimeout() throws InterruptedException {
            AnnotationConfigApplicationContext context = new AnnotationConfigApplicationContext(DefaultConfig.class);
            TracingThreadPoolTaskExecutor poolA = context.getBean("poolA", TracingThreadPoolTaskExecutor.class);
            Tasks.submit(poolA, "a1", Tasks.sleeping("a1", 3000));
            Timeline.awaitEvent("  task a1 시작", WAIT);

            Timeline.record("close() 호출");
            Shutdown.closeAndSettle(context);

            assertThat(secondsBetween("close() 호출", "③ pool-a destroy 시작")).isEqualTo(todo());   // Q1 close 부터 pool-a destroy 까지 몇 초
            assertThat(stageOf("  task a1 interrupt 됨")).isEqualTo(todo());   // Q2 a1 이 interrupt 되는 단계는
        }

        @Test
        @DisplayName("T-04d 종료가 시작된 뒤에 넘긴 작업은 거절되나")
        void acceptsTaskSubmittedDuringShutdown() throws InterruptedException {
            AnnotationConfigApplicationContext context = new AnnotationConfigApplicationContext(DefaultConfig.class);
            TracingThreadPoolTaskExecutor poolA = context.getBean("poolA", TracingThreadPoolTaskExecutor.class);
            TracingThreadPoolTaskExecutor poolB = context.getBean("poolB", TracingThreadPoolTaskExecutor.class);
            Tasks.submit(poolA, "a1", () -> {
                Timeline.record("  task a1 시작");
                awaitQuietly("② pool-a lifecycle stop 시작");
                Tasks.submit(poolB, "b1", Tasks.sleeping("b1", 10));
            });
            Timeline.awaitEvent("  task a1 시작", WAIT);

            Shutdown.closeAndSettle(context);

            assertThat(submit("b1")).isEqualTo(todo());   // Q1 ② 가 시작된 뒤 pool-b 에 넘긴 b1 은
        }
    }

    @Nested
    @DisplayName("waitForTasksToCompleteOnShutdown(true) + awaitTermination 1초 (PR 4341 설정)")
    class WaitForTasksMode {

        @Test
        @DisplayName("T-05 풀 2개에 1.5초 작업 — 어디서 기다리나, 풀끼리 동시인가 차례인가, 1초를 넘기면 끊나")
        void waitsInDestroyOnePoolAtATime() throws InterruptedException {
            AnnotationConfigApplicationContext context = new AnnotationConfigApplicationContext(WaitForTasksConfig.class);
            TracingThreadPoolTaskExecutor poolA = context.getBean("poolA", TracingThreadPoolTaskExecutor.class);
            TracingThreadPoolTaskExecutor poolB = context.getBean("poolB", TracingThreadPoolTaskExecutor.class);
            Tasks.submit(poolA, "a1", Tasks.sleeping("a1", 1500));
            Tasks.submit(poolB, "b1", Tasks.sleeping("b1", 1500));
            Timeline.awaitEvent("  task a1 시작", WAIT);
            Timeline.awaitEvent("  task b1 시작", WAIT);

            Shutdown.closeAndSettle(context);

            assertThat(secondsBetween("② pool-a lifecycle stop 시작", "② pool-a lifecycle stop 완료")).isEqualTo(todo());   // Q1 ② 에서 몇 초 기다리나
            assertThat(order("② redis(phase 0) stop", "  task a1 끝")).isEqualTo(todo());   // Q2 Redis 가 멈추는 건 작업이 끝나기 먼저인가 나중인가
            assertThat(order("③ pool-a destroy 시작", "③ pool-b destroy 시작")).isEqualTo(todo());   // Q3 pool-a 의 destroy 는 pool-b 보다 먼저인가 나중인가
            assertThat(secondsBetween("③ pool-b destroy 시작", "③ pool-b destroy 끝")).isEqualTo(todo());   // Q4 pool-b 의 destroy 는 몇 초 걸리나
            assertThat(happened("  task b1 interrupt 됨")).isEqualTo(todo());   // Q5 1초 상한을 넘긴 b1 은 끊기나
        }
    }

    @Nested
    @DisplayName("strictEarlyShutdown(true)")
    class StrictEarlyShutdownMode {

        @Test
        @DisplayName("T-06 종료 이벤트 뒤에 넘긴 작업은 거절되나")
        void rejectsAfterContextClosedEvent() throws InterruptedException {
            AnnotationConfigApplicationContext context = new AnnotationConfigApplicationContext(StrictConfig.class);
            TracingThreadPoolTaskExecutor poolA = context.getBean("poolA", TracingThreadPoolTaskExecutor.class);
            TracingThreadPoolTaskExecutor poolB = context.getBean("poolB", TracingThreadPoolTaskExecutor.class);
            Tasks.submit(poolA, "a1", () -> {
                Timeline.record("  task a1 시작");
                awaitQuietly("② pool-a lifecycle stop 시작");
                Tasks.submit(poolB, "b1", Tasks.sleeping("b1", 10));
            });
            Timeline.awaitEvent("  task a1 시작", WAIT);

            Shutdown.closeAndSettle(context);

            assertThat(submit("b1")).isEqualTo(todo());   // Q1 ② 가 시작된 뒤 pool-b 에 넘긴 b1 은 (T-04d 와 비교)
        }
    }

    private static void awaitQuietly(String event) {
        try {
            Timeline.awaitEvent(event, WAIT);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }

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
    static class StrictConfig extends ScenarioConfig {
        @Override
        protected Pools.Mode mode() {
            return Pools.Mode.STRICT_EARLY_SHUTDOWN;
        }
    }
}
