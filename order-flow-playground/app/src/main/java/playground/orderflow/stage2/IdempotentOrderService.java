package playground.orderflow.stage2;

import java.util.function.Supplier;

/**
 * 멱등키 기반 주문 생성.
 *
 * <p>다루는 사고 상황은 하나다 —
 * <b>클라이언트가 응답을 못 받았지만 서버는 이미 처리했다.</b>
 * 타임아웃, 커넥션 끊김, 프록시 재시도, 사용자 더블클릭 전부 같은 모양이다.
 * 이때 재시도가 두 번째 주문을 만들면 안 된다.
 *
 * <p><b>구현 힌트</b>
 * <ul>
 *   <li>저장할 것은 세 가지: 키 / 요청 지문(fingerprint) / 결과(orderId)</li>
 *   <li>요청 지문을 저장하지 않으면 "같은 키 다른 요청" 을 잡을 수 없다</li>
 *   <li>{@code ConcurrentHashMap#computeIfAbsent} 를 쓰면 단일 JVM 안에서
 *       키 단위 원자성이 공짜로 온다 — 다만 <b>왜 그것만으로 부족한지</b>를
 *       말할 수 있어야 한다 (docs/02 확장 질문)</li>
 * </ul>
 */
public class IdempotentOrderService {

    /**
     * 실제 주문 생성 로직. 테스트에서 호출 횟수를 세기 위해 주입받는다.
     * 이 supplier 가 <b>정확히 한 번만</b> 호출되게 만드는 것이 stage2 의 전부다.
     */
    private final Supplier<String> orderIdGenerator;

    public IdempotentOrderService(Supplier<String> orderIdGenerator) {
        this.orderIdGenerator = orderIdGenerator;
    }

    /**
     * 멱등한 주문 생성.
     *
     * <p>요구사항:
     * <ol>
     *   <li>처음 보는 키 → 주문 생성, {@code replayed=false}</li>
     *   <li>같은 키 + 같은 요청 → 기존 orderId 반환, {@code replayed=true},
     *       <b>생성 로직은 다시 실행되지 않는다</b></li>
     *   <li>같은 키 + 다른 요청 → {@link IdempotencyConflictException}</li>
     *   <li>키가 null 이거나 공백 → {@link IllegalArgumentException}</li>
     *   <li>동시에 같은 키로 N개 요청이 들어와도 생성은 정확히 1회</li>
     * </ol>
     *
     * <p>TODO(stage2): 구현.
     */
    public OrderResult create(String idempotencyKey, OrderRequest request) {
        throw new UnsupportedOperationException("TODO: stage2");
    }

    /**
     * 저장된 멱등 레코드 수. 테스트/관찰용.
     *
     * <p>이 값이 단조 증가만 한다는 것 자체가 stage2 확장 질문의 출발점이다
     * (메모리에 영원히 쌓이면? TTL 은 얼마?).
     *
     * <p>TODO(stage2): 구현.
     */
    public int recordCount() {
        throw new UnsupportedOperationException("TODO: stage2");
    }
}
