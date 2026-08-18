package playground.orderflow.stage1;

/**
 * 주문 생명주기 상태.
 *
 * <p>정상 흐름:
 * <pre>
 *   CREATED → PAID → ALLOCATED → SHIPPED → DELIVERED
 * </pre>
 *
 * <p>취소 가능 구간: CREATED / PAID / ALLOCATED (출고 전까지)
 * <p>종료 상태(terminal): DELIVERED, CANCELLED — 여기서 나가는 전이는 없다.
 */
public enum OrderStatus {

    /** 주문이 만들어졌으나 아직 결제 전 */
    CREATED,

    /** 결제 완료. 아직 재고를 잡지는 않았다 */
    PAID,

    /** 재고 예약 완료. 창고에 작업이 생성된 상태 */
    ALLOCATED,

    /** 출고되어 배송사에 인계됨 */
    SHIPPED,

    /** 수취 완료 (종료) */
    DELIVERED,

    /** 취소됨 (종료) */
    CANCELLED,
    ;

    /**
     * 종료 상태인지 여부.
     *
     * <p>TODO(stage1): 구현. 종료 상태를 여기 한 곳에서만 정의해야
     * 나중에 REFUNDED 같은 상태가 늘어날 때 분기 누락이 안 생긴다.
     */
    public boolean isTerminal() {
        throw new UnsupportedOperationException("TODO: stage1");
    }
}
