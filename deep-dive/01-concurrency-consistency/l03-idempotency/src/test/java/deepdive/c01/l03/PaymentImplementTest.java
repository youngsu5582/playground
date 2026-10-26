package deepdive.c01.l03;

import deepdive.testkit.PostgresLab;
import deepdive.testkit.Timeline;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.Callable;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.stream.IntStream;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.assertj.core.api.Assertions.catchThrowable;
import static org.assertj.core.api.Assertions.fail;

/**
 * [구현] {@link PaymentService#claim} 과 {@code replay} 를 채우면 초록이 된다. 진짜 PostgreSQL 위에서 진짜 동시성으로 돈다.
 */
@DisplayName("[구현] 01.03 PaymentService#pay — 같은 요청은 결제 한 번으로")
class PaymentImplementTest {

    static final PaymentRequest TEN_THOUSAND = new PaymentRequest("cust-1", 10_000);
    static final PaymentRequest FIFTY_THOUSAND = new PaymentRequest("cust-1", 50_000);

    final PostgresLab lab = PostgresLab.get();
    /** 외부 결제사 호출 횟수 — 이 숫자가 곧 '카드에서 실제로 돈이 나간 횟수'. */
    final AtomicInteger charges = new AtomicInteger();
    /** 처리 시간 100ms — 확인과 기록 사이의 경쟁 창을 넓힌다 (실서비스의 외부 API 지연). */
    final PaymentService service = serviceWith(() -> {
        charges.incrementAndGet();
        sleep(100);
    });

    PaymentService serviceWith(Runnable externalCharge) {
        return new PaymentService(lab::connect, externalCharge);
    }

    @BeforeEach
    void reset() {
        lab.exec(
                "DROP TABLE IF EXISTS idempotency_keys, payments",
                "CREATE TABLE idempotency_keys (key text PRIMARY KEY, request_hash text NOT NULL, status text NOT NULL, response text)",
                "CREATE TABLE payments (id bigserial PRIMARY KEY, customer_id text NOT NULL, amount bigint NOT NULL)");
    }

    static void sleep(long millis) {
        try {
            Thread.sleep(millis);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }

    long payments() {
        return ((Number) lab.one("SELECT count(*) FROM payments")).longValue();
    }

    long keyRows() {
        return ((Number) lab.one("SELECT count(*) FROM idempotency_keys")).longValue();
    }

    /** 같은 순간에 출발해서 각자의 결과(또는 예외)를 모아 온다. 30초 안에 안 끝나면 멈추지 않고 실패한다. */
    static List<Object> race(List<Callable<Object>> calls) throws Exception {
        CountDownLatch start = new CountDownLatch(1);
        // try-with-resources 를 쓰지 않는다: close() 는 DB 락에 걸린 스레드를 끝까지 기다린다 (데몬 스레드 + shutdownNow)
        ExecutorService pool = Executors.newFixedThreadPool(calls.size(), r -> {
            Thread t = new Thread(r, "race");
            t.setDaemon(true);
            return t;
        });
        try {
            List<Future<Object>> futures = new ArrayList<>();
            for (Callable<Object> call : calls) {
                futures.add(pool.submit(() -> {
                    start.await();
                    try {
                        return call.call();
                    } catch (Exception e) {
                        return e;
                    }
                }));
            }
            start.countDown();
            List<Object> results = new ArrayList<>();
            for (Future<Object> f : futures) results.add(f.get(30, TimeUnit.SECONDS));
            return results;
        } finally {
            pool.shutdownNow();
        }
    }

    static List<Callable<Object>> sameKey(PaymentService service, String key, int times) {
        return IntStream.range(0, times).<Callable<Object>>mapToObj(i -> () -> service.pay(key, TEN_THOUSAND)).toList();
    }

    @Test
    void 같은_키로_20번_동시에_호출해도_결제는_한_번이고_응답은_모두_같다() throws Exception {
        Timeline.reset("구현 확인 — 같은 키 pay-1 을 20번 동시에");
        List<Object> results = race(sameKey(service, "pay-1", 20));

        long paid = payments();
        List<Object> distinct = results.stream().distinct().toList();
        if (paid != 1 || charges.get() != 1) {
            fail("""

                    정합성 깨짐: 같은 키로 20번 호출했는데 결제가 %d건 (외부 결제 호출 %d회) 생겼다 (기대: 1건 · 1회).
                      호출들이 '키가 있나' 를 확인한 시점엔 아무도 기록을 끝내지 않아서 전부 '없음'을 보고 각자 결제했다.
                      응답 종류: %d 가지 (기대: 같은 결제 번호로 통일)
                      고칠 곳: PaymentService#claim — 확인(SELECT)과 선점(INSERT)을 한 문장으로""".formatted(paid, charges.get(), distinct.size()));
        }
        assertThat(results).as("20번 모두 예외 없이 응답을 받아야 한다").allSatisfy(r -> assertThat(r).isInstanceOf(PaymentResult.class));
        assertThat(results.stream().map(r -> ((PaymentResult) r).paymentId()).distinct().count())
                .as("모든 호출이 같은 결제 번호를 받아야 한다").isEqualTo(1);
        assertThat(results.stream().filter(r -> !((PaymentResult) r).replayed()).count())
                .as("실제로 처리한 호출은 정확히 하나, 나머지 19개는 재생(replayed)").isEqualTo(1);
    }

    @Test
    void 같은_키로_내용이_다르면_거절하고_원래_결제는_그대로다() {
        Timeline.reset("구현 확인 — 같은 키 pay-1, 1만 원 결제 뒤에 5만 원 요청");
        PaymentResult first = service.pay("pay-1", TEN_THOUSAND);

        Throwable rejected = catchThrowable(() -> service.pay("pay-1", FIFTY_THOUSAND));
        assertThat(rejected)
                .as("""

                        정합성 깨짐: 같은 멱등 키에 다른 금액(5만 원)이 왔는데 거절하지 않았다.
                          클라이언트는 5만 원 결제를 요청했는데 서버는 1만 원 결제의 응답을 '성공' 으로 돌려준 셈이다.
                          고칠 곳: PaymentService#replay — 저장된 request_hash 와 이번 요청의 hash 를 비교""")
                .isInstanceOf(IdempotencyKeyConflictException.class);
        assertThat(payments()).as("거절된 요청이 결제를 만들면 안 된다").isEqualTo(1);
        assertThat(service.pay("pay-1", TEN_THOUSAND).paymentId())
                .as("거절 뒤에도 원래 요청의 재전송은 원래 응답을 받는다").isEqualTo(first.paymentId());
    }

    @Test
    void 순차로_다시_보낸_같은_요청은_새로_처리하지_않고_같은_응답을_받는다() {
        Timeline.reset("구현 확인 — 타임아웃 뒤 재전송 (순차)");
        PaymentResult first = service.pay("pay-1", TEN_THOUSAND);
        PaymentResult retry = service.pay("pay-1", TEN_THOUSAND);

        assertThat(first.replayed()).isFalse();
        assertThat(retry.replayed()).isTrue();
        assertThat(retry.paymentId()).isEqualTo(first.paymentId());
        assertThat(charges.get()).as("재전송은 외부 결제를 다시 부르지 않는다").isEqualTo(1);
    }

    @Test
    void 첫_요청이_실패하면_같은_키로_다시_시도할_수_있다() {
        Timeline.reset("구현 확인 — 외부 결제 실패 뒤 같은 키로 재시도");
        AtomicInteger calls = new AtomicInteger();
        PaymentService flaky = serviceWith(() -> {
            if (calls.incrementAndGet() == 1) throw new IllegalStateException("외부 결제사 타임아웃");
        });

        assertThatThrownBy(() -> flaky.pay("pay-1", TEN_THOUSAND)).hasMessageContaining("타임아웃");
        assertThat(keyRows()).as("실패한 요청이 키를 붙잡고 있으면 재시도가 영영 막힌다 (키 행이 남지 않아야 한다)").isZero();

        PaymentResult retry = flaky.pay("pay-1", TEN_THOUSAND);
        assertThat(retry.replayed()).as("실패는 기록되지 않았으니 이번이 첫 처리다").isFalse();
        assertThat(payments()).isEqualTo(1);
    }

    @Test
    void 서로_다른_키는_서로를_막지_않고_각자_결제된다() throws Exception {
        Timeline.reset("구현 확인 — 서로 다른 키 10개 동시");
        List<Callable<Object>> calls = IntStream.range(0, 10)
                .<Callable<Object>>mapToObj(i -> () -> service.pay("pay-" + i, TEN_THOUSAND)).toList();
        List<Object> results = race(calls);

        assertThat(results).allSatisfy(r -> assertThat(r).isInstanceOf(PaymentResult.class));
        assertThat(payments()).as("키가 10개면 결제도 10건").isEqualTo(10);
        assertThat(charges.get()).isEqualTo(10);
    }

    @Test
    void 빈_키는_거절한다() {
        assertThatThrownBy(() -> service.pay(null, TEN_THOUSAND)).isInstanceOf(IllegalArgumentException.class);
        assertThatThrownBy(() -> service.pay("   ", TEN_THOUSAND)).isInstanceOf(IllegalArgumentException.class);
    }

    /**
     * 방법 검사 — 서버가 2대여도 막히는가. JVM 안의 락(synchronized · ConcurrentHashMap)으로 푼 해법은
     * 인스턴스가 둘이면 서로를 모르므로 여기서 빨개진다. 결과 검사는 위의 '20번 동시' 가 맡는다.
     */
    @Test
    void 방법_검사_서비스_인스턴스가_둘이어도_DB_가_중복을_막는다() throws Exception {
        Timeline.reset("구현 확인 — 서버 2대(서비스 인스턴스 2개)에서 같은 키 10번씩");
        PaymentService serverA = serviceWith(() -> {
            charges.incrementAndGet();
            sleep(100);
        });
        PaymentService serverB = serviceWith(() -> {
            charges.incrementAndGet();
            sleep(100);
        });
        List<Callable<Object>> calls = new ArrayList<>(sameKey(serverA, "pay-1", 10));
        calls.addAll(sameKey(serverB, "pay-1", 10));
        List<Object> results = race(calls);

        assertThat(results).allSatisfy(r -> assertThat(r).isInstanceOf(PaymentResult.class));
        assertThat(payments())
                .as("서버가 둘이어도 같은 키는 결제 한 번 — 멱등성의 심판은 JVM 이 아니라 DB 여야 한다")
                .isEqualTo(1);
    }
}
