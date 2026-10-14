package playground.shutdown.support;

import org.springframework.beans.factory.DisposableBean;
import playground.shutdown.timeline.Timeline;

/** 가장 나중에 만들어져 가장 먼저 destroy 된다. 타임라인에서 "③ 단계가 시작됐다" 를 알리는 표지다. */
public class DestroyMarker implements DisposableBean {

    public static final String EVENT = "③ destroy 단계 시작 (marker)";

    @Override
    public void destroy() {
        Timeline.record(EVENT);
    }
}
