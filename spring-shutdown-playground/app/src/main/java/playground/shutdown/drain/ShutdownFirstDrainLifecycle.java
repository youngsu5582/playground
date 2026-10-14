package playground.shutdown.drain;

import org.springframework.context.SmartLifecycle;
import org.springframework.scheduling.concurrent.ExecutorConfigurationSupport;
import org.springframework.scheduling.concurrent.ThreadPoolTaskExecutor;
import playground.shutdown.timeline.Timeline;

import java.time.Duration;
import java.util.List;
import java.util.concurrent.TimeUnit;

/**
 * 웹 서버·리스너가 멈춘 뒤, Redis(phase 0)가 멈추기 전에 풀을 비운다.
 * 접수를 먼저 닫고 하나의 마감 시각까지 함께 기다린다.
 *
 * <p>약점: 비우는 도중 풀 안의 작업이 같은 풀에 다음 작업을 넘기면 거절된다 (stage4).
 */
public class ShutdownFirstDrainLifecycle implements SmartLifecycle {

    /**
     * 웹 서버(MAX−2048) 뒤, LettuceConnectionFactory(phase 0) 앞.
     * 다만 풀 빈을 참조해 풀에 의존하는 빈이 되므로, 실제로는 첫 풀이 멈추기 직전에 먼저 불린다 (docs/05).
     */
    public static final int PHASE = ExecutorConfigurationSupport.DEFAULT_PHASE - 1;

    private final List<ThreadPoolTaskExecutor> pools;
    private final Duration timeout;
    private volatile boolean running;

    public ShutdownFirstDrainLifecycle(List<ThreadPoolTaskExecutor> pools, Duration timeout) {
        this.pools = pools;
        this.timeout = timeout;
    }

    @Override
    public void start() {
        running = true;
    }

    @Override
    public boolean isRunning() {
        return running;
    }

    @Override
    public int getPhase() {
        return PHASE;
    }

    @Override
    public void stop() {
        // ThreadPoolTaskExecutor.shutdown() 은 awaitTerminationMillis 만큼 풀마다 막히므로 JDK 풀을 직접 닫는다
        pools.forEach(pool -> pool.getThreadPoolExecutor().shutdown());
        Timeline.record("② drain(shutdown 먼저) 접수 마감, 대기 시작");
        long deadline = System.nanoTime() + timeout.toNanos();
        boolean allTerminated = true;
        for (ThreadPoolTaskExecutor pool : pools) {
            boolean terminated = awaitUntil(pool, deadline);   // 앞 풀이 실패해도 뒤 풀은 기다린다
            allTerminated = allTerminated && terminated;
        }
        Timeline.record(allTerminated ? "② drain(shutdown 먼저) 끝" : "② drain(shutdown 먼저) 시간 초과");
        running = false;
    }

    private boolean awaitUntil(ThreadPoolTaskExecutor pool, long deadline) {
        try {
            long remaining = Math.max(deadline - System.nanoTime(), 0);
            return pool.getThreadPoolExecutor().awaitTermination(remaining, TimeUnit.NANOSECONDS);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            return false;
        }
    }
}
