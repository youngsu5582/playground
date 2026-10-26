package deepdive.c01.l06;

import java.sql.Connection;
import java.util.List;
import java.util.function.Supplier;

/** 대사(reconciliation) — 같은 사실을 두 곳에 적어 두고, 둘이 어긋난 것을 찾는다. */
public final class Reconciler {

    private final Supplier<Connection> db;

    public Reconciler(Supplier<Connection> db) {
        this.db = db;
    }

    /**
     * TODO(구현) 내부 대사(잔고 vs 원장 합)와 외부 대사(원장 vs 외부 정산 내역)의 어긋남을 전부 돌려준다.
     *
     * <h3>지금 무엇이 문제인가</h3>
     * 지금은 아무것도 찾지 못하고 빈 목록을 돌려준다. 어긋남이 있어도 "이상 없음" 으로 보인다 —
     * 대사가 가장 위험한 때는 못 찾았을 때다. {@code ReconcilerImplementTest} 가 종류별로 잡는다.
     *
     * <h3>할 일</h3>
     * <ol>
     *   <li><b>내부 대사</b> — 계좌와 "계좌별 원장 합"(<code>SELECT account_id, SUM(amount) FROM ledger GROUP BY account_id</code>)을
     *       {@code FULL OUTER JOIN}. 계좌 행이 없으면 {@link Mismatch.Kind#LEDGER_WITHOUT_ACCOUNT},
     *       잔고 ≠ 원장 합(원장이 없으면 0)이면 {@link Mismatch.Kind#BALANCE_NOT_MATCH} (예측 Q10)</li>
     *   <li><b>외부 대사</b> — 우리 거래(원장의 + 다리: {@code WHERE amount > 0})와 {@code external_statement} 를 거래 id 로
     *       {@code FULL OUTER JOIN}. 한쪽만 있으면 {@link Mismatch.Kind#OURS_ONLY} / {@link Mismatch.Kind#THEIRS_ONLY},
     *       금액이 다르면 {@link Mismatch.Kind#AMOUNT_DIFFERS}</li>
     *   <li>{@link Mismatch} 의 left · right 는 클래스 Javadoc 의 표대로</li>
     * </ol>
     *
     * <h3>헷갈리기 쉬운 곳</h3>
     * <ul>
     *   <li>{@code INNER JOIN} 은 한쪽에만 있는 행을 아예 못 본다 — 대사에서는 그 행이 바로 찾는 대상이다</li>
     *   <li>{@code SUM} 은 행이 없으면 0 이 아니라 {@code NULL} — 잔고 0 인 빈 계좌는 어긋남이 아니다. {@code COALESCE(sum, 0)}</li>
     *   <li>NULL 은 {@code <>} 로 비교되지 않는다 ({@code NULL <> 5} 는 참이 아니다) — 없는 쪽을 먼저 따로 거른다</li>
     *   <li>이 메서드는 읽기만 한다 — 어긋남을 "고치는" 건 사람이 원인을 본 뒤의 일이다</li>
     * </ul>
     */
    public List<Mismatch> findMismatches() {
        return List.of();
    }

}
