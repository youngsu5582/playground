package playground.orderflow.stage4;

import java.time.Instant;
import java.util.Objects;

/**
 * 외부 배송사가 보내오는 상태 변경 통지.
 *
 * @param eventId    이벤트 고유 ID. <b>중복 판정의 유일한 기준</b>이다.
 *                   외부가 이 값을 안 주면? — docs/04 Q1 에서 다룬다.
 * @param shipmentId 어떤 배송 건인지
 * @param status     통지된 상태
 * @param occurredAt <b>발생 시각</b>. 도착 시각이 아니다.
 *                   이 둘을 헷갈리는 순간 순서 처리가 전부 무너진다 —
 *                   네트워크·재시도 때문에 "먼저 발생한 이벤트가 나중에 도착" 하는 것이
 *                   예외가 아니라 일상이다.
 */
public record ShipmentEvent(
        String eventId,
        String shipmentId,
        ShipmentStatus status,
        Instant occurredAt
) {

    public ShipmentEvent {
        Objects.requireNonNull(eventId, "eventId");
        Objects.requireNonNull(shipmentId, "shipmentId");
        Objects.requireNonNull(status, "status");
        Objects.requireNonNull(occurredAt, "occurredAt");
    }
}
