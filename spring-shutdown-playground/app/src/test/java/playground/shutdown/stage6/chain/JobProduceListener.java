package playground.shutdown.stage6.chain;

import org.springframework.scheduling.annotation.Async;
import org.springframework.transaction.event.TransactionPhase;
import org.springframework.transaction.event.TransactionalEventListener;
import playground.shutdown.timeline.Timeline;

/**
 * 체인 2단계. job 저장이 커밋된 뒤 사용자 대기열에 넣는다.
 * 실패하면 요청을 FAILED 로 남긴다.
 */
public class JobProduceListener {

    private final UserJobQueue queue;
    private final JobStore store;
    private final Holds holds;

    public JobProduceListener(UserJobQueue queue, JobStore store, Holds holds) {
        this.queue = queue;
        this.store = store;
        this.holds = holds;
    }

    @Async("poolA")
    @TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)
    public void produce(JobEvents.Created event) {
        Timeline.record("  produce 시작");
        try {
            holds.beforeEnqueue().await();
            queue.enqueue(event);
            Timeline.record("  produce 끝");
        } catch (Exception e) {
            Timeline.record("  produce 실패 처리: " + e.getClass().getSimpleName());
            Step.run("produce markFailed", () -> store.markFailed(event.requestId(), e.getMessage()));
        }
    }
}
