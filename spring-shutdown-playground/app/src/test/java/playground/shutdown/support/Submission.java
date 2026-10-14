package playground.shutdown.support;

/** submit(name) 의 답. 풀에 작업을 넘긴 결과. */
public enum Submission {

    /** 풀이 받았다 (대기열에 들어갔거나 바로 실행됐다). */
    ACCEPTED,

    /** 풀이 이미 접수를 닫아 TaskRejectedException 으로 거절했다. */
    REJECTED,

    /** 넘기지도 않았다. */
    NOT_SUBMITTED
}
