package playground.orderflow.stage5;

import java.time.Instant;
import java.util.Comparator;
import java.util.List;
import java.util.Optional;

/**
 * 작업 우선순위 배분.
 *
 * <p>겉보기엔 "정렬 한 줄" 이지만, 실제로 평가되는 건 세 가지다:
 * <ol>
 *   <li><b>Comparator 를 정확히 조립하는가</b> — 다단 정렬, 동률 처리, 역순</li>
 *   <li><b>자료구조 선택을 설명하는가</b> — 왜 정렬된 List 가 아니라 힙인가</li>
 *   <li><b>정렬 기준이 곧 비즈니스 규칙임을 아는가</b> — 순서를 바꾸면 SLA 위반 건수가 바뀐다</li>
 * </ol>
 *
 * <p><b>구현 힌트</b>
 * <ul>
 *   <li>{@code Comparator.comparing(...).thenComparing(...)} 체인. 직접 int 를 리턴하는
 *       비교 함수를 손으로 짜면 (a) 오버플로 (b) 비대칭 버그가 나기 쉽다</li>
 *   <li>{@code PriorityQueue} 는 <b>순회 순서를 보장하지 않는다.</b>
 *       {@code toString()} 이나 {@code stream()} 으로 확인하려 하면 힙 내부 배열이 나온다.
 *       꺼내는 순서만 정렬돼 있다 — 이걸 모르면 테스트에서 시간을 크게 태운다</li>
 * </ul>
 */
public class TaskDispatcher {

    /**
     * 작업 처리 순서를 결정하는 비교자.
     *
     * <p>순서 규칙 (앞선 기준이 우선):
     * <ol>
     *   <li>마감({@code dueAt})이 이른 것 먼저</li>
     *   <li>마감이 같으면 {@code priority} 가 낮은(=급한) 것 먼저</li>
     *   <li>그것도 같으면 {@code createdAt} 이 이른 것 먼저 (FIFO)</li>
     *   <li>전부 같으면 {@code taskId} 사전순 — <b>결정론적 순서를 위해 반드시 넣는다.</b>
     *       마지막 tie-breaker 가 없으면 같은 입력에 실행마다 다른 순서가 나와
     *       테스트가 간헐적으로 깨진다 (flaky)</li>
     * </ol>
     *
     * <p>TODO(stage5): 구현.
     */
    public static Comparator<PickingTask> byUrgency() {
        throw new UnsupportedOperationException("TODO: stage5");
    }

    /**
     * 작업을 큐에 넣는다. 같은 taskId 재등록은 무시한다(중복 방지).
     *
     * <p>TODO(stage5): 구현.
     */
    public void submit(PickingTask task) {
        throw new UnsupportedOperationException("TODO: stage5");
    }

    /**
     * 가장 급한 작업을 꺼낸다(제거). 비어 있으면 empty.
     *
     * <p>TODO(stage5): 구현.
     */
    public Optional<PickingTask> poll() {
        throw new UnsupportedOperationException("TODO: stage5");
    }

    /**
     * 꺼내지 않고 상위 {@code n} 건을 순서대로 본다 (대시보드용).
     *
     * <p>{@code PriorityQueue} 를 그대로 stream 하면 <b>정렬되지 않은</b> 결과가 나온다.
     * 이 메서드가 그 함정을 드러내려고 존재한다.
     *
     * <p>TODO(stage5): 구현.
     */
    public List<PickingTask> peekTop(int n) {
        throw new UnsupportedOperationException("TODO: stage5");
    }

    /**
     * {@code now} 기준 마감을 넘긴 작업들. 알람/에스컬레이션 대상.
     *
     * <p>TODO(stage5): 구현.
     */
    public List<PickingTask> overdueTasks(Instant now) {
        throw new UnsupportedOperationException("TODO: stage5");
    }

    /**
     * 대기 중인 작업 수.
     *
     * <p>이 값이 시간에 따라 늘기만 하면 처리량 < 유입량이라는 뜻이다.
     * 큐 길이(backlog)는 가장 값싸고 정직한 부하 지표다.
     *
     * <p>TODO(stage5): 구현.
     */
    public int size() {
        throw new UnsupportedOperationException("TODO: stage5");
    }
}
