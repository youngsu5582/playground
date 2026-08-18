package playground.orderflow.stage1;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;
import org.junit.jupiter.params.provider.EnumSource;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatExceptionOfType;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static playground.orderflow.stage1.OrderStatus.*;

/**
 * stage1 테스트는 <b>유일하게 완성된 상태로 제공된다.</b>
 *
 * <p>목적 두 가지:
 * <ol>
 *   <li>구현의 명세 역할 — 이 테스트가 초록이면 stage1 은 끝이다.</li>
 *   <li><b>테스트를 어떻게 쪼개는지에 대한 견본</b> — stage2~5 는 테스트도 직접 써야 한다.
 *       "정상 / 거부 / 종료 / 경계" 네 묶음으로 나눈 이 구조를 그대로 베껴 써라.</li>
 * </ol>
 *
 * <p>드릴에서 던지는 말: "먼저 허용 전이표를 테스트로 못 박고 시작하겠습니다."
 * — 이 문장 하나가 구현 순서를 정당화한다.
 */
class OrderStateMachineTest {

    private final OrderStateMachine sut = new OrderStateMachine();

    @Nested
    @DisplayName("허용되는 전이")
    class Allowed {

        @ParameterizedTest(name = "{0} -> {1} 은 허용된다")
        @CsvSource({
                "CREATED,   PAID",
                "CREATED,   CANCELLED",
                "PAID,      ALLOCATED",
                "PAID,      CANCELLED",
                "ALLOCATED, SHIPPED",
                "ALLOCATED, CANCELLED",
                "SHIPPED,   DELIVERED",
        })
        void 허용_전이는_true_를_반환한다(OrderStatus from, OrderStatus to) {
            assertThat(sut.canTransition(from, to)).isTrue();
        }

        @Test
        void transition_은_다음_상태를_반환한다() {
            assertThat(sut.transition(CREATED, PAID)).isEqualTo(PAID);
        }

        @Test
        void 정상_흐름_전체를_통과한다() {
            OrderStatus status = CREATED;
            for (OrderStatus next : new OrderStatus[]{PAID, ALLOCATED, SHIPPED, DELIVERED}) {
                status = sut.transition(status, next);
            }
            assertThat(status).isEqualTo(DELIVERED);
        }
    }

    @Nested
    @DisplayName("거부되는 전이")
    class Rejected {

        @ParameterizedTest(name = "{0} -> {1} 은 거부된다")
        @CsvSource({
                // 단계 건너뛰기
                "CREATED,   ALLOCATED",
                "CREATED,   SHIPPED",
                "CREATED,   DELIVERED",
                "PAID,      SHIPPED",
                "PAID,      DELIVERED",
                "ALLOCATED, DELIVERED",
                // 역방향
                "PAID,      CREATED",
                "SHIPPED,   ALLOCATED",
                "DELIVERED, SHIPPED",
                // 출고 후 취소 — 취소가 아니라 '반품' 이라는 별개 흐름이어야 한다
                "SHIPPED,   CANCELLED",
                "DELIVERED, CANCELLED",
        })
        void 불가능한_전이는_false_를_반환한다(OrderStatus from, OrderStatus to) {
            assertThat(sut.canTransition(from, to)).isFalse();
        }

        @Test
        void transition_은_불가능한_전이에_예외를_던진다() {
            assertThatExceptionOfType(IllegalStateTransitionException.class)
                    .isThrownBy(() -> sut.transition(CREATED, DELIVERED))
                    .satisfies(e -> {
                        assertThat(e.from()).isEqualTo(CREATED);
                        assertThat(e.to()).isEqualTo(DELIVERED);
                    })
                    // 로그만 보고 원인을 알 수 있어야 한다
                    .withMessageContaining("CREATED")
                    .withMessageContaining("DELIVERED");
        }
    }

    @Nested
    @DisplayName("종료 상태")
    class Terminal {

        @ParameterizedTest
        @EnumSource(value = OrderStatus.class, names = {"DELIVERED", "CANCELLED"})
        void 종료_상태는_isTerminal_이_true(OrderStatus terminal) {
            assertThat(terminal.isTerminal()).isTrue();
        }

        @ParameterizedTest
        @EnumSource(value = OrderStatus.class, names = {"CREATED", "PAID", "ALLOCATED", "SHIPPED"})
        void 진행_상태는_isTerminal_이_false(OrderStatus inProgress) {
            assertThat(inProgress.isTerminal()).isFalse();
        }

        @ParameterizedTest
        @EnumSource(value = OrderStatus.class, names = {"DELIVERED", "CANCELLED"})
        void 종료_상태에서_나가는_전이는_전부_막힌다(OrderStatus terminal) {
            for (OrderStatus next : OrderStatus.values()) {
                assertThat(sut.canTransition(terminal, next))
                        .as("%s -> %s", terminal, next)
                        .isFalse();
            }
        }
    }

    @Nested
    @DisplayName("경계 조건")
    class EdgeCases {

        @ParameterizedTest
        @EnumSource(OrderStatus.class)
        void 같은_상태로의_전이는_허용하지_않는다(OrderStatus same) {
            // 의도적 선택이다. "이미 PAID 인데 PAID 요청이 또 왔다" 는
            // 상태 전이의 문제가 아니라 중복 요청의 문제 → stage2 멱등성이 담당.
            // 드릴에서는 이 결정을 소리 내어 말하고 넘어가는 게 핵심이다.
            assertThat(sut.canTransition(same, same)).isFalse();
        }

        @Test
        void null_인자는_IllegalArgumentException() {
            assertThatThrownBy(() -> sut.canTransition(null, PAID))
                    .isInstanceOf(IllegalArgumentException.class);
            assertThatThrownBy(() -> sut.canTransition(CREATED, null))
                    .isInstanceOf(IllegalArgumentException.class);
        }

        @Test
        void 모든_상태가_전이표에_등록되어_있다() {
            // 새 상태를 enum 에 추가하고 전이표에 안 넣으면 이 테스트가 깨진다.
            // "누락되면 조용히 통과" 를 막는 안전망 — 실무에서 값이 늘어나는 enum 에 꼭 하나 둔다.
            for (OrderStatus from : OrderStatus.values()) {
                for (OrderStatus to : OrderStatus.values()) {
                    sut.canTransition(from, to); // 예외 없이 판정만 되면 통과
                }
            }
        }
    }
}
