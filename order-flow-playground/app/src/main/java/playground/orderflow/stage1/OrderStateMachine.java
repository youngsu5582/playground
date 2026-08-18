package playground.orderflow.stage1;

/**
 * 주문 상태 전이 규칙의 단일 소유자.
 *
 * <p>이 클래스가 존재하는 이유: 전이 규칙이 서비스 코드 곳곳의 {@code if} 문으로
 * 흩어지면, 새 상태가 하나 늘 때 어디를 고쳐야 하는지 아무도 모르게 된다.
 * 규칙을 한 곳(데이터)으로 모으고, 서비스는 이 클래스에 묻기만 한다.
 *
 * <p><b>구현 힌트</b> — 전이표를 코드가 아니라 <b>데이터</b>로 표현해라.
 * {@code EnumMap<OrderStatus, Set<OrderStatus>>} 또는 enum 자체에 다음 상태를
 * 들려주는 방식. if-else 체인으로 짜면 동작은 하지만, 후속 질문
 * ("상태가 3개 늘면?", "전이표를 설정으로 빼려면?")에서 막힌다.
 */
public class OrderStateMachine {

    /**
     * {@code current} 에서 {@code next} 로 가는 전이가 허용되는가.
     *
     * <p>규칙:
     * <ul>
     *   <li>CREATED   → PAID, CANCELLED</li>
     *   <li>PAID      → ALLOCATED, CANCELLED</li>
     *   <li>ALLOCATED → SHIPPED, CANCELLED</li>
     *   <li>SHIPPED   → DELIVERED</li>
     *   <li>DELIVERED → (없음)</li>
     *   <li>CANCELLED → (없음)</li>
     * </ul>
     *
     * <p>경계 조건 — 테스트가 이걸 못 박는다:
     * <ul>
     *   <li>null 인자는 {@link IllegalArgumentException}</li>
     *   <li>같은 상태로의 전이(self-transition)는 <b>false</b>.
     *       "이미 그 상태다" 와 "전이했다" 는 다른 사건이다.
     *       중복 요청 처리는 stage2 의 멱등성이 맡는다.</li>
     * </ul>
     *
     * <p>TODO(stage1): 구현.
     */
    public boolean canTransition(OrderStatus current, OrderStatus next) {
        throw new UnsupportedOperationException("TODO: stage1");
    }

    /**
     * 전이를 적용하고 새 상태를 돌려준다. 불가능한 전이면
     * {@link IllegalStateTransitionException} 을 던진다.
     *
     * <p>왜 boolean 반환 메서드와 따로 두는가:
     * 호출부가 "물어보고 나서 적용" 하는 2단계를 잊으면 규칙이 새어나간다.
     * 적용 경로를 하나로 강제하는 것이 목적이다.
     *
     * <p>TODO(stage1): 구현.
     */
    public OrderStatus transition(OrderStatus current, OrderStatus next) {
        throw new UnsupportedOperationException("TODO: stage1");
    }
}
