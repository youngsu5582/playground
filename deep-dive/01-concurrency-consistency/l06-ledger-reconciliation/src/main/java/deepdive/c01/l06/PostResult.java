package deepdive.c01.l06;

/** {@link LedgerService#post} 의 결과. */
public enum PostResult {
    /** 새로 반영했다 */
    POSTED,
    /** 같은 거래 id 가 이미 반영되어 있어 아무것도 하지 않았다 (두 번째 시도는 오류가 아니라 정상) */
    DUPLICATE,
    /** 보내는 계좌의 잔고가 모자라 반영하지 않았다 — 아무 흔적도 남지 않아야 한다 (같은 거래 id 로 다시 시도할 수 있게) */
    INSUFFICIENT
}
