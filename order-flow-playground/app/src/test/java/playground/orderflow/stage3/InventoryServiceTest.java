package playground.orderflow.stage3;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Disabled;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import playground.orderflow.ConcurrencyHarness;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * stage3 — 초과 예약 0건 만들기.
 *
 * <p>가장 중요한 테스트는 {@link #재고_10개에_50명이_동시에_달려들어도_10명만_성공한다()} 하나다.
 * 나머지는 그 테스트가 의미를 갖게 해주는 받침대다.
 *
 * <p><b>권장 진행</b>: 단일 스레드 테스트를 먼저 초록으로 만든 뒤,
 * 동시성 테스트를 켠다. 그리고 <b>일부러 락 없는 구현으로 한 번 깨뜨려 본다.</b>
 * 깨지는 걸 눈으로 봐야 "왜 락이 필요한가" 를 자기 말로 설명할 수 있다.
 */
class InventoryServiceTest {

    private InventoryService sut;

    @BeforeEach
    void setUp() {
        sut = new InventoryService();
    }

    /** 어떤 연산 뒤에도 깨지면 안 되는 불변식. 모든 테스트 끝에 호출하는 습관을 들인다. */
    private void assertInvariant(String sku, int expectedOnHand) {
        StockLevel stock = sut.stockOf(sku);
        assertThat(stock.onHand())
                .as("onHand = available + reserved 불변식")
                .isEqualTo(expectedOnHand);
        assertThat(stock.available()).isNotNegative();
        assertThat(stock.reserved()).isNotNegative();
    }

    @Test
    @DisplayName("[명세 견본] 재고 10개에서 3개 예약하면 available 7 / reserved 3")
    void 예약하면_available_이_줄고_reserved_가_는다() {
        sut.register("SKU-A", 10);

        boolean reserved = sut.reserve("SKU-A", 3);

        assertThat(reserved).isTrue();
        assertThat(sut.stockOf("SKU-A").available()).isEqualTo(7);
        assertThat(sut.stockOf("SKU-A").reserved()).isEqualTo(3);
        assertInvariant("SKU-A", 10); // 물건은 아직 창고에 그대로 있다
    }

    @Test
    @Disabled("TODO: stage3 — 직접 작성")
    @DisplayName("재고보다 많이 예약하면 false 이고 상태는 전혀 바뀌지 않는다")
    void 재고_부족이면_아무것도_바뀌지_않는다() {
        // 부분 예약이 없다는 걸 못 박는 테스트다.
        // 실패 후 available/reserved 를 둘 다 확인해야 의미가 있다.
    }

    @Test
    @Disabled("TODO: stage3 — 직접 작성")
    @DisplayName("예약 → 해제하면 원래 재고로 돌아온다")
    void 해제는_예약을_되돌린다() {
    }

    @Test
    @Disabled("TODO: stage3 — 직접 작성")
    @DisplayName("예약 → 출고 확정하면 reserved 만 줄고 available 은 그대로 (물건이 나갔다)")
    void 출고_확정은_available_로_돌려주지_않는다() {
        // 여기서 onHand 가 줄어든다. release 와의 차이를 숫자로 확인해라.
    }

    @Test
    @Disabled("TODO: stage3 — 직접 작성")
    @DisplayName("예약하지 않은 수량을 해제하면 IllegalStateException — 없던 재고가 생기면 안 된다")
    void 과다_해제는_거부한다() {
    }

    @Test
    @Disabled("TODO: stage3 — 직접 작성")
    @DisplayName("수량 0 또는 음수 예약은 IllegalArgumentException")
    void 잘못된_수량은_거부한다() {
        // 음수 예약을 허용하면 그게 곧 '재고 증가' 백도어가 된다.
    }

    @Test
    @Disabled("TODO: stage3 — 직접 작성")
    @DisplayName("등록되지 않은 SKU 는 UnknownSkuException")
    void 모르는_SKU_는_거부한다() {
    }

    // ------------------------------------------------------------------
    // 본 게임
    // ------------------------------------------------------------------

    @Test
    @Disabled("TODO: stage3 — 본 게임. 여기가 깨지는 걸 먼저 보고 고쳐라")
    @DisplayName("재고 10개에 50명이 동시에 1개씩 예약하면 정확히 10명만 성공한다")
    void 재고_10개에_50명이_동시에_달려들어도_10명만_성공한다() {
        // sut.register("SKU-A", 10);
        //
        // var outcome = ConcurrencyHarness.runConcurrently(50, () -> sut.reserve("SKU-A", 1));
        //
        // 검증 세 줄:
        //   - 성공(true) 개수가 정확히 10
        //   - stockOf().available() == 0
        //   - assertInvariant("SKU-A", 10)   ← 총량은 여전히 10
        //
        // 통과하면 ConcurrencyHarness.repeat(100, ...) 로 감싸서 다시.
        //
        // ★ 락 없는 구현으로 먼저 돌려봐라. successCount 가 10 을 넘는 순간을 보면
        //   "check-then-act 가 원자적이지 않다" 가 문장이 아니라 경험이 된다.
    }

    @Test
    @Disabled("TODO: stage3 — 여유 있으면")
    @DisplayName("서로 다른 SKU 에 대한 예약은 서로를 막지 않는다")
    void 다른_SKU_는_독립적으로_처리된다() {
        // 전역 synchronized 구현도 이 테스트는 '통과' 한다 (정확성은 맞으니까).
        // 처리량 차이는 단위 테스트로 증명하기 어렵다 —
        // 그래서 이건 코드로 증명하는 대신 '왜 SKU 단위 락이 필요한가' 를
        // 말로 설명할 수 있는지 확인하는 자리다. docs/03 Q3.
    }

    @Test
    @Disabled("TODO: stage3 — 여유 있으면")
    @DisplayName("예약과 해제가 동시에 뒤섞여도 총량 불변식은 유지된다")
    void 예약과_해제가_섞여도_총량은_유지된다() {
        // 예약 25 + 해제 25 를 섞어 던지고, 끝난 뒤 onHand 가 초기값과 같은지 본다.
        // 이런 '무작위 연산 후 불변식 확인' 이 property-based test 의 씨앗이다.
    }
}
