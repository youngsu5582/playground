package playground.shutdown.executor;

import java.time.Duration;

/**
 * 종료 설정만 다른 풀을 만든다. 스레드 1개 + 대기열 10칸이라, 두 번째 작업부터는 대기열에 쌓인다.
 */
public final class Pools {

    public enum Mode {
        /** 아무것도 설정하지 않음 (Spring 6.1.4+ 기본값). */
        DEFAULT,
        /** setStrictEarlyShutdown(true): 종료 이벤트 때 바로 접수를 닫는다. */
        STRICT_EARLY_SHUTDOWN,
        /** setWaitForTasksToCompleteOnShutdown(true) + setAwaitTerminationMillis: lifecycle 을 건너뛰고 destroy 에서 기다린다. */
        WAIT_FOR_TASKS
    }

    private Pools() {
    }

    public static TracingThreadPoolTaskExecutor create(String label, Mode mode, Duration awaitTermination) {
        TracingThreadPoolTaskExecutor executor = new TracingThreadPoolTaskExecutor(label);
        executor.setCorePoolSize(1);
        executor.setMaxPoolSize(1);
        executor.setQueueCapacity(10);
        switch (mode) {
            case STRICT_EARLY_SHUTDOWN -> executor.setStrictEarlyShutdown(true);
            case WAIT_FOR_TASKS -> {
                executor.setWaitForTasksToCompleteOnShutdown(true);
                executor.setAwaitTerminationMillis(awaitTermination.toMillis());
            }
            case DEFAULT -> {
            }
        }
        return executor;
    }

    public static TracingThreadPoolTaskExecutor create(String label, Mode mode) {
        return create(label, mode, Duration.ZERO);
    }
}
