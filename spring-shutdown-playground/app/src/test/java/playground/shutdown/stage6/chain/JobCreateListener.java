package playground.shutdown.stage6.chain;

import org.springframework.context.ApplicationEventPublisher;
import org.springframework.context.event.EventListener;
import org.springframework.scheduling.annotation.Async;
import org.springframework.transaction.annotation.Transactional;
import playground.shutdown.timeline.Timeline;

import java.util.List;

/**
 * 체인 1단계. 검증된 요청을 받아 job 을 저장하고, 저장했다는 이벤트를 발행한다.
 * 이벤트를 받는 {@link JobProduceListener} 는 이 트랜잭션이 커밋된 뒤에 같은 풀에서 돈다.
 */
public class JobCreateListener {

    private final JobStore store;
    private final ApplicationEventPublisher events;
    private final Holds holds;

    public JobCreateListener(JobStore store, ApplicationEventPublisher events, Holds holds) {
        this.store = store;
        this.events = events;
        this.holds = holds;
    }

    @Async("poolA")
    @Transactional
    @EventListener
    public void create(JobEvents.Requested event) {
        Timeline.record("  create 시작");
        try {
            List<Long> jobIds = store.saveJobs(event.requestId(), event.jobCount());
            events.publishEvent(new JobEvents.Created(event.requestId(), event.userId(), jobIds));
            holds.beforeCommit().await();
            Timeline.record("  create 끝 (메서드 반환)");
        } catch (Exception e) {
            Timeline.record("  create 실패 처리: " + e.getClass().getSimpleName());
            Step.run("create markFailed", () -> store.markFailed(event.requestId(), e.getMessage()));
        }
    }
}
