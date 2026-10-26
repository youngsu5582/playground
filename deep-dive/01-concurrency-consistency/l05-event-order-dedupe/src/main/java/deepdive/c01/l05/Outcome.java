package deepdive.c01.l05;

/** 이벤트 하나를 처리한 결과. 셋 다 정상이다 — 무엇이 일어났는지를 구분해 두면 운영에서 보인다. */
public enum Outcome {
    /** 상태에 반영했다 */
    APPLIED,
    /** 이미 처리한 messageId — 재전달이 잘 걸러졌다 */
    DUPLICATE,
    /** 처음 보는 메시지지만 이미 더 새로운 version 이 반영돼 있다 — 늦게 도착한 과거 */
    STALE
}
