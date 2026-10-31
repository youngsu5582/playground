package playground.shutdown.stage6.chain;

import java.util.List;

/** 체인을 잇는 두 이벤트. 요청이 검증되면 Requested, job 을 저장하면 Created. */
public final class JobEvents {

    private JobEvents() {
    }

    /** 검증을 통과한 요청. {@link JobCreateListener} 가 받는다. */
    public record Requested(long requestId, String userId, int jobCount) {
    }

    /** job 을 저장했다. 커밋된 뒤에 {@link JobProduceListener} 가 받는다. */
    public record Created(long requestId, String userId, List<Long> jobIds) {
    }
}
