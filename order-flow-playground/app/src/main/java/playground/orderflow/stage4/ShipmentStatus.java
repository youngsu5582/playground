package playground.orderflow.stage4;

/**
 * 배송 상태. 외부(배송사)가 알려주는 값이라 <b>우리가 순서를 통제할 수 없다.</b>
 *
 * <p>{@link #rank} 가 이 스테이지의 핵심 장치다 — 상태에 순위를 매겨두면
 * "이미 지나간 상태의 이벤트가 늦게 도착했다" 를 숫자 비교 한 줄로 판정할 수 있다.
 * enum 의 {@code ordinal()} 을 쓰지 않고 명시적 int 를 두는 이유:
 * 나중에 enum 상수 순서를 바꾸면 ordinal 이 조용히 달라진다.
 * 비즈니스 의미가 있는 순서를 ordinal 에 의존시키면 안 된다.
 *
 * <p>{@link #RETURNED} 에 999 를 준 것은 <b>의도적인 단순화</b>다.
 * 실제로는 반품이 배송 흐름의 연장이 아니라 별개 흐름이지만,
 * 60분 안에 다루려면 "가장 마지막" 으로 두는 편이 낫다.
 * 드릴에서 이 단순화를 <b>소리 내어 밝히는 것</b>까지가 포함이다.
 */
public enum ShipmentStatus {

    READY(10),
    SHIPPED(20),
    IN_TRANSIT(30),
    OUT_FOR_DELIVERY(40),
    DELIVERED(50),
    RETURNED(999),
    ;

    private final int rank;

    ShipmentStatus(int rank) {
        this.rank = rank;
    }

    /** 흐름상의 진행도. 클수록 나중 단계. */
    public int rank() {
        return rank;
    }
}
