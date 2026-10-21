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
import playground.shutdown.support.Order;
import playground.shutdown.support.ScenarioConfig;
import playground.shutdown.support.Shutdown;
import playground.shutdown.support.Stage;
import playground.shutdown.support.Submission;
import playground.shutdown.support.ThreadRole;
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
 * stage2: 풀 2개의 종료 설정만 바꿔 가며, 남은 작업이 언제·어떻게 끝나는지 예측한다.
 *
 * <h2>종료 단계 — 답의 {@link Stage}</h2>
 * <pre>
 * close()
 *  ① CONTEXT_CLOSED_EVENT  ContextClosedEvent 를 리스너에게 알린다. 아직 아무것도 멈추지 않는다
 *  ② LIFECYCLE_STOP        SmartLifecycle 의 stop() 을 phase 가 큰 빈부터 부른다
 *                          같은 phase 는 한 묶음이고, 묶음마다 timeout(여기선 1초)까지 callback 을 기다린다
 *                          같은 묶음 안에서는 다른 빈에 의존하는 빈을 먼저 멈춘다
 *  ③ BEAN_DESTROY          @PreDestroy · DisposableBean · close() 를 close 를 부른 스레드 하나가 차례로 부른다
 *                          다른 빈에 의존하는 빈이 먼저, 그 외에는 만든 역순이다
 * </pre>
 *
 * <h2>이 컨텍스트의 빈 — {@link ScenarioConfig}</h2>
 * <pre>
 * pool-a, pool-b  ThreadPoolTaskExecutor. 스레드 1개 + 대기열 10칸
 *                 둘 다 SmartLifecycle phase = MAX/2 라서 ② 에서 같은 묶음으로 함께 stop 된다
 *                 pool-b 는 pool-a 에 의존한다 (@DependsOn("poolA"))
 * redis           가짜 Redis. SmartLifecycle phase 0. stop 뒤에는 연결을 거절한다 (Lettuce 흉내)
 * mq              가짜 MQ. SmartLifecycle phase MIN. stop 때 끊고 다음 요청 때 재연결한다 (Rabbit 흉내)
 * dataSource      가짜 DB. Lifecycle 없음. destroy 때만 닫힌다 (Hikari 흉내)
 * 만든 순서       redis · mq · dataSource → pool-a → pool-b → destroyMarker
 * </pre>
 *
 * <h2>질문이 가리키는 타임라인 이벤트</h2>
 * <pre>
 * "  task a1 시작" / "끝" / "interrupt 됨"   풀 안의 작업 a1 이 시작·끝·interrupt 된 때
 * "  submit b1" / "  submit b1 거절됨"        풀에 b1 을 넘긴 때 / 거절된 때
 * "② pool-a lifecycle stop 시작"              ② 에서 pool-a 의 stop(callback) 이 불린 때 (pool-b 도 같은 형식)
 * "② pool-a lifecycle stop 완료"              pool-a 가 그 callback 을 부른 때 (= pool-a 의 stop 이 끝났다고 알린 때)
 * "② redis(phase 0) stop"                     ② 에서 Redis 가 멈춘 때
 * "③ destroy 단계 시작 (marker)"              ③ 이 시작된 때 (가장 나중에 만든 빈이 가장 먼저 destroy 된다)
 * "③ pool-a destroy 시작" / "끝"              ③ 에서 pool-a 의 destroy() 가 불린 때 / 끝난 때
 * </pre>
 *
 * <p>규칙: 실행하기 전에 {@code todo()} 를 내 예측으로 바꾼다. 한 번에 테스트 하나씩 돌린다.
 * 보기는 enum 이다 ({@link Stage} · {@link Order} · {@link ThreadRole} · {@link Submission}). 상수에 마우스를 올리면 설명이 보인다.
 * {@code secondsBetween} 은 반올림한 정수 초(long), {@code happened} 는 true/false 다.
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
            // 상황: pool-a 에서 500ms 짜리 a1 이 도는 중에 close() 를 부른다
            AnnotationConfigApplicationContext context = new AnnotationConfigApplicationContext(DefaultConfig.class);
            TracingThreadPoolTaskExecutor poolA = context.getBean("poolA", TracingThreadPoolTaskExecutor.class);
            Tasks.submit(poolA, "a1", Tasks.sleeping("a1", 500));
            Timeline.awaitEvent("  task a1 시작", WAIT);

            Shutdown.closeAndSettle(context);

            // Q1 a1 은 pool-a 가 끝날때까지 기다려준다.
            assertThat(stageOf("  task a1 끝")).isEqualTo(Stage.LIFECYCLE_STOP);

            // Q2 pool-a 는 task a1 완료까지 기다리고, redis 는 phase 0 이므로 PoolTaskExecutor 가 먼저 끝난다.
            assertThat(order("  task a1 끝", "② redis(phase 0) stop")).isEqualTo(Order.BEFORE);

            // Q3 pool-a 의 라이프사이클 종료는 pool-a 가 담당한다.
            assertThat(threadOf("② pool-a lifecycle stop 완료")).isEqualTo(ThreadRole.POOL_A);
        }

        @Test
        @DisplayName("T-04b 스레드 1개에 a1(200ms) 실행 중 + a2(1500ms) 대기열 — a2 도 기다려 주나")
        void doesNotWaitForQueuedTask() throws InterruptedException {
            // 상황: pool-a 의 스레드는 1개라, a1 이 도는 동안 a2 는 대기열에 있다. 그 상태로 close() 를 부른다
            AnnotationConfigApplicationContext context = new AnnotationConfigApplicationContext(DefaultConfig.class);
            TracingThreadPoolTaskExecutor poolA = context.getBean("poolA", TracingThreadPoolTaskExecutor.class);
            Tasks.submit(poolA, "a1", Tasks.sleeping("a1", 200));
            Tasks.submit(poolA, "a2", Tasks.sleeping("a2", 1500));
            Timeline.awaitEvent("  task a1 시작", WAIT);

            Shutdown.closeAndSettle(context);

            // Q1 poolA 는 a2 의 작업 완료까지는 기다려주지 않는다.
            assertThat(secondsBetween("  task a1 시작", "② pool-a lifecycle stop 완료")).isEqualTo(0);
            // Q2 대기열의 a2 는 처리될 수 없다.
            // - 대기열에 있다면, 꺼내지고 취소된다.
            // - 대기열에 없고 실행됐다면, Interrupt 호출이 발생한다.
            assertThat(happened("  task a2 끝")).isEqualTo(false);
        }

        @Test
        @DisplayName("T-04c phase timeout(1초)보다 긴 작업(3초)은 어떻게 되나")
        void interruptsTaskLongerThanPhaseTimeout() throws InterruptedException {
            // 상황: pool-a 에서 3초 짜리 a1 이 도는 중에 close() 를 부른다. phase timeout 은 1초다
            AnnotationConfigApplicationContext context = new AnnotationConfigApplicationContext(DefaultConfig.class);
            TracingThreadPoolTaskExecutor poolA = context.getBean("poolA", TracingThreadPoolTaskExecutor.class);
            Tasks.submit(poolA, "a1", Tasks.sleeping("a1", 3000));
            Timeline.awaitEvent("  task a1 시작", WAIT);

            Timeline.record("close() 호출");
            Shutdown.closeAndSettle(context);

            // Q1 a1 을 phase 타임아웃 까지만 기다리고, 포기하면 close(destroy) 가 진행된다. a1 을 끊진 않는다.
            assertThat(secondsBetween("close() 호출", "③ pool-a destroy 시작")).isEqualTo(1);

            // Q2 LifeCycle 때는 넘어갔지만, Pool Destroy 때 Interrupt 가 발생한다.
            assertThat(stageOf("  task a1 interrupt 됨")).isEqualTo(Stage.BEAN_DESTROY);
        }

        @Test
        @DisplayName("T-04d 종료가 시작된 뒤에 넘긴 작업은 거절되나")
        void acceptsTaskSubmittedDuringShutdown() throws InterruptedException {
            // 상황: pool-a 의 작업이 "② pool-a lifecycle stop 시작" 을 기다렸다가 pool-b 에 500ms 짜리 b1 을 넘긴다
            AnnotationConfigApplicationContext context = new AnnotationConfigApplicationContext(DefaultConfig.class);
            TracingThreadPoolTaskExecutor poolA = context.getBean("poolA", TracingThreadPoolTaskExecutor.class);
            TracingThreadPoolTaskExecutor poolB = context.getBean("poolB", TracingThreadPoolTaskExecutor.class);
            Tasks.submit(poolA, "a1", () -> {
                Timeline.record("  task a1 시작");
                awaitQuietly("② pool-a lifecycle stop 시작");
                awaitQuietly("② pool-b lifecycle stop 시작");
                Tasks.submit(poolB, "b1", Tasks.sleeping("b1", 500));
            });
            Timeline.awaitEvent("  task a1 시작", WAIT);

            Shutdown.closeAndSettle(context);

            // Q1 종료가 되더라도, 진행중인 작업은 계속되고 -> pool-b 에 넣는다.
            assertThat(submit("b1")).isEqualTo(Submission.ACCEPTED);

            //
            assertThat(order("② pool-b lifecycle stop 완료", "  submit b1")).isEqualTo(Order.BEFORE);   // Q2 b1 을 넘긴 건 pool-b 의 stop 이 끝나기 전인가 후인가
//            assertThat(happened("  task b1 끝")).isEqualTo(todo());   // Q3 접수된 b1(500ms) 은 끝까지 도나
        }
    }

    @Nested
    @DisplayName("waitForTasksToCompleteOnShutdown(true) + awaitTermination 1초 ")
    class WaitForTasksMode {

        @Test
        @DisplayName("T-05 풀 2개에 1.5초 작업 — 어디서 기다리나, 풀끼리 동시인가 차례인가, 1초를 넘기면 끊나")
        void waitsInDestroyOnePoolAtATime() throws InterruptedException {
            // 상황: pool-a 에 a1, pool-b 에 b1 (둘 다 1.5초) 이 도는 중에 close() 를 부른다. 풀마다 awaitTermination 은 1초다
            AnnotationConfigApplicationContext context = new AnnotationConfigApplicationContext(WaitForTasksConfig.class);
            TracingThreadPoolTaskExecutor poolA = context.getBean("poolA", TracingThreadPoolTaskExecutor.class);
            TracingThreadPoolTaskExecutor poolB = context.getBean("poolB", TracingThreadPoolTaskExecutor.class);
            Tasks.submit(poolA, "a1", Tasks.sleeping("a1", 1500));
            Tasks.submit(poolB, "b1", Tasks.sleeping("b1", 1500));
            Timeline.awaitEvent("  task a1 시작", WAIT);
            Timeline.awaitEvent("  task b1 시작", WAIT);

            Shutdown.closeAndSettle(context);

            // Q1 설정과 + awaitTermination 설정을 하면, 작업을 기다리지 않는다. (lifecycle 바로 진행)
            assertThat(secondsBetween("② pool-a lifecycle stop 시작", "② pool-a lifecycle stop 완료")).isEqualTo(0);

            // Q2 Redis 는 task a1 의 종료에 영향을 받지 않는다.
            // task 가 lifecycle 을 잡지 않으므로, 정상 진행
            assertThat(order("② redis(phase 0) stop", "  task a1 끝")).isEqualTo(Order.BEFORE);

            // Q3 pool-b 가 pool-a 에 의존하므로, pool-b 가 먼저 소멸이 된다. (생성과 반대)
            // 기본적으로, 의존이 안되어 있더라도 생성의 역순이므로 b -> a 순으로 destory 되긴한다.
            assertThat(order("③ pool-a destroy 시작", "③ pool-b destroy 시작")).isEqualTo(Order.AFTER);

            // Q4 pool-b 의 destroy 가 awaitTermination 만큼 대기하고 끝난다.
            assertThat(secondsBetween("③ pool-b destroy 시작", "③ pool-b destroy 끝")).isEqualTo(1);
            // Q5 b1 은 1초 상한을 넘겨도 바로 interrupt 되지 않는다.
            assertThat(happened("  task b1 interrupt 됨")).isEqualTo(false);
        }
    }

    @Nested
    @DisplayName("strictEarlyShutdown(true)")
    class StrictEarlyShutdownMode {

        @Test
        @DisplayName("T-06 종료 이벤트 뒤에 넘긴 작업은 거절되나")
        void rejectsAfterContextClosedEvent() throws InterruptedException {
            // 상황: T-04d 와 같다. 설정만 strictEarlyShutdown 이다
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

            // Q1 pool-b 가 종료된 상태 + strictEarlyShutdown 이 켜져있으므로 요청을 거부한다.
            assertThat(submit("b1")).isEqualTo(Submission.REJECTED);
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
