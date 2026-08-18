package playground.orderflow.stage2;

import org.junit.jupiter.api.Disabled;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import playground.orderflow.ConcurrencyHarness;

import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * stage2 부터는 <b>테스트도 직접 쓴다.</b>
 *
 * <p>아래 메서드 이름이 곧 시나리오 목록이다. 하나씩 {@code @Disabled} 를 지우고
 * 몸통을 채워라. 견본이 필요하면 stage1 테스트의 4묶음 구조
 * (허용 / 거부 / 종료 / 경계) 를 그대로 가져다 쓴다.
 *
 * <p>순서 권장: 1 → 2 → 3 → 4 → 동시성. 동시성을 먼저 잡으려 하면 십중팔구 시간을 태운다.
 * 단일 스레드 규칙을 못 박은 다음에 스레드를 붙여야 실패 원인이 하나로 좁혀진다.
 */
class IdempotentOrderServiceTest {

    // 테스트마다 새 인스턴스 — 상태가 새면 그것부터 버그다
    private final ConcurrencyHarness.CallCounter generatorCalls = new ConcurrencyHarness.CallCounter();
    private final IdempotentOrderService sut =
            new IdempotentOrderService(() -> "ORDER-" + generatorCalls.increment());

    private static OrderRequest request(String customerId, String sku, int qty) {
        return new OrderRequest(customerId, List.of(new OrderRequest.OrderLine(sku, qty)));
    }

    @Test
    @DisplayName("[명세 견본] 처음 보는 키는 주문을 생성하고 replayed=false 다")
    void 처음_보는_키는_주문을_생성한다() {
        // 이 하나만 채워져 있다. 나머지는 이 모양을 따라 직접 쓴다.
        OrderResult result = sut.create("key-1", request("cust-1", "SKU-A", 2));

        assertThat(result.orderId()).isEqualTo("ORDER-1");
        assertThat(result.replayed()).isFalse();
        assertThat(generatorCalls.value()).isEqualTo(1);
        assertThat(sut.recordCount()).isEqualTo(1);
    }

    @Test
    @Disabled("TODO: stage2 — 직접 작성")
    @DisplayName("같은 키 + 같은 요청은 기존 주문을 replayed=true 로 돌려주고, 생성 로직은 다시 안 돈다")
    void 같은_키_같은_요청은_기존_결과를_재생한다() {
        // 검증 포인트 3개를 전부 확인해야 의미가 있다:
        //   (1) orderId 가 첫 결과와 같다
        //   (2) replayed 가 true
        //   (3) generatorCalls.value() 가 여전히 1  ← 이게 진짜 검증이다.
        //       (1),(2)만 보면 "매번 새로 만들고 같은 값을 우연히 반환" 하는 구현도 통과한다.
    }

    @Test
    @Disabled("TODO: stage2 — 직접 작성")
    @DisplayName("같은 키 + 다른 요청은 IdempotencyConflictException")
    void 같은_키_다른_요청은_충돌이다() {
        // 무엇을 '다르다' 로 볼지 먼저 정하고 시작해라:
        //   수량이 다르면? SKU 가 다르면? customerId 가 다르면?
        //   라인 순서만 다르면? (docs/02 확장 질문 Q2)
        // 정한 기준을 테스트 이름이나 주석에 남기는 것까지가 한 세트다.
    }

    @Test
    @Disabled("TODO: stage2 — 직접 작성")
    @DisplayName("멱등키가 null 이거나 공백이면 IllegalArgumentException")
    void 빈_멱등키는_거부한다() {
        // null / "" / "   " 세 가지. 공백 트림 정책도 여기서 결정된다.
    }

    @Test
    @Disabled("TODO: stage2 — 직접 작성")
    @DisplayName("서로 다른 키는 서로 독립적이다")
    void 다른_키는_각각_주문을_만든다() {
    }

    @Test
    @Disabled("TODO: stage2 — 직접 작성 (여기가 stage2 의 본 게임)")
    @DisplayName("같은 키로 50개 요청이 동시에 들어와도 주문 생성은 정확히 1회")
    void 동시_요청에도_생성은_한_번뿐이다() {
        // ConcurrencyHarness.runConcurrently(50, () -> sut.create("key-1", req)) 사용.
        //
        // 검증:
        //   - generatorCalls.value() == 1
        //   - 반환된 orderId 가 전부 동일 (successes 를 Set 으로 모아 size 1)
        //   - replayed=false 는 정확히 1건  ← 놓치기 쉬운 검증
        //
        // 통과했다면 ConcurrencyHarness.repeat(200, ...) 로 감싸서 다시 돌려라.
        // 한 번 초록은 증명이 아니다.
    }

    @Test
    @Disabled("TODO: stage2 — 여유 있으면")
    @DisplayName("생성 도중 예외가 나면 멱등 레코드가 남지 않는다 (다음 재시도가 다시 시도할 수 있어야 한다)")
    void 생성_실패는_키를_점유하지_않는다() {
        // 실패한 시도가 키를 붙잡고 있으면, 클라이언트는 영원히 같은 실패를 재생 받는다.
        // 실패를 캐싱할 것인가 말 것인가 — 정답은 실패의 종류에 따라 갈린다.
        // (재시도로 나아질 실패인가? / 몇 번을 해도 같은 실패인가?)
    }
}
