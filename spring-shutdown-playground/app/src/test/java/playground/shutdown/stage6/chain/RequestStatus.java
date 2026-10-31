package playground.shutdown.stage6.chain;

/** 요청 행(job_request.status)의 상태. */
public enum RequestStatus {

    /** 요청이 들어와 저장됐다. 체인이 끝까지 가도 이 값은 바뀌지 않는다 (진행 상태는 큐 쪽이 들고 있다). */
    REQUESTED,

    /** 체인 어딘가의 catch 가 markFailed 로 실패를 남겼다. */
    FAILED
}
