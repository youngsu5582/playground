package deepdive.c01.l03;

/**
 * 결제 결과.
 *
 * @param paymentId 생성된(또는 이미 존재하던) 결제 번호
 * @param replayed  이번 호출이 <b>기존 결과의 재생</b>인지. 응답 바디에는 보통 안 내보내지만 로그·메트릭에는 남긴다 —
 *                  재생 비율이 튀면 상류에서 재시도 폭풍이 일고 있다는 신호다.
 */
public record PaymentResult(long paymentId, boolean replayed) {

    public static PaymentResult created(long paymentId) {
        return new PaymentResult(paymentId, false);
    }

    public static PaymentResult replayed(long paymentId) {
        return new PaymentResult(paymentId, true);
    }
}
