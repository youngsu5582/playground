package playground.shutdown.support;

import playground.shutdown.timeline.Timeline;

import java.util.List;

/**
 * 예측 질문에 쓰는 타임라인 조회. 답이 짧은 말 하나로 나오도록 만들었다.
 *
 * <pre>
 * stageOf        → "종료 전" "①" "②" "③"
 * order          → "먼저" "나중"
 * secondsBetween → 정수 초 (반올림)
 * threadOf       → 스레드 이름 ("Test worker", "pool-a-1" …)
 * happened       → true / false
 * submit         → "접수" "거절" "없음"
 * result         → "성공" "실패" "없음"
 * </pre>
 */
public final class TimelineQuery {

    private TimelineQuery() {
    }

    /** 그 이벤트가 어느 종료 단계 안에서 일어났나. 바로 앞의 ①②③ 이벤트로 판단한다. */
    public static String stageOf(String prefix) {
        List<String> events = Timeline.events();
        int index = Timeline.indexOf(prefix);
        if (index < 0) {
            throw new AssertionError("타임라인에 없다: " + prefix);
        }
        for (int i = index - 1; i >= 0; i--) {
            String event = events.get(i);
            if (event.startsWith("①") || event.startsWith("②") || event.startsWith("③")) {
                return event.substring(0, 1);
            }
        }
        return "종료 전";
    }

    /** a 가 b 보다 "먼저" 일어났나 "나중" 에 일어났나. */
    public static String order(String a, String b) {
        int indexA = Timeline.indexOf(a);
        int indexB = Timeline.indexOf(b);
        if (indexA < 0 || indexB < 0) {
            throw new AssertionError("타임라인에 없다: " + (indexA < 0 ? a : b));
        }
        return indexA < indexB ? "먼저" : "나중";
    }

    /** 두 이벤트 사이 시간. 초 단위로 반올림한다. */
    public static long secondsBetween(String from, String to) {
        return Math.round(TimelineAssert.millisBetween(from, to) / 1000.0);
    }

    public static String threadOf(String prefix) {
        return Timeline.first(prefix).thread();
    }

    public static boolean happened(String prefix) {
        return Timeline.contains(prefix);
    }

    /** Tasks.submit(executor, name, …) 이 어떻게 됐나. */
    public static String submit(String name) {
        if (Timeline.contains("  submit " + name + " 거절됨")) {
            return "거절";
        }
        return Timeline.contains("  submit " + name) ? "접수" : "없음";
    }

    /** Tasks.attempt(name, …) 가 어떻게 됐나. 한 번도 시도하지 않았으면 "없음". */
    public static String result(String name) {
        if (Timeline.contains("  " + name + " → 성공")) {
            return "성공";
        }
        return Timeline.contains("  " + name + " → 실패") ? "실패" : "없음";
    }
}
