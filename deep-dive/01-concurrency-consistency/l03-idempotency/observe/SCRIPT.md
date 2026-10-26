# 관찰 대본 — psql 두 개(A · B) + 구경꾼 C

| | |
|---|---|
| 접속 | `localhost:55434` · DB `lab` · 사용자 `lab` · 컨테이너 `deepdive-01.03-pg` |
| 실행 위치 | 이 레슨 폴더 (`01-concurrency-consistency/l03-idempotency/`) |
| 테이블 | `loose`(제약 없음) · `idem`(key PK, payload, hits) · `idempotency_keys` · `payments` |

```bash
# 레슨 폴더(01-concurrency-consistency/l03-idempotency)에서
observe/up.sh            # 한 번
observe/psql.sh A        # 터미널 1
observe/psql.sh B        # 터미널 2
observe/psql.sh C        # (C 를 쓰는 장면에서만) 터미널 3 — 구경꾼. 아무 락도 잡지 않는다
observe/down.sh          # 끝나면
```

`psql.sh` 는 컨테이너 안의 psql 을 연다 — 로컬 psql 이 없어도 된다. 테이블 구조는 psql 에서 `\d 테이블명` 으로 본다 (`\dt` 는 목록).

프롬프트의 `*` 는 "트랜잭션 안", `!` 는 "실패한 트랜잭션 안(ROLLBACK 해야 함)" 이다.
각 장면 시작 전에 아무 psql(보통 A)에서 초기화 (autocommit, 열린 트랜잭션은 먼저 `ROLLBACK;`) — 네 테이블 모두 덮는다:
`TRUNCATE loose; DELETE FROM idem WHERE key <> 'k1'; UPDATE idem SET hits = 1, payload = 'first'; TRUNCATE idempotency_keys; TRUNCATE payments RESTART IDENTITY;`

---

## 장면 1 — 확인하고 넣기 (Q01 · Q02)

제약이 없는 `loose` 테이블. 둘 다 `BEGIN;` 부터.

| 순서 | A | B |
|---|---|---|
| 1 | `SELECT count(*) FROM loose WHERE key = 'pay-1';` | |
| 2 | | `SELECT count(*) FROM loose WHERE key = 'pay-1';` |
| 3 | `INSERT INTO loose VALUES ('pay-1', 'from A');` | |
| 4 | | `INSERT INTO loose VALUES ('pay-1', 'from B');` ← 기다리나? |
| 5 | `COMMIT;` | `COMMIT;` |
| 6 | `SELECT * FROM loose;` | |

→ 4번에서 B 는 기다리지 않는다 — 부딪힐 제약이 없으니 락도 없다. 이어서 `idem`(유니크 제약)에 `INSERT INTO idem (key, payload) VALUES ('k1', 'second');` 를 해 보고 에러 메시지 원문을 NOTES "관찰 메모" 칸에 옮긴다.

## 장면 2 — 같은 키를 동시에 (Q03 · Q04 · Q05 · Q07)

| 순서 | A | B |
|---|---|---|
| 1 | `BEGIN;` | `BEGIN;` |
| 2 | `INSERT INTO idem (key, payload) VALUES ('k2', 'from A');` | |
| 3 | | `INSERT INTO idem (key, payload) VALUES ('k2', 'from B');` ← 멈춘다 |
| 4 | `COMMIT;` | ← 무슨 에러가 나나? |

같은 순서를 반복하며 바꿔 본다. 매번 초기화 SQL 을 먼저 돌린다 (k2 가 이미 커밋돼 있다):
- 4번을 `ROLLBACK;` 로 → B 의 INSERT 는? B 가 `COMMIT;` 한 뒤 `SELECT payload FROM idem WHERE key = 'k2';`
- 3번을 `INSERT … ON CONFLICT (key) DO NOTHING;` 으로 → 여전히 멈추나? A 가 커밋하면 `INSERT 0 ?`

세 번째 터미널(`observe/psql.sh C`)에서 B 가 멈춘 동안:

```sql
-- psql C 에서
SELECT pid, state, wait_event_type, wait_event, left(query, 60) AS query
FROM pg_stat_activity WHERE datname = 'lab' AND pid <> pg_backend_pid();

SELECT pid, locktype, mode, granted, transactionid
FROM pg_locks WHERE locktype = 'transactionid' ORDER BY pid, granted DESC;
```

→ B 는 무엇을 기다리나? 그 번호(`transactionid`)는 누구 것인가? (유니크 인덱스에 "내가 넣는 중" 이라고 적힌 미커밋 항목이 있어서, B 는 그 트랜잭션이 끝나길 기다린다)

## 장면 3 — 23505 뒤의 트랜잭션 (Q08 · Q09 · Q10)

| 순서 | A |
|---|---|
| 1 | `BEGIN;` |
| 2 | `INSERT INTO idem (key, payload) VALUES ('k1', 'second');` ← 23505. 프롬프트가 `!` 로 바뀐다 |
| 3 | `SELECT 1;` ← 무슨 에러? |
| 4 | `ROLLBACK;` |

SAVEPOINT 로: `BEGIN; SAVEPOINT sp;` → 위 2번 → `ROLLBACK TO SAVEPOINT sp;` → `SELECT 1;` → `COMMIT;`

마지막으로 `ON CONFLICT DO UPDATE` — 에러 없이 같은 자리를 갱신하고 그 행을 돌려준다:

```sql
-- psql A 에서
INSERT INTO idem (key, payload) VALUES ('k1', 'second')
ON CONFLICT (key) DO UPDATE SET hits = idem.hits + 1 RETURNING payload, hits;
```

→ payload 가 `first` 인 이유는? 위 문장에서 DO NOTHING 으로 바꾸고 `RETURNING key` 를 붙이면 몇 행이 돌아오나?

## 장면 4 — 키 선점 한 문장으로 PaymentService 를 손으로

구현 테스트가 하는 일을 psql 두 개로. `BEGIN;` 은 각자.

| 순서 | A | B |
|---|---|---|
| 1 | `INSERT INTO idempotency_keys (key, request_hash, status) VALUES ('pay-1', 'h1', 'IN_PROGRESS') ON CONFLICT (key) DO NOTHING;` ← `INSERT 0 1` = 내가 선점 | |
| 2 | | 같은 문장 ← 멈춘다 (A 가 아직 처리 중) |
| 3 | `INSERT INTO payments (customer_id, amount) VALUES ('c1', 10000) RETURNING id;` | |
| 4 | `UPDATE idempotency_keys SET status = 'DONE', response = '1' WHERE key = 'pay-1'; COMMIT;` | ← 풀린다. `INSERT 0 0` = 선점 실패 |
| 5 | | `SELECT request_hash, status, response FROM idempotency_keys WHERE key = 'pay-1';` → 저장된 응답 `1` |

→ 3번 전에 A 가 `ROLLBACK;` 하면 B 의 결과는? (`INSERT 0 1` — 키 행이 사라졌으니 B 가 선점한다. 이게 "실패한 요청은 같은 키로 재시도 가능" 의 정체)

---

관찰이 끝나면 README ④ 로. 본 것은 NOTES "관찰 메모"(§1-2)에, 예측과 달랐던 지점은 "틀린 예측" 칸(§1)에 남긴다.
