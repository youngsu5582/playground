package playground.shutdown.support;

/**
 * 종료 단계. 타임라인 이벤트 앞의 ①②③ 기호와 같다.
 *
 * <pre>
 * close()
 *  ① CONTEXT_CLOSED_EVENT → ② LIFECYCLE_STOP → ③ BEAN_DESTROY   (세 단계는 겹치지 않는다)
 * </pre>
 */
public enum Stage {

    /** close() 를 부르기 전. 종료가 아직 시작되지 않았다. */
    BEFORE_SHUTDOWN("종료 전"),

    /**
     * ① ContextClosedEvent 를 리스너에게 알린다.
     * 알림일 뿐이라 이 단계에서는 아무것도 멈추지 않는다.
     */
    CONTEXT_CLOSED_EVENT("①"),

    /**
     * ② SmartLifecycle 의 stop() 을 phase 가 큰 빈부터 부른다.
     * 같은 phase 의 빈은 한 묶음으로 stop(callback) 을 받고, 묶음 전체의 callback 이 오거나 timeout(이 실험장은 1초)이 지나면 다음 phase 로 넘어간다.
     * 같은 묶음 안에서는 다른 빈에 의존하는 빈을 먼저 멈춘다.
     */
    LIFECYCLE_STOP("②"),

    /**
     * ③ @PreDestroy · DisposableBean.destroy() · close() 를 부른다. 다른 빈에 의존하는 빈이 먼저, 그 외에는 빈을 만든 역순이다.
     * close() 를 부른 스레드 하나가 하나씩 처리하므로, 앞 빈의 destroy 가 끝나야 다음 빈으로 넘어간다.
     */
    BEAN_DESTROY("③");

    private final String symbol;

    Stage(String symbol) {
        this.symbol = symbol;
    }

    /** 타임라인 이벤트 앞에 붙는 기호. */
    public String symbol() {
        return symbol;
    }

    static Stage fromSymbol(String symbol) {
        for (Stage stage : values()) {
            if (stage.symbol.equals(symbol)) {
                return stage;
            }
        }
        throw new IllegalArgumentException("모르는 단계 기호: " + symbol);
    }
}
