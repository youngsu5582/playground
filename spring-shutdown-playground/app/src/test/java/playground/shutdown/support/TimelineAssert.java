package playground.shutdown.support;

import playground.shutdown.timeline.Timeline;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.fail;

/** 타임라인 판정 도구. 이벤트는 앞부분(prefix)으로 찾는다. */
public final class TimelineAssert {

    private TimelineAssert() {
    }

    /** 주어진 이벤트들이 모두 있고, 이 순서대로 일어났다. */
    public static void inOrder(String... prefixes) {
        int previous = -1;
        for (String prefix : prefixes) {
            int index = Timeline.indexOf(prefix);
            if (index < 0) {
                fail("타임라인에 없다: [%s]%n%s", prefix, dump());
            }
            if (index <= previous) {
                fail("순서가 다르다: [%s] 가 앞 이벤트보다 먼저 일어났다%n%s", prefix, dump());
            }
            previous = index;
        }
    }

    public static void happened(String prefix) {
        assertThat(Timeline.contains(prefix)).as("일어났어야 한다: [%s]%n%s", prefix, dump()).isTrue();
    }

    public static void neverHappened(String prefix) {
        assertThat(Timeline.contains(prefix)).as("일어나지 말았어야 한다: [%s]%n%s", prefix, dump()).isFalse();
    }

    /** from 이벤트에서 to 이벤트까지 걸린 시간(ms). */
    public static long millisBetween(String from, String to) {
        return Timeline.first(to).elapsedMillis() - Timeline.first(from).elapsedMillis();
    }

    private static String dump() {
        return String.join(System.lineSeparator(), Timeline.events());
    }
}
