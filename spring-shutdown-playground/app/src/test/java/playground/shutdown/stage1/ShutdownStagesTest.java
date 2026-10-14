package playground.shutdown.stage1;

import jakarta.annotation.PreDestroy;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.DisposableBean;
import org.springframework.context.ApplicationListener;
import org.springframework.context.SmartLifecycle;
import org.springframework.context.annotation.AnnotationConfigApplicationContext;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.DependsOn;
import org.springframework.context.event.ContextClosedEvent;
import org.springframework.context.support.DefaultLifecycleProcessor;
import playground.shutdown.executor.Tasks;
import playground.shutdown.timeline.Timeline;

import static org.assertj.core.api.Assertions.assertThat;
import static playground.shutdown.support.TimelineAssert.inOrder;
import static playground.shutdown.support.TimelineAssert.millisBetween;

/**
 * stage1: 풀 없이 Spring 이 컨텍스트를 닫는 순서만 본다.
 */
class ShutdownStagesTest {

    @BeforeEach
    void setUp() {
        Timeline.reset();
    }

    @Test
    @DisplayName("T-01 종료는 ① 종료 이벤트 → ② lifecycle stop(phase 큰 순) → ③ destroy(생성 역순) 순서로만 진행된다")
    void threeStagesInOrder() {
        AnnotationConfigApplicationContext context = new AnnotationConfigApplicationContext(StagesConfig.class);
        Timeline.reset();

        context.close();

        inOrder(
                "① ContextClosedEvent 수신",
                "② stop phase=1000 web-like",
                "② stop phase=0 redis-like",
                "② stop phase=-1000 mq-like",
                "③ destroy third",
                "③ destroy second",
                "③ destroy first");
    }

    @Test
    @DisplayName("T-01b 한 빈 안에서는 @PreDestroy → DisposableBean.destroy() → destroyMethod 순서로 불린다")
    void destroyCallbacksInsideOneBean() {
        AnnotationConfigApplicationContext context = new AnnotationConfigApplicationContext(CallbacksConfig.class);
        Timeline.reset();

        context.close();

        inOrder("③ @PreDestroy", "③ DisposableBean.destroy()", "③ destroyMethod(customClose)");
    }

    @Test
    @DisplayName("T-02 destroy 는 close 를 부른 스레드 하나가 빈을 하나씩 차례로 처리한다 (앞 빈이 끝나야 다음 빈)")
    void destroyIsSequentialOnClosingThread() {
        AnnotationConfigApplicationContext context = new AnnotationConfigApplicationContext(SlowDestroyConfig.class);
        Timeline.reset();
        String closingThread = Thread.currentThread().getName();

        context.close();

        inOrder("③ slow-2 destroy 시작", "③ slow-2 destroy 끝", "③ slow-1 destroy 시작", "③ slow-1 destroy 끝");
        assertThat(millisBetween("③ slow-2 destroy 시작", "③ slow-1 destroy 시작")).isGreaterThanOrEqualTo(280);
        assertThat(Timeline.first("③ slow-2 destroy 시작").thread()).isEqualTo(closingThread);
        assertThat(Timeline.first("③ slow-1 destroy 시작").thread()).isEqualTo(closingThread);
    }

    @Test
    @DisplayName("T-03 timeout-per-shutdown-phase 는 phase 묶음마다 걸리는 상한이다. 넘기면 기다리지 않고 다음 phase 로 넘어간다")
    void phaseTimeoutMovesOn() {
        AnnotationConfigApplicationContext context = new AnnotationConfigApplicationContext(PhaseTimeoutConfig.class);
        Timeline.reset();

        context.close();

        inOrder("② stuck(phase 100) stop 시작", "② stop phase=0 after-stuck");
        assertThat(millisBetween("② stuck(phase 100) stop 시작", "② stop phase=0 after-stuck")).isGreaterThanOrEqualTo(450);
    }

    // ---------------------------------------------------------------- 구성

    @Configuration
    static class StagesConfig {

        @Bean
        public ClosedEventRecorder closedEventRecorder() {
            return new ClosedEventRecorder();
        }

        @Bean
        public PhasedBean webLike() {
            return new PhasedBean("web-like", 1000);
        }

        @Bean
        public PhasedBean redisLike() {
            return new PhasedBean("redis-like", 0);
        }

        @Bean
        public PhasedBean mqLike() {
            return new PhasedBean("mq-like", -1000);
        }

        @Bean
        public DestroyRecorder first() {
            return new DestroyRecorder("first");
        }

        @Bean
        @DependsOn("first")
        public DestroyRecorder second() {
            return new DestroyRecorder("second");
        }

        @Bean
        @DependsOn("second")
        public DestroyRecorder third() {
            return new DestroyRecorder("third");
        }
    }

    @Configuration
    static class CallbacksConfig {

        @Bean(destroyMethod = "customClose")
        public DestroyCallbacksBean callbacks() {
            return new DestroyCallbacksBean();
        }
    }

    @Configuration
    static class SlowDestroyConfig {

        @Bean
        public SlowDestroyBean slow1() {
            return new SlowDestroyBean("slow-1");
        }

        @Bean
        @DependsOn("slow1")
        public SlowDestroyBean slow2() {
            return new SlowDestroyBean("slow-2");
        }
    }

    @Configuration
    static class PhaseTimeoutConfig {

        @Bean(name = "lifecycleProcessor")
        public DefaultLifecycleProcessor lifecycleProcessor() {
            DefaultLifecycleProcessor processor = new DefaultLifecycleProcessor();
            processor.setTimeoutPerShutdownPhase(500);
            return processor;
        }

        @Bean
        public StuckLifecycle stuck() {
            return new StuckLifecycle();
        }

        @Bean
        public PhasedBean afterStuck() {
            return new PhasedBean("after-stuck", 0);
        }
    }

    // ---------------------------------------------------------------- 관찰용 빈

    static class ClosedEventRecorder implements ApplicationListener<ContextClosedEvent> {

        @Override
        public void onApplicationEvent(ContextClosedEvent event) {
            Timeline.record("① ContextClosedEvent 수신");
        }
    }

    /** phase 만 다른 SmartLifecycle. stop 이 불린 순서를 남긴다. */
    static class PhasedBean implements SmartLifecycle {

        private final String name;
        private final int phase;
        private volatile boolean running;

        PhasedBean(String name, int phase) {
            this.name = name;
            this.phase = phase;
        }

        @Override
        public void start() {
            running = true;
        }

        @Override
        public void stop() {
            Timeline.record("② stop phase=" + phase + " " + name);
            running = false;
        }

        @Override
        public boolean isRunning() {
            return running;
        }

        @Override
        public int getPhase() {
            return phase;
        }
    }

    static class DestroyRecorder implements DisposableBean {

        private final String name;

        DestroyRecorder(String name) {
            this.name = name;
        }

        @Override
        public void destroy() {
            Timeline.record("③ destroy " + name);
        }
    }

    static class DestroyCallbacksBean implements DisposableBean {

        @PreDestroy
        public void preDestroy() {
            Timeline.record("③ @PreDestroy");
        }

        @Override
        public void destroy() {
            Timeline.record("③ DisposableBean.destroy()");
        }

        public void customClose() {
            Timeline.record("③ destroyMethod(customClose)");
        }
    }

    static class SlowDestroyBean implements DisposableBean {

        private final String name;

        SlowDestroyBean(String name) {
            this.name = name;
        }

        @Override
        public void destroy() {
            Timeline.record("③ " + name + " destroy 시작");
            Tasks.sleepQuietly(300);
            Timeline.record("③ " + name + " destroy 끝");
        }
    }

    /** stop(callback) 을 받고도 callback 을 부르지 않는다. phase timeout 이 어떻게 동작하는지 보려는 빈. */
    static class StuckLifecycle implements SmartLifecycle {

        private volatile boolean running;

        @Override
        public void start() {
            running = true;
        }

        @Override
        public void stop() {
        }

        @Override
        public void stop(Runnable callback) {
            Timeline.record("② stuck(phase 100) stop 시작 — callback 을 부르지 않는다");
        }

        @Override
        public boolean isRunning() {
            return running;
        }

        @Override
        public int getPhase() {
            return 100;
        }
    }
}
