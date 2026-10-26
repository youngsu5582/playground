package deepdive.c01.l02;

import deepdive.testkit.PostgresLab;
import deepdive.testkit.SqlFailure;
import deepdive.testkit.Timeline;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.fail;

/**
 * [구현] {@link TransferService#transfer} 를 채우면 초록이 된다. 서로 반대 방향 이체를 진짜 스레드로 동시에 돌린다.
 * 데드락이 나면 엔진이 40P01 로 한쪽을 끊는다 — 이 테스트는 그게 호출자에게 새는 것을 센다.
 */
@DisplayName("[구현] 01.02 TransferService#transfer — 반대 방향 이체가 데드락 없이 돌기")
class TransferImplementTest {

    static final int ITERATIONS = 10;

    final PostgresLab lab = PostgresLab.get();
    final TransferService service = new TransferService(lab::connect, Duration.ofMillis(10));

    @BeforeEach
    void reset() {
        lab.exec("DROP TABLE IF EXISTS account",
                "CREATE TABLE account (id int PRIMARY KEY, balance bigint NOT NULL CHECK (balance >= 0))",
                "INSERT INTO account VALUES (1, 1000), (2, 1000)");
    }

    /** 스레드마다 (from, to) 하나를 ITERATIONS 번 반복. 실패한 호출의 SQLState 를 모아 돌려준다. */
    List<String> race(long[][] directions) throws Exception {
        CountDownLatch start = new CountDownLatch(1);
        try (ExecutorService pool = Executors.newFixedThreadPool(directions.length)) {
            List<Future<List<String>>> futures = new ArrayList<>();
            for (long[] d : directions) {
                futures.add(pool.submit(() -> {
                    start.await();
                    List<String> failures = new ArrayList<>();
                    for (int i = 0; i < ITERATIONS; i++) {
                        try {
                            service.transfer(d[0], d[1], 1);
                        } catch (RuntimeException e) {
                            failures.add(String.valueOf(SqlFailure.stateOf(e)));
                        }
                    }
                    return failures;
                }));
            }
            start.countDown();
            List<String> all = new ArrayList<>();
            for (Future<List<String>> f : futures) all.addAll(f.get());
            return all;
        }
    }

    long totalBalance() {
        return ((Number) lab.one("SELECT sum(balance) FROM account")).longValue();
    }

    @Test
    void 반대_방향_이체를_동시에_돌려도_데드락이_나지_않고_잔고_합이_보존된다() throws Exception {
        Timeline.reset("구현 확인 — 1→2 두 스레드 · 2→1 두 스레드, 각 " + ITERATIONS + "번");
        List<String> failures = race(new long[][] {{1, 2}, {2, 1}, {1, 2}, {2, 1}});

        long deadlocks = failures.stream().filter("40P01"::equals).count();
        if (deadlocks > 0) {
            fail("""

                    정합성 깨짐이 아니라 가용성 깨짐: 이체 %d건이 데드락(40P01)으로 끊겼다 (전체 시도 %d건).
                      왜: 1→2 이체는 1번을 잡고 2번을, 2→1 이체는 2번을 잡고 1번을 기다렸다 — 서로의 행을 기다리는 순환.
                      엔진이 한쪽을 끊어 합계는 지켜졌어도, 끊긴 이체는 호출자에게 에러로 샌다.
                      고칠 곳: TransferService.transfer — 방향이 아니라 행을 기준으로 항상 같은 순서로 잠근다""".formatted(deadlocks, 4 * ITERATIONS));
        }
        assertThat(failures).as("데드락 말고 다른 실패도 없어야 한다").isEmpty();
        assertThat(totalBalance()).as("잔고 합 보존").isEqualTo(2000L);
        assertThat(lab.one("SELECT count(*) FROM account WHERE balance < 0")).as("음수 잔고").isEqualTo(0L);
        assertThat(lab.one("SELECT balance FROM account WHERE id = 1")).as("같은 횟수씩 오갔으니 원래대로").isEqualTo(1000L);
    }

    /** 결과 검사 — 예방은 "데드락이 0회" 다. 40P01 을 받아 재시도로 가려도 엔진은 데드락을 센다. */
    @Test
    void 반대_방향_이체를_동시에_돌려도_엔진이_감지한_데드락은_0회() throws Exception {
        Timeline.reset("구현 확인 — 엔진의 데드락 카운터(pg_stat_database.deadlocks) 전후");
        long before = deadlockCount();
        race(new long[][] {{1, 2}, {2, 1}, {1, 2}, {2, 1}});
        Thread.sleep(1500); // 통계는 백그라운드로 반영된다 (갱신 간격 1초)
        long detected = deadlockCount() - before;
        assertThat(detected).as("""

                가용성 깨짐: 엔진이 데드락을 %d회 감지했다 (규칙: 예방 — 감지될 일 자체가 없어야 한다).
                  왜: 40P01 을 잡아 재시도하면 호출자에게는 안 보여도 데드락은 일어났고, 끊긴 이체는 일을 두 번 했다.
                  고칠 곳: TransferService.transfer — 방향이 아니라 행을 기준으로 항상 같은 순서로 잠근다""".formatted(detected)).isZero();
    }

    long deadlockCount() {
        return ((Number) lab.one("SELECT deadlocks FROM pg_stat_database WHERE datname = current_database()")).longValue();
    }

    @Test
    void 한_방향으로만_몰려도_합이_보존된다() throws Exception {
        Timeline.reset("구현 확인 — 1→2 네 스레드");
        List<String> failures = race(new long[][] {{1, 2}, {1, 2}, {1, 2}, {1, 2}});

        assertThat(failures).as("같은 방향은 락 순서가 같으니 순환이 없다 — 이 테스트는 처음부터 초록이어야 한다").isEmpty();
        assertThat(totalBalance()).isEqualTo(2000L);
        assertThat(lab.one("SELECT balance FROM account WHERE id = 1")).isEqualTo(1000L - 4 * ITERATIONS);
    }

    @Test
    void 잔고가_모자라면_거절하고_아무것도_바꾸지_않는다() {
        assertThat(service.transfer(1, 2, 1001)).as("1번 잔고는 1000").isFalse();
        assertThat(lab.one("SELECT balance FROM account WHERE id = 1")).isEqualTo(1000L);
        assertThat(lab.one("SELECT balance FROM account WHERE id = 2")).isEqualTo(1000L);
        assertThat(service.transfer(1, 2, 1000)).isTrue();
        assertThat(lab.one("SELECT balance FROM account WHERE id = 1")).isEqualTo(0L);
    }
}
