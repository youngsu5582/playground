package playground.shutdown.resource;

import org.springframework.beans.factory.DisposableBean;
import org.springframework.context.SmartLifecycle;
import playground.shutdown.timeline.Timeline;

/**
 * Rabbit CachingConnectionFactory 의 종료 동작만 흉내 낸다 (spring-rabbit 3.x).
 * SmartLifecycle phase MIN_VALUE 에서 연결을 끊지만, 다음 요청이 오면 다시 연결한다.
 * 연결을 거부하기 시작하는 건 자기 destroy 이후부터다.
 */
public class FakeMqConnectionFactory implements SmartLifecycle, DisposableBean {

    private volatile boolean running;
    private volatile boolean connected;
    private volatile boolean destroyed;

    @Override
    public void start() {
        running = true;
        connected = true;
    }

    @Override
    public void stop() {
        Timeline.record("② mq(phase MIN) stop → 연결 끊음, 다음 요청 때 재연결");
        connected = false;
        running = false;
    }

    @Override
    public boolean isRunning() {
        return running;
    }

    @Override
    public int getPhase() {
        return Integer.MIN_VALUE;
    }

    @Override
    public void destroy() {
        Timeline.record("③ mq destroy → 이후 연결 거부");
        destroyed = true;
    }

    public String publish(String message) {
        if (destroyed) {
            throw new IllegalStateException("FakeMqConnectionFactory: the ConnectionFactory can no longer create connections");
        }
        if (!connected) {
            connected = true;
            Timeline.record("  mq 재연결");
        }
        return "published:" + message;
    }
}
