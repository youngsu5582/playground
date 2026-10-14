package playground.shutdown.timeline;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.time.Duration;
import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;

/**
 * 종료 과정에서 일어난 일을 경과 시간·스레드와 함께 한 줄씩 남긴다.
 * 테스트는 {@link #events()} 의 순서로 판정하고, 사람은 콘솔에 찍힌 타임라인으로 읽는다.
 *
 * <p>이벤트 이름 앞의 기호는 종료 단계를 뜻한다.
 * ① ContextClosedEvent · ② Lifecycle stop · ③ Bean destroy · 들여쓴 줄은 풀 안의 작업.
 */
public final class Timeline {

    private static final Logger log = LoggerFactory.getLogger("timeline");
    private static final List<Entry> ENTRIES = new CopyOnWriteArrayList<>();
    private static volatile long startNanos = System.nanoTime();

    public record Entry(long elapsedMillis, String thread, String event) {
    }

    private Timeline() {
    }

    /** 테스트마다 새로 시작한다. 경과 시간은 이 시점부터 잰다. */
    public static void reset() {
        ENTRIES.clear();
        startNanos = System.nanoTime();
    }

    public static void record(String event) {
        long elapsed = (System.nanoTime() - startNanos) / 1_000_000;
        String thread = Thread.currentThread().getName();
        ENTRIES.add(new Entry(elapsed, thread, event));
        log.info(String.format("[%5dms] [%-14s] %s", elapsed, thread, event));
    }

    public static List<String> events() {
        return ENTRIES.stream().map(Entry::event).toList();
    }

    public static boolean contains(String prefix) {
        return ENTRIES.stream().anyMatch(entry -> entry.event().startsWith(prefix));
    }

    /** prefix 로 시작하는 첫 이벤트. 없으면 예외. */
    public static Entry first(String prefix) {
        return ENTRIES.stream()
                .filter(entry -> entry.event().startsWith(prefix))
                .findFirst()
                .orElseThrow(() -> new IllegalStateException("타임라인에 없다: " + prefix + "\n" + String.join("\n", events())));
    }

    /** prefix 로 시작하는 첫 이벤트의 순서. 없으면 -1. */
    public static int indexOf(String prefix) {
        List<String> events = events();
        for (int i = 0; i < events.size(); i++) {
            if (events.get(i).startsWith(prefix)) {
                return i;
            }
        }
        return -1;
    }

    /** prefix 로 시작하는 이벤트가 기록될 때까지 기다린다. 풀 안의 작업이 "종료가 이 단계까지 왔다" 를 알아내는 데 쓴다. */
    public static void awaitEvent(String prefix, Duration timeout) throws InterruptedException {
        long deadline = System.nanoTime() + timeout.toNanos();
        while (!contains(prefix)) {
            if (System.nanoTime() > deadline) {
                throw new IllegalStateException("이벤트가 오지 않았다: " + prefix);
            }
            Thread.sleep(2);
        }
    }
}
