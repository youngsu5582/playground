package playground.orderflow.stage4;

/**
 * 이벤트 1건의 처리 결과.
 *
 * <p><b>왜 boolean 이 아니라 enum 인가</b> — 여기가 이 스테이지에서 가장 설명 가치가 높은 지점이다.
 * "처리 안 함" 에는 네 가지 다른 이유가 있고, 각각 운영 대응이 완전히 다르다:
 *
 * <pre>
 *   DUPLICATE  정상이다. 재시도가 잘 동작한 것 → 무시하고 카운트만
 *   STALE      정상이다. 늦게 온 과거 이벤트 → 무시하고 카운트만
 *   INVALID    비정상이다. 규칙에 없는 전이 → 알람 대상. 우리 모델이 현실과 어긋났다는 뜻
 *   APPLIED    반영됨
 * </pre>
 *
 * <p>이걸 {@code false} 하나로 뭉치면 운영에서 "무시된 이벤트 3,000건" 만 보이고
 * 그중 몇 건이 진짜 문제인지 알 수 없다. 대시보드에서 <b>DUPLICATE 는 평평하고
 * INVALID 만 튀는</b> 그림을 볼 수 있어야 한다.
 */
public enum ProcessResult {

    /** 상태가 실제로 바뀌었다 */
    APPLIED,

    /** 이미 처리한 eventId */
    DUPLICATE,

    /** 현재보다 과거 상태 — 순서가 역전되어 늦게 도착 */
    STALE,

    /** 허용되지 않는 전이 (종료 상태 이후 등) */
    INVALID,
    ;

    public boolean changed() {
        return this == APPLIED;
    }
}
