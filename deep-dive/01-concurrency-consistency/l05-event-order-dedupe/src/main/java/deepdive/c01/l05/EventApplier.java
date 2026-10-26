package deepdive.c01.l05;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.SQLException;
import java.util.function.Supplier;

/**
 * 도착한 이벤트를 배송 상태에 반영한다. Kafka 는 여기 없다 — 이벤트가 DB 앞에 도착한 순간만 다룬다.
 *
 * <pre>
 * CREATE TABLE shipment (id text PRIMARY KEY, version int NOT NULL, status text NOT NULL, change_count int NOT NULL);
 * CREATE TABLE inbox (message_id text PRIMARY KEY);
 * </pre>
 *
 * {@code change_count} 는 "반영된 횟수" — 알림 발송 · 포인트 적립처럼 두 번 하면 안 되는 부수 효과의 대역이다.
 * 고칠 곳은 {@link #apply}.
 */
public final class EventApplier {

    private final Supplier<Connection> db;

    public EventApplier(Supplier<Connection> db) {
        this.db = db;
    }

    /**
     * TODO(구현) 이벤트를 inbox 로 중복을 거르고, version 이 더 클 때만 반영한다 — 전부 한 트랜잭션 안에서.
     *
     * <h3>지금 무엇이 문제인가</h3>
     * 지금은 받은 이벤트를 곧바로 덮어쓴다. 같은 이벤트가 두 번 오면 {@code change_count} 가 2 가 되고 (예측 Q01),
     * v3 다음에 v2 가 늦게 도착하면 상태가 v2 로 되돌아간다 (예측 Q02). {@code EventApplierImplementTest} 가 이걸 잡는다.
     *
     * <h3>할 일</h3>
     * <ol>
     *   <li>새 커넥션을 열고 자동 커밋을 끈다 — 아래 2~3번이 <b>한 트랜잭션</b>이어야 한다 (예측 Q05 · Q06)</li>
     *   <li>이 메시지를 처음 보는지는 inbox 에 넣어 보고 <b>영향 행 수</b>로 안다 — 0 이면 {@link Outcome#DUPLICATE}</li>
     *   <li>shipment 에 반영하되, 저장된 version 과 비교하는 조건을 upsert 에 붙인다.
     *       반영됐으면 {@link Outcome#APPLIED}, 조건에 걸려 안 바뀌었으면 {@link Outcome#STALE}
     *       (반영할 때 {@code change_count} 를 1 올린다. 처음 보는 배송 건이면 {@code change_count} 는 1 로 시작)</li>
     *   <li>커밋한다. 어디서든 {@code SQLException} 이 나면 롤백하고 {@code IllegalStateException} 으로 감싸 던진다</li>
     * </ol>
     *
     * <h3>헷갈리기 쉬운 곳</h3>
     * <ul>
     *   <li>STALE 이어도 inbox 기록은 <b>남긴다</b> — 같은 메시지가 또 오면 DUPLICATE 로 끝나야 한다</li>
     *   <li>조건은 "저장된 version 이 이벤트의 version 보다 <b>작을 때만</b>" 덮어쓴다 — 같은 version 도 덮어쓰지 않는다 (예측 Q03)</li>
     *   <li>inbox INSERT 를 건너뛰고 반영부터 하면 안 된다 — 같은 messageId 가 동시에 오면 둘 다 반영한다 (예측 Q09)</li>
     *   <li>inbox 를 먼저 커밋하고 반영을 따로 하면, 그 사이에 죽었을 때 "처리됨" 인데 상태는 안 바뀐 채로 남는다</li>
     * </ul>
     */
    public Outcome apply(Event e) {
        try (Connection c = db.get();
             PreparedStatement ps = c.prepareStatement("""
                     INSERT INTO shipment (id, version, status, change_count) VALUES (?, ?, ?, 1)
                     ON CONFLICT (id) DO UPDATE SET version = EXCLUDED.version, status = EXCLUDED.status,
                                                    change_count = shipment.change_count + 1""")) {
            ps.setString(1, e.shipmentId());
            ps.setInt(2, e.version());
            ps.setString(3, e.status());
            ps.executeUpdate();
            return Outcome.APPLIED;
        } catch (SQLException ex) {
            throw new IllegalStateException("이벤트 처리 실패: " + e.messageId(), ex);
        }
    }
}
