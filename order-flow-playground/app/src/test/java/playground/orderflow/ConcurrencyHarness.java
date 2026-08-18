package playground.orderflow;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.concurrent.Callable;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;

/**
 * 동시성 테스트 하네스. <b>이건 보일러플레이트라 채워져 있다</b> — 드릴 대상이 아니다.
 *
 * <p>핵심은 {@link CountDownLatch} 두 개다:
 * <ul>
 *   <li>{@code start} — N개 스레드를 <b>같은 순간에</b> 풀어준다.
 *       이게 없으면 스레드가 순차 실행돼서 경쟁 상태가 재현되지 않는다.
 *       (동시성 테스트가 "통과했는데 운영에서 터지는" 가장 흔한 원인)</li>
 *   <li>{@code done} — 전원 종료를 기다린다.</li>
 * </ul>
 *
 * <p>한 번 통과했다고 안전이 증명되는 건 아니다. 경쟁 상태는 확률적이라
 * {@code repeat} 를 올려 반복 실행해야 신뢰가 생긴다.
 */
public final class ConcurrencyHarness {

    private ConcurrencyHarness() {
    }

    /** 성공/실패/예외를 모아 놓은 실행 결과. */
    public record Outcome<T>(List<T> successes, List<Throwable> failures) {

        public int successCount() {
            return successes.size();
        }

        public int failureCount() {
            return failures.size();
        }
    }

    /**
     * {@code threads} 개 스레드가 동시에 {@code task} 를 1회씩 실행한다.
     *
     * @param task 예외를 던지면 failures 에 수집된다
     */
    public static <T> Outcome<T> runConcurrently(int threads, Callable<T> task) {
        ExecutorService pool = Executors.newFixedThreadPool(threads);
        CountDownLatch start = new CountDownLatch(1);
        CountDownLatch done = new CountDownLatch(threads);
        List<T> successes = Collections.synchronizedList(new ArrayList<>());
        List<Throwable> failures = Collections.synchronizedList(new ArrayList<>());

        try {
            for (int i = 0; i < threads; i++) {
                pool.submit(() -> {
                    try {
                        start.await();            // 전원 대기 → 동시 출발
                        successes.add(task.call());
                    } catch (Throwable t) {
                        failures.add(t);
                    } finally {
                        done.countDown();
                    }
                });
            }
            start.countDown();
            if (!done.await(10, TimeUnit.SECONDS)) {
                throw new IllegalStateException("동시 실행이 10초 안에 끝나지 않았습니다 (데드락 의심)");
            }
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new IllegalStateException(e);
        } finally {
            pool.shutdownNow();
        }
        return new Outcome<>(List.copyOf(successes), List.copyOf(failures));
    }

    /**
     * 같은 시나리오를 {@code repeat} 회 반복한다.
     * 경쟁 상태는 한 번에 안 잡히므로, 최종 검증은 이걸로 한다.
     */
    public static void repeat(int times, Runnable scenario) {
        for (int i = 0; i < times; i++) {
            scenario.run();
        }
    }

    /** 호출 횟수를 세는 카운터. "생성 로직이 정확히 1회 실행됐는가" 검증용. */
    public static final class CallCounter {
        private final AtomicInteger count = new AtomicInteger();

        public int increment() {
            return count.incrementAndGet();
        }

        public int value() {
            return count.get();
        }
    }

    /** {@link Future} 결과를 예외 감싸기 없이 꺼낸다. */
    public static <T> T get(Future<T> future) {
        try {
            return future.get(5, TimeUnit.SECONDS);
        } catch (Exception e) {
            throw new IllegalStateException(e);
        }
    }
}
