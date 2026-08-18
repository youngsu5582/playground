package playground.orderflow.stage2;

/**
 * 같은 멱등키로 <b>다른 내용</b>의 요청이 들어온 경우.
 *
 * <p>이건 재시도가 아니라 클라이언트 버그(키 재사용)다. 조용히 기존 결과를 돌려주면
 * "요청한 것과 다른 주문이 생겼다" 는 최악의 형태로 사고가 난다.
 * HTTP 로는 409 Conflict 에 해당한다.
 */
public class IdempotencyConflictException extends RuntimeException {

    public IdempotencyConflictException(String key) {
        super("동일한 멱등키로 다른 요청이 도착했습니다: " + key);
    }
}
