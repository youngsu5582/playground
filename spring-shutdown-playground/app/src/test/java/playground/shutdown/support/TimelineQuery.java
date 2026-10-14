package playground.shutdown.support;

import playground.shutdown.timeline.Timeline;

import java.util.List;

/**
 * 예측 질문에 쓰는 타임라인 조회. 답은 enum 으로 돌려준다 (보기와 설명은 각 enum 에 있다).
 *
 * <pre>
 * stageOf(event)        → Stage       그 이벤트가 어느 종료 단계 안에서 일어났나
 * order(a, b)           → Order       a 가 b 보다 먼저인가 나중인가
 * threadOf(event)       → ThreadRole  그 이벤트를 남긴 스레드의 역할
 * submit(name)          → Submission  풀에 작업을 넘긴 결과
 * result(name)          → Outcome     작업 안에서 자원을 써 본 결과
 * secondsBetween(a, b)  → long        두 이벤트 사이 시간 (반올림한 정수 초)
 * happened(event)       → boolean     그 이벤트가 일어났나
 * </pre>
 */
public final class TimelineQuery {

    private TimelineQuery() {
    }

    /** 그 이벤트가 어느 종료 단계 안에서 일어났나. 바로 앞의 ①②③ 이벤트로 판단한다. */
    public static Stage stageOf(String event) {
        List<String> events = Timeline.events();
        int index = Timeline.indexOf(event);
        if (index < 0) {
            throw new AssertionError("타임라인에 없다: " + event);
        }
        for (int i = index - 1; i >= 0; i--) {
            String previous = events.get(i);
            if (previous.startsWith("①") || previous.startsWith("②") || previous.startsWith("③")) {
                return Stage.fromSymbol(previous.substring(0, 1));
            }
        }
        return Stage.BEFORE_SHUTDOWN;
    }

    /** a 가 b 보다 먼저 일어났나 나중에 일어났나. */
    public static Order order(String a, String b) {
        int indexA = Timeline.indexOf(a);
        int indexB = Timeline.indexOf(b);
        if (indexA < 0 || indexB < 0) {
            throw new AssertionError("타임라인에 없다: " + (indexA < 0 ? a : b));
        }
        return indexA < indexB ? Order.BEFORE : Order.AFTER;
    }

    public static ThreadRole threadOf(String event) {
        return ThreadRole.of(Timeline.first(event).thread());
    }

    /** Tasks.submit(executor, name, …) 이 어떻게 됐나. */
    public static Submission submit(String name) {
        if (Timeline.contains("  submit " + name + " 거절됨")) {
            return Submission.REJECTED;
        }
        return Timeline.contains("  submit " + name) ? Submission.ACCEPTED : Submission.NOT_SUBMITTED;
    }

    /** Tasks.attempt(name, …) 가 어떻게 됐나. */
    public static Outcome result(String name) {
        if (Timeline.contains("  " + name + " → 성공")) {
            return Outcome.SUCCESS;
        }
        return Timeline.contains("  " + name + " → 실패") ? Outcome.FAILURE : Outcome.NOT_ATTEMPTED;
    }

    /** 두 이벤트 사이 시간. 초 단위로 반올림한다. */
    public static long secondsBetween(String from, String to) {
        return Math.round(TimelineAssert.millisBetween(from, to) / 1000.0);
    }

    public static boolean happened(String event) {
        return Timeline.contains(event);
    }
}
