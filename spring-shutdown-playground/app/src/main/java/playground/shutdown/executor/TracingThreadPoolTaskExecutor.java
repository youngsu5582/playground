package playground.shutdown.executor;

import org.springframework.context.event.ContextClosedEvent;
import org.springframework.scheduling.concurrent.ThreadPoolTaskExecutor;
import playground.shutdown.timeline.Timeline;

/**
 * 동작은 ThreadPoolTaskExecutor 그대로이고, 종료 세 단계에서 불리는 순간만 타임라인에 남긴다.
 * 모든 메서드가 super 를 그대로 부르므로 결과는 원래 클래스와 같다.
 */
public class TracingThreadPoolTaskExecutor extends ThreadPoolTaskExecutor {

    private final String label;

    public TracingThreadPoolTaskExecutor(String label) {
        this.label = label;
        setThreadNamePrefix(label + "-");
    }

    public String label() {
        return label;
    }

    @Override
    public void onApplicationEvent(ContextClosedEvent event) {
        Timeline.record("① " + label + " 종료 이벤트 수신");
        super.onApplicationEvent(event);
    }

    @Override
    public void stop(Runnable callback) {
        Timeline.record("② " + label + " lifecycle stop 시작");
        super.stop(() -> {
            Timeline.record("② " + label + " lifecycle stop 완료");
            callback.run();
        });
    }

    @Override
    public void destroy() {
        Timeline.record("③ " + label + " destroy 시작");
        super.destroy();
        Timeline.record("③ " + label + " destroy 끝");
    }
}
