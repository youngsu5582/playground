package playground.orderflow.stage3;

/**
 * 재고 예약 / 해제 / 확정.
 *
 * <p>세 개의 동사가 각각 다른 사건에 대응한다:
 * <pre>
 *   reserve  주문 확정 시   available -= q,  reserved += q
 *   release  주문 취소 시   reserved  -= q,  available += q   (되돌리기)
 *   commit   출고 완료 시   reserved  -= q                     (창고에서 실제로 나감)
 * </pre>
 *
 * <p><b>이 스테이지가 노리는 것은 하나다 — 초과 예약(oversell) 0건.</b>
 * 단일 스레드로는 누구나 짤 수 있다. 스레드 50개가 재고 10개에 달려들 때
 * 정확히 10건만 성공하게 만드는 것이 본 게임이다.
 *
 * <p><b>구현 힌트 — 단계적으로 올라가라</b>
 * <ol>
 *   <li><b>1차</b>: {@code HashMap} + 단순 조건 검사. 동시성 테스트가 깨지는 걸 <b>직접 본다</b>.
 *       깨지는 걸 안 보고 넘어가면 왜 필요한지 설명할 수 없다.</li>
 *   <li><b>2차</b>: {@code synchronized} 로 통째로 잠근다. 통과한다. 그리고 물어라 —
 *       SKU 가 10만 개인데 전역 락이 맞나?</li>
 *   <li><b>3차</b>: SKU 단위로 락을 쪼갠다. {@code ConcurrentHashMap#compute} 가
 *       키 단위 원자 갱신을 준다 (= 세밀한 락을 직접 만들지 않아도 된다).</li>
 * </ol>
 * 1→2→3 을 실제로 밟아보는 것이 이 스테이지의 학습이다. 3부터 짜면 아무것도 안 남는다.
 */
public class InventoryService {

    /**
     * 초기 재고를 등록한다. (available=quantity, reserved=0)
     *
     * <p>TODO(stage3): 구현.
     */
    public void register(String sku, int quantity) {
        throw new UnsupportedOperationException("TODO: stage3");
    }

    /**
     * 재고 예약. 성공하면 true.
     *
     * <p>요구사항:
     * <ul>
     *   <li>available 이 부족하면 <b>false 를 반환하고 상태는 그대로</b> — 부분 예약 없음</li>
     *   <li>quantity 가 0 이하면 {@link IllegalArgumentException}</li>
     *   <li>등록되지 않은 SKU 는 {@link UnknownSkuException}</li>
     *   <li>동시 호출 시 available 총합을 초과해 성공하는 일이 없어야 한다</li>
     * </ul>
     *
     * <p>실패를 예외가 아니라 boolean 으로 돌려주는 이유: 재고 부족은 예외 상황이 아니라
     * <b>정상적인 비즈니스 결과</b>다. 하루에 수천 번 일어나는 일에 예외를 쓰면
     * 스택트레이스로 로그가 오염되고 성능도 잃는다.
     *
     * <p>TODO(stage3): 구현.
     */
    public boolean reserve(String sku, int quantity) {
        throw new UnsupportedOperationException("TODO: stage3");
    }

    /**
     * 예약 해제 (주문 취소). reserved → available 로 되돌린다.
     *
     * <p>예약한 적 없는 수량을 해제하려 하면 {@link IllegalStateException}.
     * — 조용히 넘어가면 <b>없던 재고가 생겨난다.</b> 재고가 늘어나는 버그는
     * 줄어드는 버그보다 발견이 늦고 손해가 크다.
     *
     * <p>TODO(stage3): 구현.
     */
    public void release(String sku, int quantity) {
        throw new UnsupportedOperationException("TODO: stage3");
    }

    /**
     * 출고 확정. reserved 에서 빼고 available 로 <b>돌려주지 않는다</b> (물건이 나갔다).
     *
     * <p>TODO(stage3): 구현.
     */
    public void commit(String sku, int quantity) {
        throw new UnsupportedOperationException("TODO: stage3");
    }

    /**
     * 현재 재고 스냅샷.
     *
     * <p>TODO(stage3): 구현.
     */
    public StockLevel stockOf(String sku) {
        throw new UnsupportedOperationException("TODO: stage3");
    }

    /** 등록되지 않은 SKU 접근. */
    public static class UnknownSkuException extends RuntimeException {
        public UnknownSkuException(String sku) {
            super("등록되지 않은 SKU: " + sku);
        }
    }
}
