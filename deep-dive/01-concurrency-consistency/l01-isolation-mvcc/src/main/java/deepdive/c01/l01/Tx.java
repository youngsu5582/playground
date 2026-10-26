package deepdive.c01.l01;

import java.sql.Connection;
import java.sql.SQLException;
import java.util.concurrent.ThreadLocalRandom;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.function.Supplier;

/** 트랜잭션 경계. 애플리케이션 코드는 이걸 거쳐서만 DB 를 바꾼다. */
public final class Tx {

    @FunctionalInterface
    public interface Work<T> {
        T run(Connection c) throws SQLException;
    }

    /** 직렬화 실패가 계속되면 언젠가는 포기해야 한다 — 무한 재시도는 장애를 키운다. */
    public static final int MAX_ATTEMPTS = 5;

    /** 지금까지 40001 때문에 다시 시도한 횟수. 테스트가 "재시도가 실제로 일어났나"를 볼 때 쓴다. */
    public static final AtomicInteger RETRIES = new AtomicInteger();

    private Tx() {}

    /**
     * TODO(구현) work 를 SERIALIZABLE 트랜잭션으로 실행하고, 직렬화 실패(40001)면 처음부터 다시 시도한다.
     *
     * <h3>지금 무엇이 문제인가</h3>
     * 지금은 기본 격리수준(READ COMMITTED)으로 한 번만 실행한다. 당직 의사 둘이 동시에 빠지면 둘 다 "2명이네"를 보고
     * 둘 다 성공해서 당직이 0명이 된다 (write skew — 예측 Q08). {@code WriteSkewImplementTest} 가 이걸 잡는다.
     *
     * <h3>할 일</h3>
     * <ol>
     *   <li>새 커넥션을 열고 {@code setAutoCommit(false)}, {@code setTransactionIsolation(Connection.TRANSACTION_SERIALIZABLE)}</li>
     *   <li>{@code work.run(c)} → {@code c.commit()} → 결과 반환</li>
     *   <li>{@code SQLException} 이 나면 {@code c.rollback()}. SQLState 가 {@code "40001"} 이면 1번부터 <b>work 전체를</b> 다시</li>
     *   <li>다시 할 때마다 {@link #RETRIES} 를 1 올리고, 짧게 쉰다: {@link #sleepJitter()}</li>
     *   <li>40001 이 아니거나, 이미 {@link #MAX_ATTEMPTS} 번 시도했으면 포기:
     *       {@code throw new IllegalStateException("…", e)}</li>
     * </ol>
     *
     * <h3>헷갈리기 쉬운 곳</h3>
     * <ul>
     *   <li>40001 은 UPDATE 가 아니라 <b>commit</b> 에서 나기도 한다 (예측 Q09) — commit 도 같은 try 안에</li>
     *   <li>마지막 문장만 다시 하면 안 된다 — 앞에서 읽은 값(당직 2명)이 이미 틀렸다</li>
     *   <li>23505(유니크 위반) 같은 오류는 다시 해도 똑같다 — 재시도 대상이 아니다</li>
     * </ul>
     */
    public static <T> T serializable(Supplier<Connection> connections, Work<T> work) {
        try (Connection c = connections.get()) {
            c.setAutoCommit(false);
            try {
                T result = work.run(c);
                c.commit();
                return result;
            } catch (SQLException e) {
                c.rollback();
                throw new IllegalStateException("트랜잭션 실패: " + e.getMessage(), e);
            }
        } catch (SQLException e) {
            throw new IllegalStateException(e);
        }
    }

    /** 재시도 사이의 짧은 무작위 대기 (5~25ms). 둘이 같은 박자로 다시 부딪히지 않게. */
    static void sleepJitter() {
        try {
            Thread.sleep(ThreadLocalRandom.current().nextInt(5, 25));
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }
}
