package playground.shutdown.resource;

import org.springframework.beans.factory.DisposableBean;
import org.springframework.context.SmartLifecycle;
import playground.shutdown.timeline.Timeline;

/**
 * LettuceConnectionFactory 의 종료 동작만 흉내 낸다 (Spring Data Redis 3.2+).
 * SmartLifecycle phase 0 에서 멈추고, 멈춘 뒤에는 연결 요청을 거절한다.
 * 진짜 Lettuce 로 같은 결과가 나오는지는 stage5 가 확인한다.
 */
public class FakeRedisConnectionFactory implements SmartLifecycle, DisposableBean {

    private volatile String state = "CREATED";

    @Override
    public void start() {
        state = "STARTED";
    }

    @Override
    public void stop() {
        Timeline.record("② redis(phase 0) stop → 이후 연결 거절");
        state = "STOPPED";
    }

    @Override
    public boolean isRunning() {
        return "STARTED".equals(state);
    }

    @Override
    public int getPhase() {
        return 0;
    }

    @Override
    public void destroy() {
        Timeline.record("③ redis destroy");
        state = "DESTROYED";
    }

    /** Lettuce 의 getConnection() 처럼 STARTED 가 아니면 거절한다. */
    public String get(String key) {
        if (!"STARTED".equals(state)) {
            throw new IllegalStateException("FakeRedisConnectionFactory has been " + state);
        }
        return "value-of-" + key;
    }
}
