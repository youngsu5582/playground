package deepdive.testkit;

import java.util.ArrayList;
import java.util.List;

/**
 * 세션 A/B 가 무엇을 언제 했는지 찍는 타임라인.
 *
 * <p>줄을 바로 찍지 않고 <b>테스트가 끝날 때까지 모아 뒀다가</b> {@link TimelineExtension} 이 한 번에 찍는다.
 * 예측 테스트에서 예측이 "?" 그대로면({@link Predict#확인}) 타임라인을 숨긴다 —
 * 타임라인의 {@code → 50} 같은 결과가 곧 정답이기 때문이다. 예측을 적으면 맞든 틀리든 보여 준다.
 */
public final class Timeline {

    private static final String HIDDEN_NOTICE = "  (타임라인 숨김 — 예측을 적고 다시 돌리면 보인다)";

    private record Line(String text, boolean header) {}

    private static final List<Line> buffer = new ArrayList<>();
    private static volatile long t0 = System.nanoTime();
    private static boolean hidden;

    private Timeline() {}

    /** 장면 시작 — 시계를 0 으로 돌리고 제목 줄을 남긴다. */
    public static void reset(String scenario) {
        t0 = System.nanoTime();
        add("", true);
        add("── " + scenario + " " + "─".repeat(Math.max(4, 70 - scenario.length())), true);
    }

    /** 세션 문장이 아닌 설명 한 줄 (※). */
    public static void note(String text) {
        add("[%6s]    ※ %s".formatted(elapsed(), text), false);
    }

    /** 접두어 없이 한 줄 그대로 (측정 표처럼 줄 맞춤이 필요한 출력). {@code System.out} 대신 이걸 써야 순서가 맞는다. */
    public static void raw(String line) {
        add(line, false);
    }

    static void log(String session, String sql, String result) {
        String oneLine = sql.replaceAll("\\s+", " ").trim();
        add("[%6s] %-2s %-58s %s".formatted(elapsed(), session, abbreviate(oneLine, 58), result), false);
    }

    /** 이번 테스트의 타임라인을 숨긴다 — 아직 예측을 적지 않았다. */
    static synchronized void hide() {
        hidden = true;
    }

    /** 모아 둔 줄을 찍고 비운다. 숨김이면 장면 제목만 찍는다. 테스트가 끝날 때 {@link TimelineExtension} 이 부른다. */
    static synchronized void flush() {
        boolean anyHeader = false;
        for (Line line : buffer) {
            if (!hidden || line.header()) {
                System.out.println(line.text());
                anyHeader |= line.header();
            }
        }
        if (hidden && anyHeader) {
            System.out.println(HIDDEN_NOTICE);
        }
        buffer.clear();
        hidden = false;
    }

    // 비동기 세션(워커 스레드)도 여기로 쓴다 → 동기화.
    private static synchronized void add(String text, boolean header) {
        buffer.add(new Line(text, header));
    }

    private static String elapsed() {
        return "+" + (System.nanoTime() - t0) / 1_000_000 + "ms";
    }

    private static String abbreviate(String s, int max) {
        return s.length() <= max ? s : s.substring(0, max - 1) + "…";
    }
}
