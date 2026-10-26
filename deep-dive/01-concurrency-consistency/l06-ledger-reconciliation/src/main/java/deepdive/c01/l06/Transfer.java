package deepdive.c01.l06;

import java.math.BigDecimal;

/**
 * 이체 한 건. 금액은 {@link BigDecimal} — 돈을 double 로 들고 다니는 순간 센트가 새기 시작한다 (예측 Q01).
 *
 * @param txnId  거래 id — 같은 이체를 두 번 올리지 않게 하는 열쇠 (멱등키)
 * @param from   돈이 나가는 계좌 (원장에 -금액)
 * @param to     돈이 들어오는 계좌 (원장에 +금액)
 * @param amount 0 보다 큰 금액, 소수점 이하 두 자리까지
 */
public record Transfer(String txnId, int from, int to, BigDecimal amount) {

    public Transfer {
        if (from == to) throw new IllegalArgumentException("같은 계좌로는 이체하지 않는다: " + from);
        if (amount.signum() <= 0) throw new IllegalArgumentException("금액은 0 보다 커야 한다: " + amount);
        if (amount.stripTrailingZeros().scale() > 2) throw new IllegalArgumentException("소수점 이하 두 자리까지만: " + amount);
    }
}
