package deepdive.c01.l06;

import java.math.BigDecimal;
import java.math.RoundingMode;

/**
 * 대사가 찾아낸 어긋남 한 건.
 *
 * <pre>
 * 종류                  key        left               right
 * BALANCE_NOT_MATCH     계좌 id    계좌 잔고          원장 합 (원장이 없으면 0)
 * LEDGER_WITHOUT_ACCOUNT 계좌 id   null               원장 합
 * OURS_ONLY             거래 id    우리 거래 금액     null
 * THEIRS_ONLY           거래 id    null               외부 내역 금액
 * AMOUNT_DIFFERS        거래 id    우리 거래 금액     외부 내역 금액
 * </pre>
 * 금액은 소수점 두 자리로 맞춰 비교한다 (0 과 0.00 이 다른 값으로 보이지 않게).
 * "우리 거래 금액" 은 그 거래의 원장 중 + 다리의 금액이다.
 */
public record Mismatch(Kind kind, String key, BigDecimal left, BigDecimal right) {

    public enum Kind {
        /** 계좌 잔고 ≠ 그 계좌의 원장 합 (원장 행이 하나도 없는 계좌는 합을 0 으로 본다) */
        BALANCE_NOT_MATCH,
        /** 원장에는 있는데 계좌 행이 없다 (합이 0 이어도 어긋남이다) */
        LEDGER_WITHOUT_ACCOUNT,
        /** 우리 원장에만 있는 거래 (외부 내역에 없다) */
        OURS_ONLY,
        /** 외부 내역에만 있는 거래 (우리 원장에 없다) */
        THEIRS_ONLY,
        /** 양쪽에 있지만 금액이 다르다 */
        AMOUNT_DIFFERS
    }

    public Mismatch {
        left = scaled(left);
        right = scaled(right);
    }

    private static BigDecimal scaled(BigDecimal v) {
        return v == null ? null : v.setScale(2, RoundingMode.HALF_UP);
    }
}
