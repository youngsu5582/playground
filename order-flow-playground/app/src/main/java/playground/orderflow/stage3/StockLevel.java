package playground.orderflow.stage3;

/**
 * 한 SKU 의 재고 스냅샷.
 *
 * <p>재고를 <b>숫자 하나로 두지 않는다</b>는 것이 이 스테이지의 첫 번째 설계 결정이다.
 * <pre>
 *   available : 지금 새 주문이 잡을 수 있는 수량
 *   reserved  : 주문이 잡아뒀지만 아직 출고되지 않은 수량
 * </pre>
 *
 * <p>왜 나누는가 — 결제는 끝났는데 아직 창고에서 물건이 안 나갔을 때,
 * 그 물건은 "있지만 팔 수 없는" 상태다. 숫자 하나로 관리하면
 * (a) 미리 빼서 취소 시 복구를 잊거나, (b) 안 빼서 초과 판매가 난다.
 *
 * <p>{@code onHand = available + reserved} 는 어떤 연산 후에도 깨지면 안 되는 불변식이다.
 * 이 불변식을 테스트에서 매번 확인하는 습관이 stage3 의 핵심이다.
 */
public record StockLevel(String sku, int available, int reserved) {

    public StockLevel {
        if (available < 0 || reserved < 0) {
            throw new IllegalArgumentException(
                    "재고는 음수가 될 수 없습니다: available=%d reserved=%d".formatted(available, reserved));
        }
    }

    /** 물리적으로 창고에 있는 총량. */
    public int onHand() {
        return available + reserved;
    }
}
