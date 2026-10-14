package playground.shutdown.demo;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.DependsOn;
import org.springframework.context.support.DefaultLifecycleProcessor;
import playground.shutdown.drain.IdleDrainLifecycle;
import playground.shutdown.executor.Pools;
import playground.shutdown.executor.TracingThreadPoolTaskExecutor;
import playground.shutdown.resource.FakeRedisConnectionFactory;

import java.time.Duration;
import java.util.List;

/** SigtermDemo 의 시나리오별 구성. 풀 하나 + 가짜 Redis 하나로 줄였다. */
final class DemoConfigs {

    private DemoConfigs() {
    }

    abstract static class Base {

        protected abstract Pools.Mode mode();

        protected Duration awaitTermination() {
            return Duration.ofSeconds(5);
        }

        @Bean(name = "lifecycleProcessor")
        public DefaultLifecycleProcessor lifecycleProcessor() {
            DefaultLifecycleProcessor processor = new DefaultLifecycleProcessor();
            processor.setTimeoutPerShutdownPhase(5000);
            return processor;
        }

        @Bean
        public FakeRedisConnectionFactory redis() {
            return new FakeRedisConnectionFactory();
        }

        @Bean
        @DependsOn("redis")
        public TracingThreadPoolTaskExecutor poolA() {
            return Pools.create("pool-a", mode(), awaitTermination());
        }
    }

    /** 설정 없음: ② MAX/2 에서 실행 중 작업을 기다려 준다. */
    @Configuration
    static class DefaultMode extends Base {
        @Override
        protected Pools.Mode mode() {
            return Pools.Mode.DEFAULT;
        }
    }

    /** PR 4341 설정: ③ destroy 에서 기다린다. 그사이 Redis 는 ② phase 0 에서 멈춘다. */
    @Configuration
    static class WaitForTasks extends Base {
        @Override
        protected Pools.Mode mode() {
            return Pools.Mode.WAIT_FOR_TASKS;
        }
    }

    /** PR 플래그 + IdleDrainLifecycle: Redis 가 멈추기 전에 풀을 비운다. */
    @Configuration
    static class IdleDrain extends Base {
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
            return new IdleDrainLifecycle(List.of(poolA()), Duration.ofSeconds(5));
        }
    }
}
