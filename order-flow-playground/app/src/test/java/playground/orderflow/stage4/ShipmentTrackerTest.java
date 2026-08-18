package playground.orderflow.stage4;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Disabled;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.time.Instant;
import java.util.concurrent.atomic.AtomicInteger;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * stage4 — 순서를 보장하지 않는 외부 이벤트 소비하기.
 *
 * <p>이 스테이지의 함정: <b>테스트를 "정상 순서" 로만 짜면 아무것도 검증하지 못한다.</b>
 * 이벤트를 일부러 뒤섞어 던지고, 어떤 순서로 던져도 최종 상태가 같은지를 봐야 한다.
 */
class ShipmentTrackerTest {

    private ShipmentTracker sut;
    private final AtomicInteger seq = new AtomicInteger();
    private static final Instant T0 = Instant.parse("2025-01-01T00:00:00Z");

    @BeforeEach
    void setUp() {
        sut = new ShipmentTracker();
        seq.set(0);
    }

    /** eventId 를 자동 부여하는 헬퍼. 중복을 만들고 싶을 때만 {@link #event(String, ShipmentStatus, long)} 를 쓴다. */
    private ShipmentEvent event(ShipmentStatus status, long secondsAfterT0) {
        return event("evt-" + seq.incrementAndGet(), status, secondsAfterT0);
    }

    private ShipmentEvent event(String eventId, ShipmentStatus status, long secondsAfterT0) {
        return new ShipmentEvent(eventId, "SHIP-1", status, T0.plusSeconds(secondsAfterT0));
    }

    @Test
    @DisplayName("[명세 견본] 정상 순서로 오면 전부 APPLIED 되고 최종 상태는 DELIVERED")
    void 정상_순서는_모두_반영된다() {
        assertThat(sut.apply(event(ShipmentStatus.READY, 0))).isEqualTo(ProcessResult.APPLIED);
        assertThat(sut.apply(event(ShipmentStatus.SHIPPED, 10))).isEqualTo(ProcessResult.APPLIED);
        assertThat(sut.apply(event(ShipmentStatus.IN_TRANSIT, 20))).isEqualTo(ProcessResult.APPLIED);
        assertThat(sut.apply(event(ShipmentStatus.DELIVERED, 30))).isEqualTo(ProcessResult.APPLIED);

        assertThat(sut.statusOf("SHIP-1")).contains(ShipmentStatus.DELIVERED);
        assertThat(sut.countOf(ProcessResult.APPLIED)).isEqualTo(4);
    }

    @Test
    @Disabled("TODO: stage4 — 직접 작성")
    @DisplayName("같은 eventId 가 다시 오면 DUPLICATE 이고 상태는 그대로")
    void 같은_이벤트ID_는_한_번만_처리된다() {
        // event("evt-dup", SHIPPED, 10) 을 두 번 던진다.
        // 두 번째 결과가 DUPLICATE, countOf(APPLIED) 는 여전히 1.
    }

    @Test
    @Disabled("TODO: stage4 — 직접 작성. 여기가 본 게임")
    @DisplayName("DELIVERED 이후 SHIPPED 가 늦게 도착해도 상태를 되돌리지 않는다")
    void 늦게_도착한_과거_이벤트는_STALE_이다() {
        // 배송 완료 알림을 받은 고객에게 '배송 중' 으로 되돌아간 화면을 보여주는 사고 —
        // 실제로 매우 흔하다. 이 테스트 하나가 그걸 막는다.
    }

    @Test
    @Disabled("TODO: stage4 — 직접 작성")
    @DisplayName("어떤 순서로 던져도 최종 상태는 같다 (순서 무관성)")
    void 도착_순서가_뒤섞여도_최종_상태는_동일하다() {
        // 같은 이벤트 4개를 (a) 정상 순서 (b) 역순 (c) 뒤죽박죽 으로 각각 새 tracker 에 던지고,
        // 세 경우의 statusOf() 가 전부 DELIVERED 인지 확인한다.
        //
        // 이 성질에 이름이 있다: 가환성(commutativity).
        // "재처리해도 안전하다" 는 말의 실질적인 의미가 이것이다.
    }

    @Test
    @Disabled("TODO: stage4 — 직접 작성")
    @DisplayName("같은 rank 의 다른 이벤트는 STALE (바꿀 게 없다)")
    void 동일_상태_재통지는_STALE_이다() {
        // eventId 는 다른데 상태가 같은 경우. 배송사가 같은 상태를 재통지하는 일은 흔하다.
        // DUPLICATE 가 아니라 STALE 로 라벨링하는 이유를 말할 수 있어야 한다.
    }

    @Test
    @Disabled("TODO: stage4 — 직접 작성")
    @DisplayName("DELIVERED 이후 RETURNED 를 제외한 전진 시도는 INVALID")
    void 종료_이후_전이는_INVALID_이다() {
        // INVALID 는 '알람 대상' 이다. DUPLICATE/STALE 과 다른 취급을 받는다는 걸
        // 카운터로 확인해라.
    }

    @Test
    @Disabled("TODO: stage4 — 직접 작성")
    @DisplayName("중간 단계를 건너뛴 이벤트는 허용한다 (READY → DELIVERED)")
    void 단계_건너뛰기는_허용한다() {
        // 외부 시스템이 우리 모델대로 이벤트를 보내줄 거라 가정하면 안 된다.
        // 여기서 INVALID 를 내면 정상 배송이 미완료로 남는다.
    }

    @Test
    @Disabled("TODO: stage4 — 직접 작성")
    @DisplayName("서로 다른 배송 건은 서로의 상태에 영향을 주지 않는다")
    void 배송_건별로_상태가_격리된다() {
        // shipmentId 를 파라미터로 받는 헬퍼가 필요해진다.
        // 이걸 깜빡하고 전역 상태 하나로 짜는 실수가 의외로 잦다.
    }

    @Test
    @Disabled("TODO: stage4 — 여유 있으면")
    @DisplayName("occurredAt 기준과 rank 기준이 충돌하면 어떻게 되는가")
    void 발생시각과_상태순위가_어긋나는_경우() {
        // 발생 시각은 더 최근인데 상태 rank 는 더 낮은 이벤트.
        // (예: 배송 완료 후 실제로 '배송 중' 으로 돌아간 진짜 사건 — 재배송)
        //
        // 정답을 코드로 정하기 전에 답할 것: 우리는 무엇을 신뢰하는가?
        //   - rank 를 믿는다  → 상태는 절대 후퇴하지 않는다. 단순하고 안전. 진짜 후퇴를 놓친다
        //   - 시각을 믿는다   → 후퇴를 반영한다. 외부 시계를 신뢰해야 한다 (위험)
        // docs/04 Q3. 코드보다 이 판단을 말로 정리하는 게 이 테스트의 목적이다.
    }
}
