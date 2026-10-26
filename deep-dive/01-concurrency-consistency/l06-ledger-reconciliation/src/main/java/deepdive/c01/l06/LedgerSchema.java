package deepdive.c01.l06;

import java.io.IOException;
import java.io.InputStream;
import java.io.UncheckedIOException;
import java.nio.charset.StandardCharsets;

/** 이 레슨의 테이블 · 제약 · 트리거. 정의는 {@code src/main/resources/ledger-schema.sql} — observe 도 같은 파일을 쓴다. */
public final class LedgerSchema {

    /** 테스트마다 깨끗하게 시작할 때 먼저 실행한다. */
    public static final String DROP =
            "DROP TABLE IF EXISTS account, posted_txn, ledger, external_statement, money_box CASCADE";

    private LedgerSchema() {}

    /** 테이블 · 함수 · 트리거를 만드는 SQL 전체 (한 번에 실행해도 된다). */
    public static String sql() {
        try (InputStream in = LedgerSchema.class.getResourceAsStream("/ledger-schema.sql")) {
            if (in == null) throw new IllegalStateException("ledger-schema.sql 을 찾을 수 없다");
            return new String(in.readAllBytes(), StandardCharsets.UTF_8);
        } catch (IOException e) {
            throw new UncheckedIOException(e);
        }
    }
}
