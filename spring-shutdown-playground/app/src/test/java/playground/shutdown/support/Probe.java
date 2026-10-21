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

    /**
     * waitForEvent 가 타임라인에 찍힐 때까지 기다린 뒤, 200ms 후 Redis·MQ·DB 를 한 번씩 호출하는 작업을 만든다.
     * 여기서는 Runnable 만 만들고, 실제 실행은 Tasks.submit 으로 풀에 제출할 때 시작한다.
     * 각 호출의 성공/실패는 Tasks.attempt 가 기록한다. 이벤트 대기 중 interrupt 되면 자원 호출 없이 끝난다.
     */
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
            // 실제 작업처럼 시간이 걸린다. 누군가 기다려 주지 않으면 그사이 Redis 가 멈춘다
            Tasks.sleepQuietly(200);
            Tasks.attempt("redis", () -> redis.get("k"));
            Tasks.attempt("mq", () -> mq.publish("m"));
            Tasks.attempt("db", db::query);
            Timeline.record("  probe 끝");
        };
    }
}
