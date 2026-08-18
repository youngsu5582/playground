package playground.orderflow.stage5;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Disabled;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.time.Instant;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * stage5 — 정렬 기준을 비즈니스 규칙으로 다루기.
 *
 * <p>쉬워 보이지만 시간을 태우는 두 함정:
 * <ul>
 *   <li>{@code PriorityQueue} 의 순회 순서를 정렬 순서로 착각</li>
 *   <li>마지막 tie-breaker 누락 → 테스트가 실행마다 다르게 통과/실패</li>
 * </ul>
 */
class TaskDispatcherTest {

    private TaskDispatcher sut;
    private static final Instant T0 = Instant.parse("2025-01-01T09:00:00Z");

    @BeforeEach
    void setUp() {
        sut = new TaskDispatcher();
    }

    private static PickingTask task(String id, long dueMinutes, int priority, long createdMinutes) {
        return new PickingTask(id, T0.plusSeconds(dueMinutes * 60), priority, T0.plusSeconds(createdMinutes * 60));
    }

    @Test
    @DisplayName("[명세 견본] 마감이 이른 작업이 먼저 나온다")
    void 마감이_이른_것이_먼저다() {
        sut.submit(task("late", 120, 1, 0));
        sut.submit(task("soon", 30, 1, 0));
        sut.submit(task("mid", 60, 1, 0));

        assertThat(sut.poll()).get().extracting(PickingTask::taskId).isEqualTo("soon");
        assertThat(sut.poll()).get().extracting(PickingTask::taskId).isEqualTo("mid");
        assertThat(sut.poll()).get().extracting(PickingTask::taskId).isEqualTo("late");
        assertThat(sut.poll()).isEmpty();
    }

    @Test
    @Disabled("TODO: stage5 — 직접 작성")
    @DisplayName("마감이 같으면 priority 가 낮은(급한) 것이 먼저다")
    void 마감이_같으면_우선순위로_가른다() {
    }

    @Test
    @Disabled("TODO: stage5 — 직접 작성")
    @DisplayName("마감·우선순위가 같으면 먼저 생성된 것이 먼저다 (FIFO)")
    void 동률이면_생성순이다() {
    }

    @Test
    @Disabled("TODO: stage5 — 직접 작성")
    @DisplayName("모든 기준이 같아도 순서는 결정론적이다 (taskId 사전순)")
    void 완전_동률에서도_순서가_흔들리지_않는다() {
        // 완전히 동일한 필드를 가진 작업 5개를 넣고 전부 꺼낸 뒤,
        // 같은 시나리오를 10회 반복해서 매번 같은 순서인지 확인한다.
        // 이 테스트가 없으면 flaky 를 나중에 운영에서 만난다.
    }

    @Test
    @Disabled("TODO: stage5 — 직접 작성. 함정 확인용")
    @DisplayName("peekTop 은 정렬된 순서를 준다 (PriorityQueue 순회 순서가 아니다)")
    void peekTop_은_정렬_순서를_보장한다() {
        // ★ 먼저 일부러 틀리게 짜봐라: new ArrayList<>(queue).subList(0, n)
        //   작업을 6~7개 넣으면 순서가 어긋나기 시작한다. 그 장면을 보는 게 이 테스트의 목적이다.
        //   (힙은 부분 순서만 유지한다 — 루트만 최소값이고 나머지 배열은 정렬돼 있지 않다)
        //
        // 그다음 제대로: 별도 정렬된 복사본을 만들거나, 애초에 다른 자료구조를 쓴다.
    }

    @Test
    @Disabled("TODO: stage5 — 직접 작성")
    @DisplayName("같은 taskId 를 두 번 넣으면 한 번만 들어간다")
    void 중복_등록은_무시한다() {
        // stage2 의 멱등성이 여기서도 나온다. 큐에 같은 작업이 두 번 들어가면
        // 창고에서 같은 물건을 두 번 집으러 간다.
    }

    @Test
    @Disabled("TODO: stage5 — 직접 작성")
    @DisplayName("빈 큐에서 poll 하면 empty 이고 예외가 아니다")
    void 빈_큐는_예외를_던지지_않는다() {
    }

    @Test
    @Disabled("TODO: stage5 — 직접 작성")
    @DisplayName("overdueTasks 는 기준 시각을 넘긴 작업만 돌려준다")
    void 마감_초과_작업을_찾아낸다() {
        // 경계값: dueAt == now 인 작업은 초과인가 아닌가?
        // isAfter 냐 !isBefore 냐로 갈린다. 정하고, 테스트 이름에 남겨라.
    }

    @Test
    @Disabled("TODO: stage5 — 여유 있으면")
    @DisplayName("작업 1만 건을 넣고 꺼내도 순서가 정확하다")
    void 대량_작업에서도_순서가_유지된다() {
        // 성능 측정이 목적이 아니다. n 이 커졌을 때만 드러나는 힙 버그를 잡는 게 목적.
        // 겸사겸사: submit n회 + poll n회의 복잡도는? O(n log n).
        // 반면 매번 전체 정렬을 다시 하면 O(n² log n) 이 된다 — 이 비교를 말할 수 있어야 한다.
    }
}
