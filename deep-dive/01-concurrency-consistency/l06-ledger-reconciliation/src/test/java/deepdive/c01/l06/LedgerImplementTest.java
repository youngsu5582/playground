package deepdive.c01.l06;

import deepdive.testkit.ConcurrencyHarness;
import deepdive.testkit.ConcurrencyHarness.Outcome;
import deepdive.testkit.PostgresLab;
import deepdive.testkit.SqlFailure;
import deepdive.testkit.Timeline;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.math.BigDecimal;
import java.sql.Connection;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.concurrent.atomic.AtomicInteger;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.fail;

/**
 * [구현] {@link LedgerService#post} 를 채우면 초록이 된다. 진짜 PostgreSQL 위에서 진짜 동시성으로 돈다.
 * 결과 검사: 같은 거래 두 번 · 같은 거래 동시에 · 동시 이체 뒤 잔고 = 원장 합 / 가드: 이체 반영 · 잔고 부족 / 방법 검사: 큰 금액.
 * 이 테스트는 {@code Reconciler} 를 쓰지 않는다 — 원장 검증은 아래 SQL 로 따로 한다.
 */
@DisplayName("[구현] 01.06 LedgerService#post — 같은 거래는 한 번만 · 동시 이체 뒤에도 잔고 = 원장 합")
class LedgerImplementTest {

    static final int ACCOUNTS = 4;
    static final int TRANSFERS = 24;
    static final int ROUNDS = 3;

    final PostgresLab lab = PostgresLab.get();

    @BeforeEach
    void reset() {
        lab.exec(LedgerSchema.DROP, LedgerSchema.sql());
    }

    /** 계좌 1~4 에 1000.00 씩 — 시스템 계정 0 에서 들어온 것으로 원장에도 남긴다 (그래서 처음부터 잔고 = 원장 합). */
    void openAccounts() {
        lab.exec("INSERT INTO account VALUES (0, -4000.00), (1, 1000.00), (2, 1000.00), (3, 1000.00), (4, 1000.00)",
                "INSERT INTO ledger (txn_id, account_id, amount) VALUES "
                        + "('OPEN-1', 0, -1000.00), ('OPEN-1', 1, 1000.00), ('OPEN-2', 0, -1000.00), ('OPEN-2', 2, 1000.00), "
                        + "('OPEN-3', 0, -1000.00), ('OPEN-3', 3, 1000.00), ('OPEN-4', 0, -1000.00), ('OPEN-4', 4, 1000.00)");
    }

    BigDecimal balanceOf(int account) {
        return (BigDecimal) lab.one("SELECT balance FROM account WHERE id = " + account);
    }

    long legsOf(String txnId) {
        return ((Number) lab.one("SELECT count(*) FROM ledger WHERE txn_id = '" + txnId + "'")).longValue();
    }

    /** 계좌별 (잔고, 원장 합). */
    Map<Integer, BigDecimal[]> balanceAndLedger() {
        Map<Integer, BigDecimal[]> result = new LinkedHashMap<>();
        try (Connection c = lab.connect(); Statement st = c.createStatement();
             ResultSet rs = st.executeQuery("""
                     SELECT a.id, a.balance, COALESCE((SELECT SUM(amount) FROM ledger l WHERE l.account_id = a.id), 0)
                     FROM account a ORDER BY a.id""")) {
            while (rs.next()) result.put(rs.getInt(1), new BigDecimal[]{rs.getBigDecimal(2), rs.getBigDecimal(3)});
        } catch (SQLException e) {
            throw new IllegalStateException(e);
        }
        return result;
    }

    // ── 가드: 빈칸 상태에서도 초록이어야 한다 ─────────────────────

    @Test
    void 이체_한_건은_양쪽_잔고와_원장에_반영된다() {
        openAccounts();
        Timeline.reset("구현 확인 — 이체 한 건 (1 → 2 · 250.75)");
        PostResult result = new LedgerService(lab::connect).post(new Transfer("T1", 1, 2, new BigDecimal("250.75")));
        assertThat(result).isEqualTo(PostResult.POSTED);
        assertThat(balanceOf(1)).isEqualByComparingTo("749.25");
        assertThat(balanceOf(2)).isEqualByComparingTo("1250.75");
        assertThat(legsOf("T1")).as("원장에는 두 줄 (차변 · 대변)").isEqualTo(2);
        assertThat(lab.one("SELECT amount FROM ledger WHERE txn_id = 'T1' AND account_id = 1")).isEqualTo(new BigDecimal("-250.75"));
        assertThat(lab.one("SELECT amount FROM ledger WHERE txn_id = 'T1' AND account_id = 2")).isEqualTo(new BigDecimal("250.75"));
    }

    @Test
    void 잔고가_모자라면_거절하고_아무_흔적도_남기지_않는다() {
        openAccounts();
        LedgerService service = new LedgerService(lab::connect);
        Timeline.reset("구현 확인 — 잔고 1000 에서 1500 을 보내면");
        PostResult first = service.post(new Transfer("T-BIG", 1, 2, new BigDecimal("1500.00")));
        assertThat(first).as("잔고 부족은 INSUFFICIENT").isEqualTo(PostResult.INSUFFICIENT);
        assertThat(balanceOf(1)).as("거절했으면 잔고는 그대로").isEqualByComparingTo("1000.00");
        assertThat(balanceOf(2)).isEqualByComparingTo("1000.00");
        assertThat(legsOf("T-BIG")).as("거절했으면 원장에도 흔적이 없다").isZero();

        lab.exec("UPDATE account SET balance = 2000.00 WHERE id = 1"); // 입금된 셈 (원장 합은 이 테스트에서 안 본다)
        Timeline.reset("구현 확인 — 입금된 뒤 같은 거래 id 로 다시");
        assertThat(service.post(new Transfer("T-BIG", 1, 2, new BigDecimal("1500.00"))))
                .as("""

                        거절된 거래가 '이미 반영됨' 으로 남았다 — 같은 거래 id 로 다시 시도하면 DUPLICATE 가 나온다.
                          고칠 곳: LedgerService#post — 잔고 부족이면 멱등 선점(posted_txn)도 같이 롤백""")
                .isEqualTo(PostResult.POSTED);
    }

    // ── 결과 검사 ───────────────────────────────────────────────

    @Test
    void 같은_거래를_두_번_올리면_한_번만_반영된다() {
        openAccounts();
        LedgerService service = new LedgerService(lab::connect);
        Timeline.reset("구현 확인 — 같은 거래 id T1 을 두 번");
        Transfer t = new Transfer("T1", 1, 2, new BigDecimal("100.00"));
        assertThat(service.post(t)).isEqualTo(PostResult.POSTED);
        PostResult second = service.post(t);
        assertThat(balanceOf(1))
                .as("""

                        정합성 깨짐: 같은 거래 T1 이 두 번 반영됐다 (계좌 1 잔고 900 이어야 하는데 이 값).
                          두 번째 시도는 오류가 아니라 DUPLICATE 여야 한다 (아무것도 하지 않는다).
                          고칠 곳: LedgerService#post — 맨 앞에서 posted_txn 에 INSERT … ON CONFLICT DO NOTHING 하고 영향 행 수로 판단""")
                .isEqualByComparingTo("900.00");
        assertThat(second).isEqualTo(PostResult.DUPLICATE);
        assertThat(legsOf("T1")).as("원장도 두 줄 그대로").isEqualTo(2);
    }

    @Test
    void 같은_거래를_동시에_올려도_한_번만_반영된다() {
        for (int round = 1; round <= ROUNDS; round++) {
            reset();
            openAccounts();
            Timeline.reset("구현 확인 같은 거래 동시에 " + round + "회차 — 8 스레드가 T1 을 같이 올린다");
            LedgerService service = new LedgerService(lab::connect);
            Transfer t = new Transfer("T1", 1, 2, new BigDecimal("100.00"));
            Outcome<PostResult> outcome = ConcurrencyHarness.runConcurrently(8, () -> service.post(t));
            failIfException(round, outcome);
            long posted = outcome.successes().stream().filter(r -> r == PostResult.POSTED).count();
            long duplicate = outcome.successes().stream().filter(r -> r == PostResult.DUPLICATE).count();
            if (posted != 1 || duplicate != 7 || balanceOf(1).compareTo(new BigDecimal("900.00")) != 0) {
                fail("""

                        정합성 깨짐: %d회차 — 같은 거래 T1 을 8 번 동시에 올렸더니 반영 %d번 · 중복 %d번 · 계좌 1 잔고 %s (기대: 1번 · 7번 · 900.00).
                          '있나 확인하고 넣기' 는 동시에 오면 둘 다 "없네" 를 본다 (01.03).
                          고칠 곳: LedgerService#post — 확인과 선점을 INSERT … ON CONFLICT DO NOTHING 한 문장으로""".formatted(
                        round, posted, duplicate, balanceOf(1)));
            }
        }
    }

    @Test
    void 동시_이체_뒤에도_모든_계좌의_잔고는_원장_합이고_전체_합은_보존된다() {
        for (int round = 1; round <= ROUNDS; round++) {
            reset();
            openAccounts();
            Timeline.reset("구현 확인 동시 이체 " + round + "회차 — 계좌 4 개 사이 " + TRANSFERS + " 건을 같은 순간에");
            LedgerService service = new LedgerService(lab::connect);
            AtomicInteger next = new AtomicInteger();
            Outcome<PostResult> outcome = ConcurrencyHarness.runConcurrently(TRANSFERS, () -> service.post(transfer(next.getAndIncrement())));
            failIfException(round, outcome);

            long posted = outcome.successes().stream().filter(r -> r == PostResult.POSTED).count();
            if (posted != TRANSFERS) {
                fail("""

                        정합성 깨짐: %d회차 — %d건 중 %d건만 반영됐다 (잔고가 충분한데 거절했다).
                          고칠 곳: LedgerService#post — 잔고 부족(INSUFFICIENT)은 CHECK 가 거절했을 때만""".formatted(round, TRANSFERS, posted));
            }
            for (var entry : balanceAndLedger().entrySet()) {
                BigDecimal balance = entry.getValue()[0];
                BigDecimal ledgerSum = entry.getValue()[1];
                if (balance.compareTo(ledgerSum) != 0) {
                    fail("""

                            정합성 깨짐: %d회차 — 계좌 %d 의 잔고 %s ≠ 원장 합 %s (대사가 이 어긋남을 찾아야 하는 상황).
                              여러 이체가 같은 잔고를 읽고 각자 계산해 덮어쓰면 서로의 변경이 사라진다 (01.04 갱신 손실).
                              고칠 곳: LedgerService#post — 잔고를 앱에서 계산하지 말고 UPDATE … SET balance = balance + ? 로""".formatted(
                            round, entry.getKey(), balance, ledgerSum));
                }
            }
            assertThat((BigDecimal) lab.one("SELECT SUM(balance) FROM account"))
                    .as("정합성 깨짐: 전체 잔고 합이 변했다 — 이체는 돈을 만들지도 없애지도 않는다")
                    .isEqualByComparingTo("0.00");
            assertThat(lab.one("SELECT count(*) FROM ledger"))
                    .as("원장 줄 수: 개설 8 + 이체 %d × 2".formatted(TRANSFERS))
                    .isEqualTo(8L + 2L * TRANSFERS);
        }
    }

    /** i 번째 이체 — 계좌 1~4 사이를 오가는 정해진 패턴 (반대 방향 쌍이 섞인다). 금액은 센트 단위. */
    static Transfer transfer(int i) {
        int from = i % ACCOUNTS + 1;
        int to = (from + (i / ACCOUNTS) % 3) % ACCOUNTS + 1;
        return new Transfer("T-%02d".formatted(i), from, to, BigDecimal.valueOf(1000 + 37L * i, 2));
    }

    static void failIfException(int round, Outcome<PostResult> outcome) {
        if (outcome.failures().isEmpty()) return;
        Throwable first = outcome.failures().getFirst();
        String hint = "40P01".equals(SqlFailure.stateOf(first))
                ? "데드락(40P01): 서로 반대 방향 이체가 두 계좌의 락을 엇갈려 잡았다 — 두 계좌를 항상 같은 순서(id 순)로 갱신한다 (01.02)"
                : "예외 원인을 확인한다";
        fail("""

                예외가 났다: %d회차 — %d건 실패. 첫 번째: %s
                  고칠 곳: LedgerService#post — %s""".formatted(round, outcome.failures().size(), first, hint));
    }

    // ── 방법 검사 ───────────────────────────────────────────────

    /** 방법 검사 — 금액을 double 로 다루면 큰 금액에서 센트가 사라진다. 결과 검사는 위의 동시 이체 테스트가 맡는다. */
    @Test
    void 방법_검사_금액을_double_로_다루면_큰_금액에서_센트가_깨진다() {
        BigDecimal start = new BigDecimal("20000000000000000.00");   // 2 * 10^16
        BigDecimal amount = new BigDecimal("12345678901234567.89");  // double 은 유효숫자 15~17 자리까지만 정확하다
        lab.exec("INSERT INTO account VALUES (1, 20000000000000000.00), (2, 0.01)");
        Timeline.reset("구현 확인 — 12345678901234567.89 이체 (double 이면 센트가 깨진다)");
        new LedgerService(lab::connect).post(new Transfer("BIG-1", 1, 2, amount));
        assertThat(balanceOf(1))
                .as("""

                        정합성 깨짐: 보내는 계좌 잔고가 %s 이어야 하는데 이 값이다 — 금액이 double 을 거치며 하위 자릿수가 사라졌다.
                          double 은 유효숫자 15~17 자리라 17 자리 금액에서 센트를 못 담는다 (예측 Q01).
                          고칠 곳: LedgerService#post — 잔고 계산을 DB(numeric)에 맡기고 금액은 BigDecimal 로만 주고받는다""".formatted(start.subtract(amount)))
                .isEqualByComparingTo(start.subtract(amount));
        assertThat(balanceOf(2)).as("받는 계좌 잔고").isEqualByComparingTo(amount.add(new BigDecimal("0.01")));
        assertThat(lab.one("SELECT amount FROM ledger WHERE txn_id = 'BIG-1' AND account_id = 2")).isEqualTo(amount);
    }
}
