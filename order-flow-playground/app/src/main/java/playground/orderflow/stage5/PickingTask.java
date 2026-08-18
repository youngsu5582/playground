package playground.orderflow.stage5;

import java.time.Instant;
import java.util.Objects;

/**
 * 창고 작업자에게 내려보낼 피킹 작업 1건.
 *
 * @param taskId    작업 ID
 * @param dueAt     이 시각까지 출고되어야 한다 (SLA 마감)
 * @param priority  낮을수록 급함 (1 = 최우선). 유료 배송 등급 같은 것
 * @param createdAt 생성 시각. 동률일 때 먼저 온 것을 먼저 처리(FIFO)하는 tie-breaker
 */
public record PickingTask(
        String taskId,
        Instant dueAt,
        int priority,
        Instant createdAt
) {

    public PickingTask {
        Objects.requireNonNull(taskId, "taskId");
        Objects.requireNonNull(dueAt, "dueAt");
        Objects.requireNonNull(createdAt, "createdAt");
    }

    /** {@code now} 기준으로 마감을 넘겼는가. */
    public boolean isOverdue(Instant now) {
        return now.isAfter(dueAt);
    }
}
