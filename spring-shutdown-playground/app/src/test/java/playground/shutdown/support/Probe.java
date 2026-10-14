package playground.shutdown.support;

import playground.shutdown.executor.Tasks;
import playground.shutdown.resource.FakeDataSource;
import playground.shutdown.resource.FakeMqConnectionFactory;
import playground.shutdown.resource.FakeRedisConnectionFactory;
import playground.shutdown.timeline.Timeline;

import java.time.Duration;

/**
 * 풀 안에서 "종료가 어느 단계까지 왔을 때" 자원을 써 보는 작업.
 * 회사 코드의 커밋 뒤 비동기 리스너가 캐시(Redis)·발행(MQ)·DB 를 쓰는 상황을 줄였다.
 */
public final class Probe {

    private Probe() {
    }

    /** waitForEvent 가 타임라인에 찍힐 때까지 기다렸다가 Redis·MQ·DB 를 한 번씩 쓴다. */
    public static Runnable afterEvent(String waitForEvent, FakeRedisConnectionFactory redis, FakeMqConnectionFactory mq, FakeDataSource db) {
        return () -> {
            Timeline.record("  probe 대기: [" + waitForEvent + "] 까지");
            try {
                Timeline.awaitEvent(waitForEvent, Duration.ofSeconds(5));
            } catch (InterruptedException e) {
                Timeline.record("  probe interrupt 됨");
                Thread.currentThread().interrupt();
                return;
            }
            Tasks.attempt("redis", () -> redis.get("k"));
            Tasks.attempt("mq", () -> mq.publish("m"));
            Tasks.attempt("db", db::query);
            Timeline.record("  probe 끝");
        };
    }
}
