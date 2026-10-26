package deepdive.testkit;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.fail;

/**
 * [예측] <b>돌리기 전에 결과를 적는다</b>. 틀린 예측이 가장 좋은 교재다.
 *
 * <pre>
 * String 예측 = "?";          ← 이걸 "50" 처럼 바꾼 뒤 돌린다
 * Predict.확인("A 의 두 번째 SELECT 는?", 예측, 실제값);
 * </pre>
 *
 * <ul>
 *   <li>"?" 그대로면 실제 값을 <b>보여 주지 않고</b> 실패한다 — 먼저 생각하게. 그 테스트의 타임라인도 숨긴다</li>
 *   <li>틀리면 실제 값과 함께 실패한다 — 왜 틀렸는지 NOTES.md 에 한 줄</li>
 *   <li>띄어쓰기 · 대소문자는 무시한다 ("에러 40001" = "에러40001", "TRUE" = "true")</li>
 * </ul>
 */
public final class Predict {

    public static final String 모름 = "?";

    private Predict() {}

    public static void 확인(String 질문, String 예측, Object 실제) {
        if (모름.equals(예측)) {
            Timeline.hide(); // 타임라인의 결과 줄이 곧 정답 — 같이 숨긴다
            fail("""

                    먼저 예측을 적는다 → %s
                      테스트 코드의  String 예측 = "?";  를 내 답으로 바꾸고 다시 돌린다.
                      (실제 값은 예측을 적은 뒤에야 보여 준다)""".formatted(질문));
        }
        assertThat(정리(String.valueOf(실제)))
                .as("""

                        예측이 빗나갔다 → %s
                          내 예측: %s
                          왜 다른지 한 줄로 NOTES.md 에 남기자 (틀린 예측이 제일 남는다)""".formatted(질문, 예측))
                .isEqualTo(정리(예측));
    }

    /** 비교 전에 띄어쓰기를 지우고 소문자로 — 형식 때문에 틀리지 않게. */
    private static String 정리(String s) {
        return s.replaceAll("\\s+", "").toLowerCase();
    }
}
