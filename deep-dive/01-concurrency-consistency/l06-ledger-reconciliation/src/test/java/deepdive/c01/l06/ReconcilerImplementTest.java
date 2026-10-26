package deepdive.c01.l06;

import deepdive.c01.l06.Mismatch.Kind;
import deepdive.testkit.PostgresLab;
import deepdive.testkit.Timeline;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.math.BigDecimal;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * [구현] {@link Reconciler#findMismatches} 를 채우면 초록이 된다.
 * 어긋남을 일부러 만들어 넣고(테스트가 SQL 로 직접 — {@code LedgerService} 와 무관), 종류별로 정확히 찾는지 본다.
 * "깨끗하면 빈 결과" 는 가드라 처음부터 초록이다 — 못 찾는 대사기가 아니라 <b>안 틀리는</b> 대사기를 먼저 확인한다.
 */
@DisplayName("[구현] 01.06 Reconciler#findMismatches — 어긋남을 종류별로 정확히 찾기")
class ReconcilerImplementTest {

    final PostgresLab lab = PostgresLab.get();
    final Reconciler reconciler = new Reconciler(lab::connect);

    @BeforeEach
    void reset() {
        lab.exec(LedgerSchema.DROP, LedgerSchema.sql());
    }

    static BigDecimal money(String v) {
        return new BigDecimal(v);
    }

    /** 이체 한 건을 직접 SQL 로 — 두 다리를 한 문장으로 넣고(합 0), 잔고도 맞춰 둔다. 어긋남은 이 다음에 일부러 낸다. */
    void book(String txn, int from, int to, String amount) {
        lab.exec("INSERT INTO ledger (txn_id, account_id, amount) VALUES ('%s', %d, -%s), ('%s', %d, %s)".formatted(txn, from, amount, txn, to, amount),
                "UPDATE account SET balance = balance - %s WHERE id = %d".formatted(amount, from),
                "UPDATE account SET balance = balance + %s WHERE id = %d".formatted(amount, to));
    }

    /** 깨끗한 바탕: 계좌 0(시스템) · 1 · 2 · 5(빈 계좌, 잔고 0) 와 거래 D1 · D2, 외부 내역도 같다. */
    void cleanBooks() {
        lab.exec("INSERT INTO account VALUES (0, 0), (1, 0), (2, 0), (5, 0)");
        book("D1", 0, 1, "100.00");
        book("D2", 0, 2, "40.00");
        lab.exec("INSERT INTO external_statement VALUES ('D1', 100.00), ('D2', 40.00)");
    }

    // ── 가드 ────────────────────────────────────────────────────

    @Test
    void 깨끗하면_빈_결과다() {
        cleanBooks();
        Timeline.reset("구현 확인 — 어긋남 없는 장부 (잔고 0 인 빈 계좌 5 번 포함)");
        assertThat(reconciler.findMismatches())
                .as("""

                        어긋남이 없는데 찾아냈다 — 잔고 0 인 빈 계좌(원장 행 없음)를 어긋남으로 세지 않았는지,
                        금액 0.00 과 0 을 다르게 비교하지 않는지 본다.
                          고칠 곳: Reconciler#findMismatches — COALESCE(합, 0) 와 비교""")
                .isEmpty();
    }

    // ── 결과 검사 ───────────────────────────────────────────────

    @Test
    void 잔고가_원장_합과_다른_계좌를_찾는다() {
        cleanBooks();
        lab.exec("UPDATE account SET balance = balance + 10.00 WHERE id = 2"); // 누군가 잔고만 직접 고쳤다
        Timeline.reset("구현 확인 — 계좌 2 의 잔고만 +10 (원장은 그대로)");
        assertThat(reconciler.findMismatches())
                .as("""

                        잔고 ≠ 원장 합인 계좌 2 를 정확히 하나로 찾아야 한다 (left = 잔고 50.00 · right = 원장 합 40.00).
                          고칠 곳: Reconciler#findMismatches 내부 대사 — 계좌 JOIN 계좌별 SUM(amount)""")
                .containsExactly(new Mismatch(Kind.BALANCE_NOT_MATCH, "2", money("50.00"), money("40.00")));
    }

    @Test
    void 원장이_없는_계좌와_계좌가_없는_원장을_찾는다() {
        cleanBooks();
        lab.exec("UPDATE account SET balance = 10.00 WHERE id = 5");  // 원장 한 줄 없이 잔고만 생겼다
        lab.exec("INSERT INTO ledger (txn_id, account_id, amount) VALUES ('D4', 0, -5.00), ('D4', 4, 5.00)"); // 4 번 계좌 행이 없다
        lab.exec("UPDATE account SET balance = balance - 5.00 WHERE id = 0");
        lab.exec("INSERT INTO external_statement VALUES ('D4', 5.00)");
        Timeline.reset("구현 확인 — 원장 없는 계좌 5 (잔고 10) · 계좌 없는 원장 4");
        assertThat(reconciler.findMismatches())
                .as("""

                        두 가지를 모두 찾아야 한다 — 원장이 없는 계좌 5 (left 10.00 · right 0.00), 계좌 행이 없는 원장 4 (left null · right 5.00).
                          INNER JOIN 은 한쪽에만 있는 행을 못 본다.
                          고칠 곳: Reconciler#findMismatches 내부 대사 — FULL OUTER JOIN + COALESCE""")
                .containsExactlyInAnyOrder(
                        new Mismatch(Kind.BALANCE_NOT_MATCH, "5", money("10.00"), money("0.00")),
                        new Mismatch(Kind.LEDGER_WITHOUT_ACCOUNT, "4", null, money("5.00")));
    }

    @Test
    void 외부_정산_내역과_맞춰_세_종류를_찾는다() {
        cleanBooks();
        lab.exec("UPDATE external_statement SET amount = 45.00 WHERE txn_id = 'D2'");   // 금액 다름
        lab.exec("INSERT INTO external_statement VALUES ('X9', 20.00)");                 // 저쪽에만 있음
        lab.exec("INSERT INTO account VALUES (3, 0)");
        book("D3", 0, 3, "7.50");                                                         // 우리에게만 있음 (외부 내역에 없다)
        Timeline.reset("구현 확인 — 외부 대사: D2 금액 다름 · D3 우리만 · X9 저쪽만");
        assertThat(reconciler.findMismatches())
                .as("""

                        외부 대사 세 종류를 모두 찾아야 한다 — AMOUNT_DIFFERS D2 (40.00 vs 45.00) · OURS_ONLY D3 (7.50) · THEIRS_ONLY X9 (20.00).
                          우리 거래 금액은 원장의 + 다리 금액이다.
                          고칠 곳: Reconciler#findMismatches 외부 대사 — (원장 + 다리) FULL OUTER JOIN external_statement ON txn_id""")
                .containsExactlyInAnyOrder(
                        new Mismatch(Kind.AMOUNT_DIFFERS, "D2", money("40.00"), money("45.00")),
                        new Mismatch(Kind.OURS_ONLY, "D3", money("7.50"), null),
                        new Mismatch(Kind.THEIRS_ONLY, "X9", null, money("20.00")));
    }

    @Test
    void 어긋남이_섞여_있어도_종류별로_정확히_찾는다() {
        cleanBooks();
        lab.exec("UPDATE account SET balance = balance + 10.00 WHERE id = 2");        // 잔고만 고침
        lab.exec("UPDATE account SET balance = 3.00 WHERE id = 5");                    // 원장 없는 계좌
        book("D3", 0, 2, "1.00");                                                      // 외부 내역에 없는 거래
        lab.exec("INSERT INTO external_statement VALUES ('X9', 20.00)");              // 우리에게 없는 거래
        lab.exec("UPDATE external_statement SET amount = 99.00 WHERE txn_id = 'D1'"); // 금액이 다른 거래
        Timeline.reset("구현 확인 — 어긋남 다섯 개가 섞여 있다");
        List<Mismatch> found = reconciler.findMismatches();
        assertThat(found)
                .as("""

                        어긋남 다섯 개를 하나도 빠뜨리거나 더하지 않고 찾아야 한다 (깨끗한 계좌 0 · 1 · D1 의 잔고 쪽은 안 나와야 한다).
                          고칠 곳: Reconciler#findMismatches — 내부 대사 + 외부 대사의 결과를 합친다""")
                .containsExactlyInAnyOrder(
                        new Mismatch(Kind.BALANCE_NOT_MATCH, "2", money("51.00"), money("41.00")),
                        new Mismatch(Kind.BALANCE_NOT_MATCH, "5", money("3.00"), money("0.00")),
                        new Mismatch(Kind.OURS_ONLY, "D3", money("1.00"), null),
                        new Mismatch(Kind.THEIRS_ONLY, "X9", null, money("20.00")),
                        new Mismatch(Kind.AMOUNT_DIFFERS, "D1", money("100.00"), money("99.00")));
    }
}
