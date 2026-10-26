-- 스키마는 ../src/main/resources/ledger-schema.sql (01-schema.sql 로 먼저 실행된다).
-- 여기는 일부러 어긋나게 만든 데이터 — 대사 쿼리가 무엇을 찾는지 보려고.

-- 계좌: 3 번은 원장에 한 줄도 없다 · 4 번 계좌는 아예 없다 · 2 번은 잔고와 원장 합이 다르다
INSERT INTO account VALUES (0, -145.00), (1, 100.00), (2, 50.00), (3, 10.00), (5, 0.00);

-- 원장: 거래마다 두 다리의 합이 0. 한 문장으로 넣는다 (지연 제약은 문장이 아니라 커밋 때 본다)
INSERT INTO ledger (txn_id, account_id, amount) VALUES
    ('D1', 0, -100.00), ('D1', 1, 100.00),
    ('D2', 0,  -40.00), ('D2', 2,  40.00),
    ('D4', 0,   -5.00), ('D4', 4,   5.00);

INSERT INTO posted_txn VALUES ('D1'), ('D2'), ('D4');

-- 외부 정산 내역: D2 는 금액이 다르고 · D4 는 저쪽에 없고 · X9 는 우리에게 없다
INSERT INTO external_statement VALUES ('D1', 100.00), ('D2', 45.00), ('X9', 20.00);
