package playground.shutdown.drain;

import org.springframework.context.SmartLifecycle;
import org.springframework.scheduling.concurrent.ThreadPoolTaskExecutor;
import playground.shutdown.timeline.Timeline;

import java.time.Duration;
import java.util.List;

/**
 * 웹 서버·리스너가 멈춘 뒤, Redis(phase 0)가 멈추기 전에 풀을 비운다.
 * 접수는 닫지 않고, 모든 풀이 "실행 중 0 + 대기열 0" 이 될 때까지 기다린다.
 * 그래서 비우는 도중 넘어온 다음 작업(체인)도 받아서 끝낸 뒤에 다음 단계로 넘어간다.
 *
 * <p>접수를 닫는 건 그 뒤 destroy 단계의 몫이다.
 * 비교용 완성본은 {@link ShutdownFirstDrainLifecycle} 이다 (접수를 먼저 닫아 체인 작업을 거절한다).
 */
public class IdleDrainLifecycle implements SmartLifecycle {

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
        boolean idleOnce = false;
        boolean drained = false;

        try {
            while (System.nanoTime() < deadline) {
                if (allIdle()) {
                    if (idleOnce) {
                        drained = true; // 연속 두 번째 idle 관측
                        break;
                    }
                    idleOnce = true;
                } else {
                    idleOnce = false;
                }

                Thread.sleep(10);
            }
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }

        Timeline.record(
                drained ? "② drain(idle 대기) 끝"
                        : "② drain(idle 대기) 시간 초과");
        running = false;
    }

    private boolean allIdle() {
        return pools.stream().allMatch(
                pool -> {
                    // 처리중인게 없고, 큐에 대기하는 요소도 없다.
                    var executor = pool.getThreadPoolExecutor();
                    return executor.getActiveCount() == 0 && executor.getQueue().isEmpty();
                }
        );
    }
}
