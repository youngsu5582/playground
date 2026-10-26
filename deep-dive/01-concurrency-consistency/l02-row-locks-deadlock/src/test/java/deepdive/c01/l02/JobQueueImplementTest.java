package deepdive.c01.l02;

import deepdive.testkit.PostgresLab;
import deepdive.testkit.Session;
import deepdive.testkit.Timeline;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.TreeMap;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.stream.Collectors;

import static deepdive.testkit.Session.Isolation.READ_COMMITTED;
import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.fail;

/**
 * [구현] {@link JobQueue#claimNext} 를 채우면 초록이 된다. 진짜 PostgreSQL 위에서 워커 스레드 여러 개가 진짜로 경쟁한다.
 * 타이밍 단언(몇 ms 안에)은 없다 — "기다리는가"만 본다.
 */
@DisplayName("[구현] 01.02 JobQueue#claimNext — 같은 작업을 둘이 집지 않기")
class JobQueueImplementTest {

    static final int WORKERS = 4;
    static final int JOBS = 40;

    final PostgresLab lab = PostgresLab.get();
    final JobQueue queue = new JobQueue(lab::connect, Duration.ofMillis(5));

    @BeforeEach
    void reset() {
        lab.exec("DROP TABLE IF EXISTS jobs",
                "CREATE TABLE jobs (id int PRIMARY KEY, status text NOT NULL DEFAULT 'pending', claimed_by text)");
    }

    void seed(int n) {
        // 역순으로 넣는다 — 물리적 저장 순서가 id 순서와 우연히 같아서 ORDER BY 가 없어도 통과하는 일을 막는다
        lab.exec("INSERT INTO jobs (id) SELECT g FROM generate_series(" + n + ", 1, -1) g");
    }

    /** 워커들이 큐가 빌 때까지 집는다. 작업 id → 그 작업을 집었다고 주장한 워커들. */
    Map<Long, List<String>> drainWithWorkers() throws Exception {
        CountDownLatch start = new CountDownLatch(1);
        try (ExecutorService pool = Executors.newFixedThreadPool(WORKERS)) {
            List<Future<List<Long>>> futures = new ArrayList<>();
            List<String> names = new ArrayList<>();
            for (int w = 1; w <= WORKERS; w++) {
                String name = "worker-" + w;
                names.add(name);
                futures.add(pool.submit(() -> {
                    start.await();
                    List<Long> mine = new ArrayList<>();
                    for (Optional<Long> job = queue.claimNext(name); job.isPresent(); job = queue.claimNext(name)) {
                        mine.add(job.get());
                    }
                    return mine;
                }));
            }
            start.countDown();
            Map<Long, List<String>> claims = new TreeMap<>();
            for (int w = 0; w < WORKERS; w++) {
                for (long id : futures.get(w).get()) claims.computeIfAbsent(id, k -> new ArrayList<>()).add(names.get(w));
            }
            return claims;
        }
    }

    @Test
    void 워커_여럿이_집어도_작업은_각각_정확히_한_번() throws Exception {
        Timeline.reset("구현 확인 — 워커 " + WORKERS + "개 × 작업 " + JOBS + "개");
        seed(JOBS);
        Map<Long, List<String>> claims = drainWithWorkers();

        Map<Long, List<String>> duplicated = new TreeMap<>();
        claims.forEach((id, who) -> { if (who.size() > 1) duplicated.put(id, who); });
        List<Long> missing = new ArrayList<>();
        for (long id = 1; id <= JOBS; id++) if (!claims.containsKey(id)) missing.add(id);

        if (!duplicated.isEmpty() || !missing.isEmpty()) {
            fail("""

                    정합성 깨짐: 중복 처리 %d건 · 누락 %d건 (규칙: 작업 하나는 정확히 한 워커만 집는다).
                      중복 (작업 → 집었다고 한 워커들): %s
                      누락: %s
                      왜: 워커들이 '첫 pending' 을 잠그지 않고 읽어서, 같은 작업을 동시에 보고 둘 다 집었다 — 읽기는 서로를 막지 않는다.
                      고칠 곳: JobQueue.claimNext 의 SELECT""".formatted(duplicated.size(), missing.size(), head(duplicated), head(missing)));
        }
        long activeWorkers = claims.values().stream().flatMap(List::stream).distinct().count();
        assertThat(activeWorkers)
                .as("""

                        정합성은 맞지만 일을 나눠 갖지 못했다: 작업을 집은 워커가 %d명뿐이다 (워커 %d개).
                          왜: 한 워커가 남은 작업을 전부 잠가 버리면(예: LIMIT 없이 잠금) 다른 워커는 집을 게 없어 빈손으로 돌아간다.
                          고칠 곳: JobQueue.claimNext 의 SELECT — 잠그는 건 지금 처리할 작업 하나만""".formatted(activeWorkers, WORKERS))
                .isGreaterThanOrEqualTo(2);
        assertThat(lab.one("SELECT count(*) FROM jobs WHERE status = 'running'")).isEqualTo((long) JOBS);
    }

    @Test
    void 큐가_비면_비어_있다고_답한다() {
        seed(1);
        assertThat(queue.claimNext("worker-1")).contains(1L);
        assertThat(queue.claimNext("worker-1")).isEmpty();
    }

    @Test
    void 집은_작업은_running_이_되고_집은_워커가_기록된다() {
        seed(3);
        long id = queue.claimNext("worker-7").orElseThrow();
        assertThat(id).as("가장 앞의 pending 부터").isEqualTo(1L);
        assertThat(lab.one("SELECT status || '/' || claimed_by FROM jobs WHERE id = " + id)).isEqualTo("running/worker-7");
        assertThat(lab.one("SELECT count(*) FROM jobs WHERE status = 'pending'")).isEqualTo(2L);
    }

    @Test
    void 남이_하나를_잡고_있어도_두_워커가_동시에_집으면_서로_다른_작업을_받는다() {
        Timeline.reset("구현 확인 — A 가 1번을 잡은 동안 워커 둘이 동시에 claimNext");
        seed(3);
        try (Session holder = lab.session("A")) {
            holder.begin(READ_COMMITTED);
            holder.query("SELECT id FROM jobs WHERE id = 1 FOR UPDATE");
            AtomicInteger n = new AtomicInteger();
            ExecutorService pool = Executors.newFixedThreadPool(2, r -> {
                Thread t = new Thread(r, "worker");
                t.setDaemon(true); // 락에 걸린 스레드가 테스트를 붙잡지 않게
                return t;
            });
            try {
                CountDownLatch start = new CountDownLatch(1);
                List<Future<Optional<Long>>> claims = new ArrayList<>();
                for (int i = 0; i < 2; i++) {
                    claims.add(pool.submit(() -> {
                        start.await();
                        return queue.claimNext("worker-" + n.incrementAndGet());
                    }));
                }
                start.countDown();
                List<Long> got = new ArrayList<>();
                try {
                    for (Future<Optional<Long>> claim : claims) awaitUnlessLockWait(claim, Duration.ofSeconds(3)).ifPresent(got::add);
                } catch (LockWait e) {
                    long lockWaiters = e.waiters;
                    holder.rollback(); // 풀어 줘야 대기 중이던 워커가 끝난다
                    throw new AssertionError("""

                            3초가 지나도 워커가 끝나지 않았다 — 엔진 기준 락을 기다리는 세션이 %s개다.
                              왜: A 가 잡은 1번 작업 때문에 기다리고 있다. 잠긴 행을 건너뛰지 않고 그 앞에 줄을 선 것이다.
                              고칠 곳: JobQueue.claimNext 의 SELECT — 잠긴 행은 건너뛰는 절(SKIP LOCKED)""".formatted(lockWaiters));
                } catch (Exception e) {
                    throw new IllegalStateException(e);
                }
                holder.rollback();
                assertThat(got)
                        .as("""

                                정합성 깨짐: 1번을 A 가 잡은 동안 두 워커가 받은 작업이 기대와 다르다 (기대: 2번과 3번 하나씩).
                                  왜: 둘이 같은 작업을 집었거나(중복), 한 워커가 남은 작업을 전부 잠가 다른 워커가 빈손이 됐다.
                                  고칠 곳: JobQueue.claimNext 의 SELECT""")
                        .containsExactlyInAnyOrder(2L, 3L);
            } finally {
                pool.shutdownNow();
            }
        }
    }

    /** 방법 검사 — SKIP LOCKED 가 약속한 동작: 남이 잡은 작업 앞에서 줄을 서지 않고 다음 것을 집는다. 결과 검사는 위의 '정확히 한 번' 이 맡는다. */
    @Test
    void 방법_검사_남이_잡고_있는_작업은_기다리지_않고_건너뛴다() {
        Timeline.reset("구현 확인 — A 가 1번을 잡고 있는 동안 워커가 claimNext");
        seed(3);
        try (Session holder = lab.session("A")) {
            holder.begin(READ_COMMITTED);
            holder.query("SELECT id FROM jobs WHERE id = 1 FOR UPDATE");
            ExecutorService pool = Executors.newSingleThreadExecutor();
            try {
                Future<Optional<Long>> claim = pool.submit(() -> queue.claimNext("worker-1"));
                Optional<Long> got;
                try {
                    got = awaitUnlessLockWait(claim, Duration.ofSeconds(1));
                } catch (LockWait e) {
                    holder.rollback(); // 풀어 줘야 대기 중이던 워커가 끝난다
                    throw new AssertionError("""

                            1초가 지나도 claimNext 가 끝나지 않았다 — 1번을 잡은 A 를 기다리고 있다.
                              왜: 워커가 잠긴 1번 앞에서 줄을 서 있다 (읽기만 해서 1번을 골랐거나, 잠그는 SELECT 가 락을 기다리거나).
                              워커는 줄을 설 게 아니라 잠긴 건 넘기고 다음 작업을 집으면 된다.
                              고칠 곳: JobQueue.claimNext 의 SELECT — 잠긴 행은 건너뛰는 절""");
                } catch (Exception e) {
                    throw new IllegalStateException(e);
                }
                assertThat(got).as("1번은 A 가 잡고 있으니 다음 pending 인 2번").contains(2L);
            } finally {
                pool.shutdownNow();
            }
            holder.rollback();
        }
    }

    /** 엔진이 "락을 기다리는 중"이라고 확인한 경우. 단순히 느린 것과 구분한다. */
    static final class LockWait extends RuntimeException {
        final long waiters;

        LockWait(long waiters) {
            super("락 대기 세션 " + waiters + "개");
            this.waiters = waiters;
        }
    }

    /**
     * grace 안에 끝나면 결과. 안 끝났을 때 엔진(pg_stat_activity)이 Lock 대기라고 하면 {@link LockWait},
     * 그냥 느린 것이면 더 기다린다 — 바쁜 머신에서 "느림"을 "대기"로 착각하지 않게 (testkit 의 isWaiting 과 같은 원칙).
     */
    <T> T awaitUnlessLockWait(Future<T> f, Duration grace) throws Exception {
        try {
            return f.get(grace.toMillis(), TimeUnit.MILLISECONDS);
        } catch (TimeoutException slow) {
            long deadline = System.nanoTime() + Duration.ofSeconds(20).toNanos();
            while (System.nanoTime() < deadline) {
                long waiters = ((Number) lab.one("SELECT count(*) FROM pg_stat_activity WHERE wait_event_type = 'Lock'")).longValue();
                if (waiters > 0) throw new LockWait(waiters);
                try {
                    return f.get(50, TimeUnit.MILLISECONDS);
                } catch (TimeoutException stillSlow) {
                    // 락 대기는 아니다 — 계속 지켜본다
                }
            }
            throw new IllegalStateException("20초 동안 끝나지도, 락을 기다리지도 않는다");
        }
    }

    /** 메시지가 수십 줄이 되지 않게 처음 5건만 보여 준다. */
    static String head(Map<Long, List<String>> m) {
        String first = m.entrySet().stream().limit(5).map(Object::toString).collect(Collectors.joining(", "));
        return m.size() > 5 ? first + " 외 " + (m.size() - 5) + "건" : first;
    }

    static String head(List<Long> l) {
        String first = l.stream().limit(5).map(String::valueOf).collect(Collectors.joining(", "));
        return l.size() > 5 ? first + " 외 " + (l.size() - 5) + "건" : first;
    }
}
