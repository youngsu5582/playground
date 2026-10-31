package playground.shutdown.stage6.chain;

import org.springframework.jdbc.core.JdbcTemplate;

import java.util.List;

/**
 * 요청(job_request)과 job 행을 다룬다. 스키마는 {@code ChainInfra.reset()} 이 만든다.
 * 트랜잭션은 부르는 쪽이 정한다 — create 는 @Transactional 안에서, markFailed 는 auto-commit 으로 쓴다.
 */
public class JobStore {

    private final JdbcTemplate jdbc;

    public JobStore(JdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    /** API 가 요청을 받은 순간. 체인이 시작되기 전에 이미 커밋돼 있다. */
    public long newRequest(String userId) {
        return jdbc.queryForObject(
                "INSERT INTO job_request (user_id, status) VALUES (?, 'REQUESTED') RETURNING id", Long.class, userId);
    }

    public List<Long> saveJobs(long requestId, int count) {
        return jdbc.queryForList(
                "INSERT INTO job (request_id) SELECT ? FROM generate_series(1, ?) RETURNING id", Long.class, requestId, count);
    }

    public void markFailed(long requestId, String reason) {
        jdbc.update("UPDATE job_request SET status = 'FAILED', reason = ? WHERE id = ?", reason, requestId);
    }
}
