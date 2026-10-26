-- 01.06 원장과 대사 — 스키마 (테스트 · observe 가 같이 쓴다)
--
-- account    잔고. 0 번은 시스템 계정 — 바깥에서 돈이 들어오고 나가는 상대편이라 마이너스가 될 수 있다
-- ledger     원장. 거래 내역을 쌓기만 한다 (append-only). amount 는 잔고에 더해지는 값(+ 입금 · - 출금)
-- posted_txn 이미 반영한 거래 id (멱등 선점)
-- external_statement  외부(상대 시스템)가 보내 준 정산 내역 — 외부 대사의 상대편

CREATE TABLE account (
    id      int PRIMARY KEY,
    balance numeric(20,2) NOT NULL CHECK (balance >= 0 OR id = 0)
);

CREATE TABLE posted_txn (
    txn_id text PRIMARY KEY
);

CREATE TABLE ledger (
    entry_id   bigserial PRIMARY KEY,
    txn_id     text NOT NULL,
    account_id int NOT NULL,
    amount     numeric(20,2) NOT NULL,
    UNIQUE (txn_id, account_id)
);

CREATE TABLE external_statement (
    txn_id text PRIMARY KEY,
    amount numeric(20,2) NOT NULL
);

-- 규칙 1: 한 거래의 다리(원장 행) 합은 0 이다. 문장마다가 아니라 커밋 때 검사한다 (DEFERRABLE INITIALLY DEFERRED).
CREATE OR REPLACE FUNCTION ledger_txn_must_net_zero() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    legs_sum numeric;
BEGIN
    SELECT sum(amount) INTO legs_sum FROM ledger WHERE txn_id = NEW.txn_id;
    IF legs_sum <> 0 THEN
        RAISE EXCEPTION '거래 % 의 다리 합이 0 이 아니다: %', NEW.txn_id, legs_sum;
    END IF;
    RETURN NULL;
END
$$;

CREATE CONSTRAINT TRIGGER ledger_txn_net_zero
    AFTER INSERT ON ledger
    DEFERRABLE INITIALLY DEFERRED
    FOR EACH ROW EXECUTE FUNCTION ledger_txn_must_net_zero();

-- 규칙 2: 원장은 쌓기만 한다 — 고치거나 지우지 못한다 (고칠 땐 반대 방향 거래를 새로 쌓는다).
CREATE OR REPLACE FUNCTION ledger_append_only() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION '원장은 고치거나 지울 수 없다 (% 시도)', TG_OP;
END
$$;

CREATE TRIGGER ledger_no_update_delete
    BEFORE UPDATE OR DELETE ON ledger
    FOR EACH ROW EXECUTE FUNCTION ledger_append_only();
