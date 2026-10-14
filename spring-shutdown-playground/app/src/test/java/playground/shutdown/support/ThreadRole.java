package playground.shutdown.support;

/** threadOf(event) 의 답. 그 이벤트를 남긴 스레드가 맡은 역할. */
public enum ThreadRole {

    /** 테스트에서 context.close() 를 부른 스레드 (Gradle 에서는 "Test worker"). 종료 단계를 차례로 진행시키는 스레드다. */
    CLOSING_THREAD,

    /** pool-a 의 작업 스레드 ("pool-a-1"). */
    POOL_A,

    /** pool-b 의 작업 스레드 ("pool-b-1"). */
    POOL_B,

    /** SIGTERM 을 받았을 때 JVM shutdown hook 이 close() 를 부르는 스레드 ("SpringContextShutdownHook"). */
    SHUTDOWN_HOOK,

    /** 위에 없는 스레드. */
    OTHER;

    static ThreadRole of(String threadName) {
        if (threadName.startsWith("pool-a-")) {
            return POOL_A;
        }
        if (threadName.startsWith("pool-b-")) {
            return POOL_B;
        }
        if (threadName.equals("SpringContextShutdownHook")) {
            return SHUTDOWN_HOOK;
        }
        if (threadName.equals("Test worker") || threadName.equals("main")) {
            return CLOSING_THREAD;
        }
        return OTHER;
    }
}
