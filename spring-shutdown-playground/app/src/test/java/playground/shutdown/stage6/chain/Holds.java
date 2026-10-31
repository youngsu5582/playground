package playground.shutdown.stage6.chain;

import playground.shutdown.timeline.Timeline;

import java.time.Duration;
import java.util.function.BooleanSupplier;

/**
 * 실서비스에서 "저장이 오래 걸린다" · "발행 전에 할 일이 남았다" 에 해당하는 자리.
 * 테스트가 정한 종료 시점까지 그 자리에서 기다려, 종료의 어느 순간에 커밋·발행이 일어나는지를 고정한다.
 *
 * @param beforeCommit  create 가 커밋하기 직전에 기다린다
 * @param beforeEnqueue produce 가 큐에 넣기 직전에 기다린다
 */
public record Holds(Hold beforeCommit, Hold beforeEnqueue) {

    private static final Duration WAIT = Duration.ofSeconds(5);

    public static Holds none() {
        return new Holds(Hold.NONE, Hold.NONE);
    }

    public static Holds beforeCommit(Hold hold) {
        return new Holds(hold, Hold.NONE);
    }

    public static Holds beforeEnqueue(Hold hold) {
        return new Holds(Hold.NONE, hold);
    }

    /** event 가 타임라인에 찍히고, condition 까지 참이 될 때까지 기다린다. */
    public record Hold(String event, BooleanSupplier condition) {

        static final Hold NONE = new Hold(null, () -> true);

        public static Hold until(String event) {
            return new Hold(event, () -> true);
        }

        public Hold and(BooleanSupplier next) {
            return new Hold(event, next);
        }

        void await() throws InterruptedException {
            if (event == null) {
                return;
            }
            Timeline.awaitEvent(event, WAIT);
            long deadline = System.nanoTime() + WAIT.toNanos();
            while (!condition.getAsBoolean() && System.nanoTime() < deadline) {
                Thread.sleep(1);
            }
        }
    }
}
