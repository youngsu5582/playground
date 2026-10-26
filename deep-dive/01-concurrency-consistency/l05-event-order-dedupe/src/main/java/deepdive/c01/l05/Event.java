package deepdive.c01.l05;

/**
 * DB 에 도착한 이벤트 하나 — 브로커가 어떻게 가져왔든 "도착한 순간"의 모습.
 *
 * @param messageId  메시지 한 건의 신원. 같은 메시지가 재전달되면 같은 값 (중복을 거르는 축)
 * @param shipmentId 어느 배송 건의 이벤트인가 (순서를 따지는 단위)
 * @param version    그 배송 건 안에서의 순번. 클수록 최신 (역전을 거르는 축)
 * @param status     이 이벤트가 말하는 배송 상태
 */
public record Event(String messageId, String shipmentId, int version, String status) {}
