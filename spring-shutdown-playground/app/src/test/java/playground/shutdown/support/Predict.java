package playground.shutdown.support;

/**
 * 예측 테스트의 핵심 장치 (java-playground 와 같은 방식).
 *
 * <p>기대값 자리에 {@code todo()} 를 둔다. 실행하기 전에 <b>먼저 예측해서</b> 값으로 바꾼다.
 * 바꾸지 않고 돌리면 {@link PredictionMissing} 으로 실패한다. "틀렸다" 가 아니라 "아직 예측하지 않았다" 는 뜻이다.
 */
public final class Predict {

    private Predict() {
    }

    /** 예측값 자리. 어떤 타입 자리에도 들어가도록 제네릭이다. 실행되면 항상 던진다. */
    public static <T> T todo() {
        throw new PredictionMissing();
    }

    public static final class PredictionMissing extends AssertionError {
        PredictionMissing() {
            super("예측값을 아직 적지 않았다 — todo() 를 내가 예측한 값으로 바꾸고 다시 실행한다");
        }
    }
}
