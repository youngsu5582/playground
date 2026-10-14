package playground.shutdown.resource;

import playground.shutdown.timeline.Timeline;

/**
 * HikariDataSource 의 종료 동작만 흉내 낸다.
 * Lifecycle 을 구현하지 않아 ② 에서는 아무 일도 없고, ③ destroy 에서 close() 로만 닫힌다.
 * (Spring 은 @Bean 의 AutoCloseable 을 destroy 때 close() 로 닫는다.)
 */
public class FakeDataSource implements AutoCloseable {

    private volatile boolean closed;

    public int query() {
        if (closed) {
            throw new IllegalStateException("FakeDataSource has been closed");
        }
        return 1;
    }

    @Override
    public void close() {
        Timeline.record("③ db close");
        closed = true;
    }
}
