package deepdive.c01.l02;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.time.Duration;
import java.util.Optional;
import java.util.function.Supplier;

/**
 * 작업 큐 — 워커 여럿이 "다음 작업 하나"를 집어 간다 (DB 를 큐로 쓰는 가장 흔한 형태).
 *
 * <pre>
 * CREATE TABLE jobs (id int PRIMARY KEY, status text NOT NULL DEFAULT 'pending', claimed_by text);
 * </pre>
 *
 * 규칙: <b>작업 하나는 정확히 한 워커만 집는다</b> (중복 0 · 누락 0).
 * 고칠 곳은 {@link #claimNext} 의 SELECT 한 문장.
 */
public final class JobQueue {

    private final Supplier<Connection> db;
    private final Duration thinkTime;

    /** @param thinkTime 고르고 나서 갱신하기까지의 지연 — 경쟁이 일어날 창을 넓힌다 (실서비스의 네트워크·로직 시간) */
    public JobQueue(Supplier<Connection> db, Duration thinkTime) {
        this.db = db;
        this.thinkTime = thinkTime;
    }

    /**
     * TODO(구현) 가장 앞의 pending 작업 하나를 집어 {@code running} 으로 바꾸고, 그 id 를 돌려준다. 남은 작업이 없으면 비어 있다.
     *
     * <h3>지금 무엇이 문제인가</h3>
     * 지금은 잠그지 않고 첫 pending 을 <b>읽기만</b> 한다. 워커 둘이 동시에 부르면 둘 다 같은 1번을 읽고,
     * 둘 다 "내가 집었다"며 갱신한다 — 중복 처리 (예측 Q02: 읽기는 락을 잡지도, 락에 막히지도 않는다).
     * {@code JobQueueImplementTest} 가 이걸 잡는다.
     *
     * <h3>할 일</h3>
     * <ol>
     *   <li>아래 {@code sql} 을 고쳐 고른 행을 <b>그 자리에서 잠근다</b> ({@code FOR UPDATE})</li>
     *   <li>다른 워커가 이미 잠근 행은 <b>기다리지 말고 건너뛴다</b> — 예측 Q05 의 그 절</li>
     * </ol>
     *
     * <h3>헷갈리기 쉬운 곳</h3>
     * <ul>
     *   <li>{@code FOR UPDATE} 만 붙여도 중복은 사라진다 — 하지만 두 번째 워커는 첫 워커의 커밋을 <b>기다린다</b> (예측 Q06).
     *       워커들이 같은 작업 앞에 한 줄로 선다. 이 줄을 없애는 게 2번이다</li>
     *   <li>SELECT 의 잠금은 커밋(또는 롤백)까지 간다 — 갱신과 커밋이 같은 트랜잭션 안이어야 한다 (이미 그렇게 짜여 있다)</li>
     * </ul>
     */
    public Optional<Long> claimNext(String worker) {
        try (Connection c = db.get()) {
            c.setAutoCommit(false);
            String sql = "SELECT id FROM jobs WHERE status = 'pending' ORDER BY id LIMIT 1";
            Long id = null;
            try (PreparedStatement ps = c.prepareStatement(sql); ResultSet rs = ps.executeQuery()) {
                if (rs.next()) id = rs.getLong(1);
            }
            if (id == null) {
                c.commit();
                return Optional.empty();
            }
            pause();
            try (PreparedStatement ps = c.prepareStatement("UPDATE jobs SET status = 'running', claimed_by = ? WHERE id = ?")) {
                ps.setString(1, worker);
                ps.setLong(2, id);
                ps.executeUpdate();
            }
            c.commit();
            return Optional.of(id);
        } catch (SQLException e) {
            throw new IllegalStateException("claimNext 실패: " + e.getMessage(), e);
        }
    }

    private void pause() {
        try {
            Thread.sleep(thinkTime.toMillis());
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }
}
