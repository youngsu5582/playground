package playground.shutdown.support;

/** result(name) 의 답. 작업 안에서 자원(Redis·MQ·DB)을 써 본 결과. */
public enum Outcome {

    /** 자원을 썼고 성공했다. */
    SUCCESS,

    /** 자원을 썼는데 예외가 났다 (이미 멈췄거나 닫힌 자원). */
    FAILURE,

    /** 써 보지도 못했다 (작업이 실행되지 않았거나, 쓰기 전에 끊겼다). */
    NOT_ATTEMPTED
}
