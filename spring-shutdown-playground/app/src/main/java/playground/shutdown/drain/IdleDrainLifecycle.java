package playground.shutdown.drain;

import org.springframework.context.SmartLifecycle;
import org.springframework.scheduling.concurrent.ThreadPoolTaskExecutor;
import playground.shutdown.timeline.Timeline;

import java.time.Duration;
import java.util.List;
import java.util.concurrent.ThreadPoolExecutor;

/**
 * 웹 서버·리스너가 멈춘 뒤, Redis(phase 0)가 멈추기 전에 풀을 비운다.
 * 접수는 닫지 않고, 모든 풀이 "실행 중 0 + 대기열 0" 으로 연속해서 관측될 때까지 기다린다.
 * 그래서 비우는 도중 넘어온 다음 작업(체인)도 받아서 끝낸 뒤에 다음 단계로 넘어간다.
 *
 * <p>접수를 닫는 건 그 뒤 destroy 단계의 몫이다.
 */
public class IdleDrainLifecycle implements SmartLifecycle {

    private static final Duration POLL_INTERVAL = Duration.ofMillis(20);

    /** 작업이 대기열에서 막 꺼내져 아직 실행 중으로 집계되기 전의 틈을 넘기려고 두 번 연속 확인한다. */
    private static final int REQUIRED_IDLE_CHECKS = 2;

    private final List<ThreadPoolTaskExecutor> pools;
    private final Duration timeout;
    private volatile boolean running;

    public IdleDrainLifecycle(List<ThreadPoolTaskExecutor> pools, Duration timeout) {
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
        return ShutdownFirstDrainLifecycle.PHASE;
    }

    @Override
    public void stop() {
        Timeline.record("② drain(idle 대기) 시작");
        long deadline = System.nanoTime() + timeout.toNanos();
        int idleStreak = 0;
        while (System.nanoTime() < deadline && idleStreak < REQUIRED_IDLE_CHECKS) {
            idleStreak = allIdle() ? idleStreak + 1 : 0;
            try {
                Thread.sleep(POLL_INTERVAL.toMillis());
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                break;
            }
        }
        Timeline.record(idleStreak >= REQUIRED_IDLE_CHECKS ? "② drain(idle 대기) 끝" : "② drain(idle 대기) 시간 초과");
        running = false;
    }

    private boolean allIdle() {
        return pools.stream().allMatch(pool -> {
            ThreadPoolExecutor executor = pool.getThreadPoolExecutor();
            return executor.getActiveCount() == 0 && executor.getQueue().isEmpty();
        });
    }
}
