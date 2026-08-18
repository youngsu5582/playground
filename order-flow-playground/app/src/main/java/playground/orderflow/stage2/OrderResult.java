package playground.orderflow.stage2;

/**
 * 주문 생성 결과.
 *
 * @param orderId 생성된(또는 이미 존재하던) 주문 ID
 * @param replayed 이번 호출이 <b>기존 결과의 재생</b>인지 여부.
 *                 API 응답 바디에는 보통 안 내보내지만, 로그·메트릭에는 반드시 남긴다.
 *                 재생 비율이 갑자기 튀면 상류에서 재시도 폭풍이 일고 있다는 신호다.
 */
public record OrderResult(String orderId, boolean replayed) {

    public static OrderResult created(String orderId) {
        return new OrderResult(orderId, false);
    }

    public static OrderResult replayed(String orderId) {
        return new OrderResult(orderId, true);
    }
}
