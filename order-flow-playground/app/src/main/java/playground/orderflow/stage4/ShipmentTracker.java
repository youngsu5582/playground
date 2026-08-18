package playground.orderflow.stage4;

import java.util.Optional;

/**
 * 배송 상태 추적기 — 순서를 보장하지 않는 외부 이벤트를 받아 현재 상태를 유지한다.
 *
 * <p>at-least-once 로 전달되는 이벤트를 소비하는 컨슈머가 반드시 갖춰야 할 세 가지를
 * 한 클래스에 압축했다:
 * <pre>
 *   1. 중복 제거      같은 eventId 두 번 → 두 번째는 DUPLICATE
 *   2. 순서 역전 방어  과거 상태가 늦게 도착 → STALE (상태를 되돌리지 않는다)
 *   3. 전이 검증      규칙에 없는 변화 → INVALID
 * </pre>
 *
 * <p><b>판정 순서가 곧 정책이다.</b> 중복 검사를 먼저 할지, 전이 검증을 먼저 할지에 따라
 * "중복이면서 동시에 무효한 이벤트" 의 결과 라벨이 달라진다. 정답은 하나가 아니지만,
 * <b>정한 순서를 말로 설명할 수 있어야</b> 한다. 권장: 중복 → stale → 전이 검증.
 * (이미 처리한 이벤트를 굳이 다시 검증할 이유가 없다)
 *
 * <p><b>구현 힌트</b>
 * <ul>
 *   <li>상태 저장: {@code Map<shipmentId, ShipmentStatus>}</li>
 *   <li>중복 판정: {@code Set<eventId>} — 이 Set 이 무한히 커지는 문제는 docs/04 Q4</li>
 *   <li>stale 판정: {@code rank} 비교. 같은 rank 는 어떻게? 그것도 결정 사항이다</li>
 * </ul>
 */
public class ShipmentTracker {

    /**
     * 이벤트 1건을 반영하고 결과 라벨을 돌려준다.
     *
     * <p>요구사항:
     * <ol>
     *   <li>처음 보는 배송 건의 첫 이벤트는 APPLIED (초기 상태는 없음으로 취급)</li>
     *   <li>같은 eventId 재도착 → DUPLICATE, 상태 변화 없음</li>
     *   <li>현재보다 낮은 rank → STALE, 상태 변화 없음
     *       (DELIVERED 인데 SHIPPED 가 오면 DELIVERED 유지)</li>
     *   <li>같은 rank 의 다른 eventId → STALE (상태는 이미 그 값이므로 바꿀 게 없다)</li>
     *   <li>DELIVERED / RETURNED 이후의 전진 시도 → INVALID</li>
     *   <li>단계 건너뛰기(READY → DELIVERED)는 <b>허용</b>한다.
     *       외부 배송사는 중간 단계를 안 보낼 수 있다. 여기서 INVALID 를 내면
     *       정상 배송이 영원히 미완료로 남는다 — 현실을 이기려 들지 말 것.</li>
     * </ol>
     *
     * <p>TODO(stage4): 구현.
     */
    public ProcessResult apply(ShipmentEvent event) {
        throw new UnsupportedOperationException("TODO: stage4");
    }

    /**
     * 현재 상태 조회. 아직 이벤트가 없으면 empty.
     *
     * <p>TODO(stage4): 구현.
     */
    public Optional<ShipmentStatus> statusOf(String shipmentId) {
        throw new UnsupportedOperationException("TODO: stage4");
    }

    /**
     * 결과 라벨별 처리 건수. 관측성(observability) 연습용.
     *
     * <p>실서비스에서 이 카운터가 메트릭으로 나가면
     * "STALE 이 갑자기 늘었다 = 상류 재처리가 돌고 있다" 같은 판단이 가능해진다.
     *
     * <p>TODO(stage4): 구현.
     */
    public long countOf(ProcessResult result) {
        throw new UnsupportedOperationException("TODO: stage4");
    }
}
