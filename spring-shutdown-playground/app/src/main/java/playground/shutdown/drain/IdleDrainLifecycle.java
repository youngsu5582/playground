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

        // TODO 직접 구현한다
        //   통과 기준: ./gradlew s3 --tests '*idleDrain'  ·  ./gradlew s4 --tests '*idleDrainRunsChainedTask'
        //              ./gradlew s5 --tests '*idleDrainWithRealLettuce'
        //
        //   1. 접수는 닫지 않는다. 비우는 도중 넘어오는 체인 작업도 받아야 한다 (T-08c).
        //   2. 모든 풀이 "실행 중 0 + 대기열 0" 인지 주기적으로 확인한다.
        //      힌트: pool.getThreadPoolExecutor().getActiveCount(), .getQueue().isEmpty()
        //   3. 한 번 비어 보였다고 바로 끝내면 안 되는 경우가 있다. 언제일까? (대기열에서 막 꺼낸 작업은 어떻게 집계될까)
        //   4. timeout 을 넘기면 포기하고 넘어간다. 그때는 아래 대신 "② drain(idle 대기) 시간 초과" 를 남긴다.
        //   5. 정답과 비교: ShutdownFirstDrainLifecycle 은 무엇을 먼저 하고, 그래서 T-08b 에서 무엇이 거절되나

        Timeline.record("② drain(idle 대기) 끝");
        running = false;
    }
}
