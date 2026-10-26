package deepdive.c01.l05;

import deepdive.testkit.ConcurrencyHarness;
import deepdive.testkit.PostgresLab;
import deepdive.testkit.Timeline;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Random;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.stream.IntStream;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.catchThrowable;
import static org.assertj.core.api.Assertions.fail;

/**
 * [구현] {@link EventApplier#apply} 를 채우면 초록이 된다. 진짜 PostgreSQL 위에서 진짜 동시성으로 돈다.
 */
@DisplayName("[구현] 01.05 EventApplier#apply — 중복과 역전 막기")
class EventApplierImplementTest {

    final PostgresLab lab = PostgresLab.get();
    final EventApplier applier = new EventApplier(lab::connect);

    @BeforeEach
    void reset() {
        lab.exec(
                "DROP TABLE IF EXISTS shipment, inbox",
                "CREATE TABLE shipment (id text PRIMARY KEY, version int NOT NULL, status text NOT NULL, change_count int NOT NULL)",
                "CREATE TABLE inbox (message_id text PRIMARY KEY)");
    }

    static Event v(int version) {
        return new Event("m-v" + version, "s1", version, "S" + version);
    }

    long changeCount() {
        return ((Number) lab.one("SELECT change_count FROM shipment WHERE id = 's1'")).longValue();
    }

    /** 이벤트들을 각자 다른 스레드에서, 같은 순간에 시작한다. 예외가 나면 그대로 실패시킨다. */
    List<Outcome> raceAll(List<Event> events) {
        AtomicInteger next = new AtomicInteger();
        var result = ConcurrencyHarness.runConcurrently(events.size(), () -> applier.apply(events.get(next.getAndIncrement())));
        if (!result.failures().isEmpty()) throw new IllegalStateException("동시 처리 중 예외", result.failures().getFirst());
        return result.successes();
    }

    @Test
    void 같은_messageId_가_5번_동시에_와도_한_번만_반영된다() {
        Timeline.reset("구현 확인 — 같은 messageId 5개가 동시에 도착");
        List<Event> five = Collections.nCopies(5, v(1));
        List<Outcome> outcomes = raceAll(five);
        if (changeCount() != 1) {
            fail("""

                    정합성 깨짐: 같은 메시지가 %d번 반영됐다 (기대: 1번) — 중복 처리.
                      재전달된 이벤트를 알아보지 못해서 알림 · 적립 같은 부수 효과가 그만큼 반복된다.
                      각 호출의 결과: %s
                      고칠 곳: EventApplier.apply — inbox 의 PRIMARY KEY 로 같은 messageId 를 한 번만 통과시키기""".formatted(changeCount(), outcomes));
        }
        assertThat(outcomes).containsOnlyOnce(Outcome.APPLIED).containsOnly(Outcome.APPLIED, Outcome.DUPLICATE);
    }

    @Test
    void version_1_부터_10_을_섞어_전달해도_최종은_10_이다() {
        Timeline.reset("구현 확인 — version 1..10 을 뒤섞어 순서대로(한 번에 하나씩) 전달");
        List<Event> events = new ArrayList<>(IntStream.rangeClosed(1, 10).mapToObj(EventApplierImplementTest::v).toList());
        Collections.shuffle(events, new Random(7));
        List<Integer> arrival = events.stream().map(Event::version).toList();
        events.forEach(applier::apply);
        assertFinalIs10(arrival);
    }

    @Test
    void version_1_부터_10_을_동시에_전달해도_최종은_10_이다() {
        for (int round = 1; round <= 5; round++) {
            Timeline.reset("구현 확인 " + round + "회차 — version 1..10 이 동시에 도착");
            lab.exec("DELETE FROM shipment", "DELETE FROM inbox");
            List<Event> events = new ArrayList<>(IntStream.rangeClosed(1, 10).mapToObj(EventApplierImplementTest::v).toList());
            Collections.shuffle(events, new Random(round));
            raceAll(events);
            assertFinalIs10(events.stream().map(Event::version).toList());
        }
    }

    void assertFinalIs10(List<Integer> arrival) {
        Object version = lab.one("SELECT version FROM shipment WHERE id = 's1'");
        Object status = lab.one("SELECT status FROM shipment WHERE id = 's1'");
        if (!Integer.valueOf(10).equals(version) || !"S10".equals(status)) {
            fail("""

                    정합성 깨짐: 최종 상태가 version=%s, status=%s 이다 (기대: version=10, status=S10) — 순서 역전.
                      늦게 도착한 과거 이벤트가 최신 상태를 덮어썼다.
                      도착 순서: %s
                      고칠 곳: EventApplier.apply — 저장된 version 이 이벤트의 version 보다 작을 때만 반영하기""".formatted(version, status, arrival));
        }
    }

    @Test
    void stale_로_무시된_메시지가_다시_오면_DUPLICATE_이다() {
        Timeline.reset("구현 확인 — v5 반영 → v3 는 STALE → v3 재전달");
        assertThat(applier.apply(v(5))).isEqualTo(Outcome.APPLIED);
        assertThat(applier.apply(v(3))).as("v5 가 이미 반영돼 있다 — 늦게 온 과거").isEqualTo(Outcome.STALE);
        assertThat(applier.apply(v(3)))
                .as("STALE 로 무시했어도 '처리했다' 는 기록은 남아야 한다 — 같은 메시지의 재전달은 DUPLICATE")
                .isEqualTo(Outcome.DUPLICATE);
        assertThat(lab.one("SELECT count(*) FROM inbox")).isEqualTo(2L);
        assertThat(changeCount()).as("v3 는 상태를 바꾸지 않았다").isEqualTo(1L);
    }

    /**
     * 반영 실패는 CHECK 제약으로 흉내 낸다 — 일시 장애(DB 점검 · 다운스트림 오류)의 결정적인 대역이다.
     * 제약을 풀면 "장애가 풀린 뒤 재전달" 이 된다. 예측 Q05 · Q06 과 같은 방식.
     *
     * <p>빈칸 상태(덮어쓰기 한 문장)에서도 초록이다 — 롤백할 inbox 기록이 애초에 없어서다. inbox 를 도입하면서
     * 기록을 따로 커밋하면 이 테스트가 빨개진다.
     */
    @Test
    void inbox_기록_뒤_반영_중_예외가_나면_전체_롤백되고_재전달하면_정상_반영된다() {
        Timeline.reset("구현 확인 — 반영이 실패한다 (장애) → 장애가 풀린 뒤 같은 메시지 재전달");
        Event delivered = new Event("m-d", "s1", 1, "DELIVERED");
        lab.exec("ALTER TABLE shipment ADD CONSTRAINT maintenance CHECK (status <> 'DELIVERED')");
        Throwable thrown = catchThrowable(() -> applier.apply(delivered));
        assertThat(thrown).as("반영이 실패하면 호출자에게 예외로 알려야 재전달(재시도)이 일어난다").isInstanceOf(IllegalStateException.class);
        Object recorded = lab.one("SELECT count(*) FROM inbox WHERE message_id = 'm-d'");
        if (!Long.valueOf(0).equals(recorded)) {
            fail("""

                    정합성 깨짐: 반영은 실패했는데 inbox 에는 '처리됨' 기록이 남았다.
                      재전달돼도 DUPLICATE 로 건너뛰어서, 이 이벤트는 영영 반영되지 않는다.
                      고칠 곳: EventApplier.apply — inbox 기록과 반영을 한 트랜잭션으로 묶고, 예외 때 롤백하기""");
        }
        lab.exec("ALTER TABLE shipment DROP CONSTRAINT maintenance");
        assertThat(applier.apply(delivered)).isEqualTo(Outcome.APPLIED);
        assertThat(lab.one("SELECT status FROM shipment WHERE id = 's1'")).isEqualTo("DELIVERED");
    }

    @Test
    void 같은_version_의_다른_메시지는_STALE_이고_먼저_반영된_상태가_남는다() {
        Timeline.reset("구현 확인 — (a, v5, X) 다음에 (b, v5, Y)");
        assertThat(applier.apply(new Event("a", "s1", 5, "X"))).isEqualTo(Outcome.APPLIED);
        Outcome second = applier.apply(new Event("b", "s1", 5, "Y"));
        if (second != Outcome.STALE || !"X".equals(lab.one("SELECT status FROM shipment WHERE id = 's1'"))) {
            fail("""

                    정합성 깨짐: 같은 version 의 다른 메시지가 %s 로 처리되고 상태가 %s 가 됐다 (기대: STALE, 상태 X 유지).
                      version 이 '같을 때' 도 덮어쓰면 반영이 두 번 일어나고, 어느 쪽이 이길지는 도착 순서가 정한다.
                      고칠 곳: EventApplier.apply — 저장된 version 이 이벤트 version 보다 '작을 때만' 반영하기""".formatted(
                    second, lab.one("SELECT status FROM shipment WHERE id = 's1'")));
        }
        assertThat(changeCount()).isEqualTo(1L);
    }

    /** 가드 — 막을 게 없는 정상 경로. 어떤 구현이든 초록이어야 한다 (빈칸 상태에서도). */
    @Test
    void 정상_순서로_한_번씩_오면_전부_APPLIED_이다() {
        Timeline.reset("구현 확인 — v1 → v2 → v3 정상 순서");
        List<Outcome> outcomes = IntStream.rangeClosed(1, 3).mapToObj(i -> applier.apply(v(i))).toList();
        assertThat(outcomes).containsOnly(Outcome.APPLIED);
        assertThat(changeCount()).isEqualTo(3L);
    }
}
