package playground.orderflow.stage1;

/**
 * 허용되지 않은 상태 전이 시도.
 *
 * <p>메시지에 from/to 를 반드시 남긴다 — 운영 중 이 예외가 로그에 찍혔을 때
 * "어떤 전이가 막혔는지" 가 없으면 원인 추적이 불가능하다.
 */
public class IllegalStateTransitionException extends RuntimeException {

    private final OrderStatus from;
    private final OrderStatus to;

    public IllegalStateTransitionException(OrderStatus from, OrderStatus to) {
        super("허용되지 않는 상태 전이: %s -> %s".formatted(from, to));
        this.from = from;
        this.to = to;
    }

    public OrderStatus from() {
        return from;
    }

    public OrderStatus to() {
        return to;
    }
}
