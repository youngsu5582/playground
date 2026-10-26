package deepdive.c01.l03;

/**
 * 같은 멱등 키로 <b>다른 내용</b>의 요청이 들어왔다.
 *
 * <p>재시도가 아니라 클라이언트 버그(키 재사용)다. 조용히 기존 결과를 돌려주면 "요청한 것과 다른 결제가 처리됐다"는
 * 최악의 모양이 된다. HTTP 로는 409 Conflict (Stripe 는 400 계열 idempotency_error).
 */
public final class IdempotencyKeyConflictException extends RuntimeException {

    public IdempotencyKeyConflictException(String key) {
        super("같은 멱등 키로 다른 내용의 요청이 왔다: " + key);
    }
}
