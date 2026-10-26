package deepdive.testkit;

import java.time.Duration;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.concurrent.Callable;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

/**
 * N 개 스레드를 <b>같은 순간에</b> 풀어 주는 동시성 하네스.
 *
 * <p>출발선 래치({@code start}) 가 없으면 스레드가 순차로 돌아 경쟁이 재현되지 않는다 — 동시성 테스트가
 * "통과했는데 운영에서 터지는" 가장 흔한 원인이다. 경쟁은 확률적이라 한 번 통과로는 증명되지 않는다 → 호출하는 쪽에서 여러 번 돈다.
 */
public final class ConcurrencyHarness {

    /** 이 시간 안에 전원이 끝나지 않으면 데드락·무한 대기로 보고 실패시킨다 (테스트가 멈추는 대신 빨개지게). */
    public static final Duration TIMEOUT = Duration.ofSeconds(30);

    private ConcurrencyHarness() {}

    /** @param successes 정상 반환값 (순서 무관) · @param failures 던져진 예외 · @param elapsed 출발 신호부터 전원 종료까지 */
    public record Outcome<T>(List<T> successes, List<Throwable> failures, Duration elapsed) {}

    /** {@code threads} 개 스레드가 동시에 {@code task} 를 1회씩 실행한다. 예외는 failures 로 모은다. */
    public static <T> Outcome<T> runConcurrently(int threads, Callable<T> task) {
        CountDownLatch start = new CountDownLatch(1);
        CountDownLatch done = new CountDownLatch(threads);
        List<T> successes = Collections.synchronizedList(new ArrayList<>());
        List<Throwable> failures = Collections.synchronizedList(new ArrayList<>());
        // try-with-resources 를 쓰지 않는다: close() 는 작업이 끝날 때까지 기다리는데, DB 락에 걸린 스레드는
        // 인터럽트로도 깨지 않아 테스트가 영원히 멈춘다. 데몬 스레드로 만들고, 끝나면 shutdownNow 만 한다.
        ExecutorService pool = Executors.newFixedThreadPool(threads, r -> {
            Thread t = new Thread(r, "harness");
            t.setDaemon(true);
            return t;
        });
        try {
            for (int i = 0; i < threads; i++) {
                pool.submit(() -> {
                    try {
                        start.await();
                        successes.add(task.call());
                    } catch (Throwable t) {
                        failures.add(t);
                    } finally {
                        done.countDown();
                    }
                });
            }
            long t0 = System.nanoTime();
            start.countDown();
            if (!done.await(TIMEOUT.toSeconds(), TimeUnit.SECONDS)) {
                throw new IllegalStateException("동시 실행이 " + TIMEOUT.toSeconds() + "초 안에 끝나지 않았다 — 데드락 · 무한 락 대기 의심 ("
                        + done.getCount() + "개 스레드가 아직 안 끝남)");
            }
            return new Outcome<>(List.copyOf(successes), List.copyOf(failures), Duration.ofNanos(System.nanoTime() - t0));
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new IllegalStateException(e);
        } finally {
            pool.shutdownNow();
        }
    }
}
