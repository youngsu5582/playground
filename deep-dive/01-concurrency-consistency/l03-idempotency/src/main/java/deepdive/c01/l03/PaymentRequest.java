package deepdive.c01.l03;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import java.util.Objects;

/**
 * 결제 요청 (클라이언트가 보내는 것).
 *
 * <p>{@link #fingerprint()} 가 "같은 요청"의 기준이다 — 멱등 키가 같아도 지문이 다르면 다른 요청이다.
 * 여기서는 고객과 금액만 본다. 무엇을 같다고 볼지는 비즈니스 결정이다 (NOTES 꼬리질문 4).
 */
public record PaymentRequest(String customerId, long amount) {

    public PaymentRequest {
        Objects.requireNonNull(customerId, "customerId");
        if (amount <= 0) throw new IllegalArgumentException("amount must be positive: " + amount);
    }

    /** 요청 내용의 SHA-256 (hex). idempotency_keys.request_hash 에 저장한다. */
    public String fingerprint() {
        try {
            byte[] digest = MessageDigest.getInstance("SHA-256")
                    .digest((customerId + "|" + amount).getBytes(StandardCharsets.UTF_8));
            return HexFormat.of().formatHex(digest);
        } catch (NoSuchAlgorithmException e) {
            throw new IllegalStateException(e); // SHA-256 은 모든 JVM 이 가진다
        }
    }
}
