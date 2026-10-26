-- 장면 1 · 2: 같은 키를 두고 벌이는 경쟁
CREATE TABLE loose (key text NOT NULL, note text);              -- 제약 없음 — 같은 키가 여러 행일 수 있다
CREATE TABLE idem (key text PRIMARY KEY, payload text NOT NULL, hits int NOT NULL DEFAULT 1);
INSERT INTO idem (key, payload) VALUES ('k1', 'first');

-- 장면 4: PaymentService 가 쓰는 테이블 (구현 테스트와 같은 모양)
CREATE TABLE idempotency_keys (key text PRIMARY KEY, request_hash text NOT NULL, status text NOT NULL, response text);
CREATE TABLE payments (id bigserial PRIMARY KEY, customer_id text NOT NULL, amount bigint NOT NULL);
