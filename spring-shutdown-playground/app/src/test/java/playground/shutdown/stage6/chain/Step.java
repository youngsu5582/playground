package playground.shutdown.stage6.chain;

import playground.shutdown.timeline.Timeline;

import java.util.function.Supplier;

/**
 * 자원을 한 번 쓰고 성공·실패를 타임라인에 남긴다. {@code Tasks.attempt} 와 달리 예외를 삼키지 않고 다시 던진다 —
 * 실서비스 코드처럼 바깥 catch 가 실패를 받아야 하기 때문이다. 결과는 {@code result(name)} 으로 꺼낸다.
 */
final class Step {

    private Step() {
    }

    static <T> T run(String name, Supplier<T> call) {
        try {
            T value = call.get();
            Timeline.record("  " + name + " → 성공");
            return value;
        } catch (RuntimeException e) {
            Timeline.record("  " + name + " → 실패 " + e.getClass().getSimpleName() + ": " + e.getMessage());
            throw e;
        }
    }

    static void run(String name, Runnable call) {
        run(name, () -> {
            call.run();
            return null;
        });
    }
}
