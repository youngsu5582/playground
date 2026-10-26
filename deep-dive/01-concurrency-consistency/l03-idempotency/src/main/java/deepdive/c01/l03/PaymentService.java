package deepdive.c01.l03;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.function.Supplier;

/**
 * 멱등 결제 — 타임아웃 뒤 같은 요청이 다시 와도 <b>돈은 한 번만</b> 나간다.
 *
 * <p>한 번의 호출 = 한 트랜잭션 (READ COMMITTED). 흐름은 이렇다.
 * <pre>
 * BEGIN
 *   claim  ── 이 키를 내가 선점했나?
 *     예   → process : 외부 결제 호출 → payments INSERT → 키를 DONE 으로
 *     아니오 → replay  : 저장된 요청 지문과 비교 → 같으면 저장된 응답, 다르면 예외
 * COMMIT   (예외가 나면 ROLLBACK — 키 행도 같이 사라지므로 같은 키로 다시 시도할 수 있다)
 * </pre>
 *
 * <pre>
 * CREATE TABLE idempotency_keys (key text PRIMARY KEY, request_hash text NOT NULL,
 *                                status text NOT NULL, response text);
 * CREATE TABLE payments (id bigserial PRIMARY KEY, customer_id text NOT NULL, amount bigint NOT NULL);
 * </pre>
 *
 * 고칠 곳은 {@link #claim} 과 {@link #replay} 두 곳. 나머지 배관은 손대지 않는다.
 */
public final class PaymentService {

    private final Supplier<Connection> db;
    private final Runnable externalCharge;

    /**
     * @param externalCharge 외부 결제사 호출 흉내 — 느리고, 실패할 수 있고, <b>한 번 나간 돈은 되돌릴 수 없다</b>.
     *                       테스트가 호출 횟수를 센다 (이 횟수가 곧 '실제로 결제된 횟수')
     */
    public PaymentService(Supplier<Connection> db, Runnable externalCharge) {
        this.db = db;
        this.externalCharge = externalCharge;
    }

    public PaymentResult pay(String idempotencyKey, PaymentRequest request) {
        if (idempotencyKey == null || idempotencyKey.isBlank()) {
            throw new IllegalArgumentException("idempotencyKey must not be null or blank");
        }
        String hash = request.fingerprint();
        try (Connection c = db.get()) {
            c.setAutoCommit(false);
            try {
                PaymentResult result = claim(c, idempotencyKey, hash)
                        ? process(c, idempotencyKey, request)
                        : replay(c, idempotencyKey, hash);
                c.commit();
                return result;
            } catch (SQLException | RuntimeException e) {
                c.rollback();
                throw e;
            }
        } catch (SQLException e) {
            throw new IllegalStateException("결제 처리 중 DB 오류: " + e.getMessage(), e);
        }
    }

    /**
     * TODO(구현) 이 키를 <b>내가</b> 처리해도 되는지, 키 행을 넣는 동시에 판정한다 (true = 내가 선점).
     *
     * <h3>지금 무엇이 문제인가</h3>
     * 지금은 "키가 있나 SELECT → 없으면 INSERT 하고 처리하러 간다" 다. 같은 키가 동시에 오면 둘 다 SELECT 에서 "없음"을 보고
     * 둘 다 true 를 돌려받아 외부 결제가 두 번 나간다 (예측 Q01 의 교차 실행과 같은 모양).
     * INSERT 에 {@code ON CONFLICT DO NOTHING} 이 붙어 있어 에러도 안 난다 — 그래서 더 조용히 샌다.
     * {@code PaymentImplementTest} 의 "같은 키로 20번 동시 호출" 이 이걸 잡는다.
     *
     * <h3>할 일</h3>
     * <ol>
     *   <li>SELECT 로 먼저 확인하는 부분을 지운다 — 확인과 선점을 <b>한 문장</b>으로 합친다</li>
     *   <li>{@code INSERT INTO idempotency_keys (key, request_hash, status) VALUES (?, ?, 'IN_PROGRESS') ON CONFLICT (key) DO NOTHING}</li>
     *   <li>{@code executeUpdate()} 가 돌려주는 영향 행 수가 1 이면 true, 0 이면 false (예측 Q06 · Q07)</li>
     * </ol>
     *
     * <h3>헷갈리기 쉬운 곳</h3>
     * <ul>
     *   <li>같은 키가 이미 처리 중(미커밋)이면 이 INSERT 가 그 트랜잭션이 끝날 때까지 <b>기다린다</b> (예측 Q03 · Q07).
     *       기다림은 공짜로 온다 — 직접 sleep·polling 을 짜지 않는다</li>
     *   <li>기다리던 쪽이 풀렸을 때 0행이 나온다 → false → {@link #replay} 로 간다. 앞선 쪽이 롤백했다면 1행이 나온다 → 내가 처리한다</li>
     *   <li>SELECT 를 남겨 두고 영향 행 수까지 쓰는 건 중복이다 — 판정은 INSERT 하나가 한다</li>
     * </ul>
     */
    private boolean claim(Connection c, String key, String hash) throws SQLException {
        try (PreparedStatement ps = c.prepareStatement("SELECT 1 FROM idempotency_keys WHERE key = ?")) {
            ps.setString(1, key);
            try (ResultSet rs = ps.executeQuery()) {
                if (rs.next()) return false;
            }
        }
        try (PreparedStatement ps = c.prepareStatement("""
                INSERT INTO idempotency_keys (key, request_hash, status) VALUES (?, ?, 'IN_PROGRESS')
                ON CONFLICT (key) DO NOTHING""")) {
            ps.setString(1, key);
            ps.setString(2, hash);
            ps.executeUpdate();
        }
        return true;
    }

    /** 선점에 성공한 쪽의 일 — 외부 결제를 부르고, 결제 행을 만들고, 키를 DONE 으로 바꾼다. 실패하면 호출자가 롤백한다. */
    private PaymentResult process(Connection c, String key, PaymentRequest request) throws SQLException {
        externalCharge.run();
        long paymentId;
        try (PreparedStatement ps = c.prepareStatement(
                "INSERT INTO payments (customer_id, amount) VALUES (?, ?) RETURNING id")) {
            ps.setString(1, request.customerId());
            ps.setLong(2, request.amount());
            try (ResultSet rs = ps.executeQuery()) {
                rs.next();
                paymentId = rs.getLong(1);
            }
        }
        try (PreparedStatement ps = c.prepareStatement(
                "UPDATE idempotency_keys SET status = 'DONE', response = ? WHERE key = ?")) {
            ps.setString(1, Long.toString(paymentId));
            ps.setString(2, key);
            ps.executeUpdate();
        }
        return PaymentResult.created(paymentId);
    }

    /**
     * TODO(구현) 이미 있는 키 — 저장된 요청과 같으면 저장된 응답을 돌려주고, 다르면 {@link IdempotencyKeyConflictException}.
     *
     * <h3>지금 무엇이 문제인가</h3>
     * 지금은 요청 내용을 보지 않고 저장된 응답을 그냥 돌려준다. 같은 키에 다른 금액이 와도 "성공" 으로 보이는데,
     * 클라이언트가 낸 건 5만 원 결제인데 실제로는 1만 원 결제가 처리된 상태다.
     * {@code PaymentImplementTest} 의 "같은 키 다른 내용" 이 이걸 잡는다.
     *
     * <h3>할 일</h3>
     * <ol>
     *   <li>아래 SELECT 로 읽은 {@code request_hash} 를 인자로 받은 {@code hash} 와 비교한다</li>
     *   <li>다르면 {@code throw new IdempotencyKeyConflictException(key)}</li>
     * </ol>
     *
     * <h3>헷갈리기 쉬운 곳</h3>
     * <ul>
     *   <li>이 메서드는 선점에 실패(false)했을 때만 불린다 — 그때 키 행은 이미 <b>커밋돼 보이는</b> 행이다 (READ COMMITTED 에서 기다렸다 풀려났으므로)</li>
     *   <li>비교는 키가 아니라 <b>지문</b> — 같은 키는 이미 전제다</li>
     * </ul>
     */
    private PaymentResult replay(Connection c, String key, String hash) throws SQLException {
        try (PreparedStatement ps = c.prepareStatement(
                "SELECT request_hash, status, response FROM idempotency_keys WHERE key = ?")) {
            ps.setString(1, key);
            try (ResultSet rs = ps.executeQuery()) {
                if (!rs.next() || !"DONE".equals(rs.getString("status"))) {
                    throw new IllegalStateException("선점에 실패했는데 완료된 키 행이 없다: " + key);
                }
                return PaymentResult.replayed(Long.parseLong(rs.getString("response")));
            }
        }
    }
}
