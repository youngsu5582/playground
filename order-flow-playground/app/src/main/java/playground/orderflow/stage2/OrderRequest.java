package playground.orderflow.stage2;

import java.util.List;
import java.util.Objects;

/**
 * 주문 생성 요청 (클라이언트가 보내는 것).
 *
 * <p>record 라서 {@code equals} 가 값 비교로 공짜로 생긴다 —
 * "같은 멱등키인데 페이로드가 다르다" 를 판정할 때 이걸 쓴다.
 * 단, {@link List} 필드는 <b>순서가 다르면 다른 값</b>이 된다.
 * 그게 맞는 정책인지는 stage2 확장 질문에서 다룬다.
 */
public record OrderRequest(String customerId, List<OrderLine> lines) {

    public OrderRequest {
        Objects.requireNonNull(customerId, "customerId");
        Objects.requireNonNull(lines, "lines");
        lines = List.copyOf(lines); // 방어적 복사 — 호출자가 나중에 바꿔도 저장된 요청은 불변
    }

    public record OrderLine(String sku, int quantity) {
        public OrderLine {
            Objects.requireNonNull(sku, "sku");
            if (quantity <= 0) {
                throw new IllegalArgumentException("quantity must be positive: " + quantity);
            }
        }
    }
}
