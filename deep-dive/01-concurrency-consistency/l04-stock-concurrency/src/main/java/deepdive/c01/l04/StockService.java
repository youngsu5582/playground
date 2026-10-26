package deepdive.c01.l04;

/**
 * 재고 차감 — 한 SKU 의 재고를 qty 개만큼 잡는다.
 *
 * <pre>
 * CREATE TABLE stock (sku text PRIMARY KEY, qty int NOT NULL, version int NOT NULL DEFAULT 0);
 * </pre>
 *
 * 세 구현이 같은 약속을 다른 방법으로 지킨다: {@link AtomicUpdateStockService} (조건부 UPDATE) ·
 * {@link OptimisticLockStockService} (version) · {@link PessimisticLockStockService} (FOR UPDATE).
 */
public interface StockService {

    /** @return 잡았으면 true, 재고가 모자라면 false (재고는 그대로). 재고가 있는데도 못 잡는 일은 없어야 한다 */
    boolean reserve(String sku, int qty);
}
