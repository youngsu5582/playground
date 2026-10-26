package deepdive.c01.l01;

import deepdive.testkit.PostgresLab;
import deepdive.testkit.Timeline;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.sql.Connection;
import java.sql.SQLException;
import java.time.Duration;
import java.util.List;
import java.util.concurrent.Callable;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.assertj.core.api.Assertions.catchThrowable;
import static org.assertj.core.api.Assertions.fail;

/**
 * [구현] {@link Tx#serializable} 를 채우면 초록이 된다. 진짜 PostgreSQL 위에서 진짜 동시성으로 돈다.
 */
@DisplayName("[구현] 01.01 Tx.serializable — write skew 막기")
class WriteSkewImplementTest {

    final PostgresLab lab = PostgresLab.get();
    final OnCallService service = new OnCallService(lab::connect, Duration.ofMillis(100));

    @BeforeEach
    void reset() {
        lab.exec("DROP TABLE IF EXISTS on_call",
                "CREATE TABLE on_call (doctor text PRIMARY KEY, on_call boolean NOT NULL)");
        Tx.RETRIES.set(0);
    }

    void twoOnCall() {
        lab.exec("DELETE FROM on_call", "INSERT INTO on_call VALUES ('alice', true), ('bob', true)");
    }

    /** alice 와 bob 이 같은 순간에 goOffCall. 두 호출의 결과(또는 예외)를 돌려준다. */
    List<Object> raceBoth() throws Exception {
        CountDownLatch start = new CountDownLatch(1);
        try (ExecutorService pool = Executors.newFixedThreadPool(2)) {
            Callable<Object> alice = () -> { start.await(); return call("alice"); };
            Callable<Object> bob = () -> { start.await(); return call("bob"); };
            Future<Object> fa = pool.submit(alice);
            Future<Object> fb = pool.submit(bob);
            start.countDown();
            return List.of(fa.get(), fb.get());
        }
    }

    Object call(String doctor) {
        try {
            return service.goOffCall(doctor);
        } catch (RuntimeException e) {
            return e;
        }
    }

    @Test
    void 당직은_동시에_빠져도_항상_1명_이상_남는다() throws Exception {
        for (int round = 1; round <= 5; round++) {
            Timeline.reset("구현 확인 " + round + "회차 — alice · bob 동시에 goOffCall");
            twoOnCall();
            List<Object> results = raceBoth();
            long left = ((Number) lab.one("SELECT count(*) FROM on_call WHERE on_call")).longValue();
            if (left < 1) {
                fail("""

                        정합성 깨짐: %d회차에서 당직이 %d명이 됐다 (규칙: 항상 1명 이상) — write skew.
                          두 트랜잭션이 각자 '2명이니 빠져도 된다'를 보고, 서로 다른 행을 고쳐서 행 락으로는 안 막혔다.
                          두 호출의 결과: %s
                          고칠 곳: Tx.serializable — SERIALIZABLE 로 돌리고, 40001 이면 처음부터 다시""".formatted(round, left, results));
            }
        }
    }

    @Test
    void 경쟁에서_진_쪽은_예외_대신_재시도해서_정상_응답을_받는다() throws Exception {
        twoOnCall();
        Timeline.reset("구현 확인 — 경쟁에서 진 쪽의 호출자는 무엇을 받나");
        List<Object> results = raceBoth();
        assertThat(results)
                .as("호출자에게 40001 이 새면 안 된다 — 재시도해서 '마지막 한 명이라 거절(false)'로 끝나야 한다")
                .allSatisfy(r -> assertThat(r).isInstanceOf(Boolean.class))
                .containsExactlyInAnyOrder(true, false);
        assertThat(Tx.RETRIES.get())
                .as("경쟁이 있었으면 40001 재시도가 최소 1번은 일어났어야 한다 (SERIALIZABLE 로 돌고 있나?)")
                .isGreaterThanOrEqualTo(1);
    }

    /**
     * 40001 은 commit 에서도 난다 (예측 Q09). work 안에서 별도 연결로 충돌하는 SERIALIZABLE 트랜잭션을 먼저 커밋시켜,
     * 우리 쪽은 work 를 <b>끝까지 마친 뒤 commit 에서</b> 실패하게 만든다. 타이밍이 아니라 순서로 정해지는 장면이다.
     */
    @Test
    void commit_시점에_40001_이_나도_work_전체를_다시_실행한다() {
        twoOnCall();
        Timeline.reset("구현 확인 — alice 의 work 가 끝난 뒤 commit 에서 40001");
        AtomicInteger attempts = new AtomicInteger();
        AtomicInteger finishedWorks = new AtomicInteger();

        AtomicReference<Object> result = new AtomicReference<>();
        Throwable thrown = catchThrowable(() -> result.set(Tx.serializable(lab::connect, c -> {
            boolean firstAttempt = attempts.incrementAndGet() == 1;
            long onCall = countOnCall(c);
            if (onCall < 2) {
                finishedWorks.incrementAndGet();
                return false;
            }
            try (var st = c.createStatement()) {
                st.executeUpdate("UPDATE on_call SET on_call = false WHERE doctor = 'alice'");
            }
            if (firstAttempt) {
                // 같은 읽기 · 다른 행 쓰기 — 우리가 읽은 것을 바꾸고 먼저 커밋한다
                Tx.serializable(lab::connect, other -> {
                    countOnCall(other);
                    try (var st = other.createStatement()) {
                        st.executeUpdate("UPDATE on_call SET on_call = false WHERE doctor = 'bob'");
                    }
                    return null;
                });
            }
            finishedWorks.incrementAndGet();
            return true;
        })));

        assertThat(thrown)
                .as("""
                        정합성 깨짐은 아니지만 재시도가 빠졌다: commit 의 40001 이 호출자에게 그대로 샜다 (%s).
                          왜: 첫 시도의 work 는 끝까지 돌고 commit 에서 직렬화 실패가 났다 — commit 이 재시도 try 밖에 있으면 이렇게 샌다.
                          고칠 곳: Tx.serializable — c.commit() 도 SQLException 을 잡는 같은 try 안에""".formatted(thrown))
                .isNull();

        assertThat(finishedWorks.get())
                .as("work 가 끝까지 도는 시도는 두 번이어야 한다 (commit 에서 실패한 첫 시도 + 재시도)")
                .isEqualTo(2);
        assertThat(attempts.get()).as("work 는 정확히 두 번 (실패한 시도 + 재시도)").isEqualTo(2);
        assertThat(Tx.RETRIES.get()).as("commit 에서 40001 을 받아 재시도한 횟수").isEqualTo(1);
        assertThat(result.get()).as("재시도에서는 bob 이 이미 빠져 있어 '마지막 한 명이라 거절(false)'").isEqualTo(false);
        assertThat(((Number) lab.one("SELECT count(*) FROM on_call WHERE on_call")).longValue())
                .as("정합성 깨짐: 당직이 1명 이상 남아야 한다").isEqualTo(1L);
    }

    private static long countOnCall(Connection c) throws SQLException {
        try (var st = c.createStatement(); var rs = st.executeQuery("SELECT count(*) FROM on_call WHERE on_call")) {
            rs.next();
            return rs.getLong(1);
        }
    }

    @Test
    void 직렬화_실패가_계속되면_MAX_ATTEMPTS_에서_포기한다() {
        AtomicInteger runs = new AtomicInteger();
        assertThatThrownBy(() -> Tx.serializable(lab::connect, c -> {
            runs.incrementAndGet();
            throw new SQLException("가짜 직렬화 실패", "40001");
        })).isInstanceOf(IllegalStateException.class);
        assertThat(runs.get())
                .as("40001 은 다시 시도할 가치가 있다 — 단, 무한히는 아니다")
                .isEqualTo(Tx.MAX_ATTEMPTS);
    }

    @Test
    void 직렬화_실패가_아닌_오류는_다시_시도하지_않는다() {
        AtomicInteger runs = new AtomicInteger();
        assertThatThrownBy(() -> Tx.serializable(lab::connect, c -> {
            runs.incrementAndGet();
            throw new SQLException("가짜 유니크 위반", "23505");
        })).isInstanceOf(IllegalStateException.class);
        assertThat(runs.get()).as("23505 는 다시 해도 똑같다").isEqualTo(1);
    }

    /** 방법 검사 — 메서드 이름(serializable)이 약속한 대로 도는가. 결과 검사는 위의 '당직은 … 1명 이상' 이 맡는다. */
    @Test
    void 방법_검사_Tx_serializable_은_이름대로_SERIALIZABLE_로_돈다() {
        Object level = Tx.serializable(lab::connect, (Connection c) -> {
            try (var st = c.createStatement(); var rs = st.executeQuery("SHOW transaction_isolation")) {
                rs.next();
                return rs.getString(1);
            }
        });
        assertThat(level).isEqualTo("serializable");
    }

}
