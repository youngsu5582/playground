# 관찰 대본 — psql 한두 개 (A · 필요하면 B)

| | |
|---|---|
| 접속 | `localhost:55437` · DB `lab` · 사용자 `lab` · 컨테이너 `deepdive-01.06-pg` |
| 실행 위치 | 이 레슨 폴더 (`01-concurrency-consistency/l06-ledger-reconciliation/`) |
| 테이블 | `account` · `ledger` · `posted_txn` · `external_statement` (정의: `src/main/resources/ledger-schema.sql`) |

```bash
# 레슨 폴더에서
observe/up.sh            # 한 번 — seed 에 일부러 어긋난 데이터가 들어 있다
observe/psql.sh A        # 터미널 1
observe/psql.sh B        # (장면 2 에서만) 터미널 2
observe/down.sh          # 끝나면
```

프롬프트의 `*` 는 "트랜잭션 안", `!` 는 "실패한 트랜잭션 안(ROLLBACK 해야 함)" 이다. 테이블 구조는 `\d ledger` (트리거까지 보인다).
장면 2 이후 데이터를 처음으로 돌리려면 `observe/down.sh` 후 `observe/up.sh` (볼륨까지 지우고 seed 부터 새로).

---

## 장면 1 — float 와 numeric (Q01 · Q02 · Q09)

```sql
SELECT 0.1::float8 + 0.2::float8 AS f, 0.1::numeric + 0.2::numeric AS n;
SELECT 0.1::float8 + 0.2::float8 = 0.3::float8 AS f_eq, 0.1::numeric + 0.2::numeric = 0.3::numeric AS n_eq;
SELECT sum(0.1::float8) AS f_sum, sum(0.1::float8) = 1 AS f_eq FROM generate_series(1, 10);
SET extra_float_digits = 3;   -- float8 를 더 길게 보이게
SELECT 0.1::float8 + 0.2::float8 AS f;
SELECT 12345678901234567.89::float8 AS f, 12345678901234567.89::numeric AS n;
SELECT 1.005::numeric(12,2) AS pos, (-1.005)::numeric(12,2) AS neg;
```

> 관찰 포인트: float8 쪽은 "거의 같은" 값을 들고 있다. `=` 로 합계를 비교하는 대사는 거짓 경보를 낸다. 17 자리 금액의 센트는 float8 에서 사라진다.

## 장면 2 — 지연 제약이 커밋 때 터진다 (Q04 · Q05 · Q06)

| 순서 | A |
|---|---|
| 1 | `BEGIN;` |
| 2 | `INSERT INTO ledger (txn_id, account_id, amount) VALUES ('T1', 1, 50.00);` ← 성공하나? |
| 3 | `SELECT * FROM ledger WHERE txn_id = 'T1';` ← 내 트랜잭션 안에서는 보이나? |
| 4 | `COMMIT;` ← 메시지 원문을 NOTES 에. 프롬프트 상태는? |
| 5 | `SELECT * FROM ledger WHERE txn_id = 'T1';` |

→ 다시 `BEGIN;` · 2번 · `SET CONSTRAINTS ALL IMMEDIATE;` ← 어느 문장에서 에러가 나나? `ROLLBACK;`
→ 다시 `BEGIN;` · 두 다리를 모두 INSERT (`('T1', 1, 50.00), ('T1', 0, -50.00)`) · `COMMIT;`
→ 잔고 CHECK: `BEGIN; UPDATE account SET balance = balance - 500 WHERE id = 1;` ← 에러 · 이어서 `SELECT 1;` ← 프롬프트 `!` · `ROLLBACK;`
→ append-only: `UPDATE ledger SET amount = 0 WHERE txn_id = 'D1';` ← 에러 · `BEGIN; TRUNCATE ledger; SELECT count(*) FROM ledger; ROLLBACK;` ← 막히나?

> 관찰 포인트: 장면의 INSERT 는 성공하고 **COMMIT** 이 실패한다 — 규칙을 어긴 줄이 "내 트랜잭션 안에서는 보였다". CHECK 는 문장에서 바로 실패한다 (지연 불가).
> 장면을 마친 뒤 장면 3 전에 `observe/down.sh` · `observe/up.sh` 로 seed 를 새로 올린다 (장면 2 가 T1 을 남겼다).

## 장면 3 — 대사 쿼리로 어긋남 찾기 (Q10)

seed 의 의도: 계좌 3 은 원장이 없고(잔고 10) · 계좌 4 는 행이 없고 · 계좌 2 는 잔고 50 · 원장 합 40 이다. 계좌 5 는 잔고 0 에 원장이 없다 (정상).

```sql
-- 계좌별 잔고와 원장 합을 나란히
SELECT a.id, a.balance, COALESCE(l.s, 0) AS ledger_sum
FROM account a LEFT JOIN (SELECT account_id, sum(amount) s FROM ledger GROUP BY account_id) l ON l.account_id = a.id
ORDER BY a.id;

-- INNER JOIN 대사 — 몇 건 찾나?
SELECT a.id, a.balance, l.s
FROM account a JOIN (SELECT account_id, sum(amount) s FROM ledger GROUP BY account_id) l ON l.account_id = a.id
WHERE a.balance <> l.s;

-- FULL OUTER JOIN 대사 — 몇 건 찾나? (계좌 없는 원장 포함)
SELECT COALESCE(a.id, l.account_id) AS account_id, a.balance, l.s AS ledger_sum
FROM account a FULL OUTER JOIN (SELECT account_id, sum(amount) s FROM ledger GROUP BY account_id) l ON l.account_id = a.id
WHERE a.id IS NULL OR a.balance <> COALESCE(l.s, 0)
ORDER BY 1;

-- 외부 대사: 우리 거래 (+ 다리) vs 외부 정산 내역
SELECT COALESCE(o.txn_id, e.txn_id) AS txn_id, o.amount AS ours, e.amount AS theirs
FROM (SELECT txn_id, amount FROM ledger WHERE amount > 0) o
FULL OUTER JOIN external_statement e ON e.txn_id = o.txn_id
WHERE o.txn_id IS NULL OR e.txn_id IS NULL OR o.amount <> e.amount
ORDER BY 1;
```

→ 두 번째(INNER)는 몇 건, 세 번째(FULL)는 몇 건이고 어느 계좌들인가? 외부 대사 결과 세 줄은 각각 어떤 종류(OURS_ONLY · THEIRS_ONLY · AMOUNT_DIFFERS)인가?
→ `WHERE a.balance <> COALESCE(l.s, 0)` 에서 `COALESCE` 를 빼면 어떤 줄이 사라지나? 왜?

---

관찰이 끝나면 README ④ 로. 본 것은 NOTES "관찰 메모"(§1-2)에, 예측과 달랐던 지점은 "틀린 예측" 칸(§1)에 남긴다.
