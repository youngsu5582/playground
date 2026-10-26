# 관찰 대본 — psql 두 개(A · B) + 구경꾼 C

| | |
|---|---|
| 접속 | `localhost:55432` · DB `lab` · 사용자 `lab` · 컨테이너 `deepdive-01.01-pg` |
| 실행 위치 | 이 레슨 폴더 (`01-concurrency-consistency/l01-isolation-mvcc/`) |
| 테이블 | `account`(id, balance) · `on_call`(doctor, on_call) |

```bash
# 레슨 폴더(01-concurrency-consistency/l01-isolation-mvcc)에서
observe/up.sh            # 한 번
observe/psql.sh A        # 터미널 1
observe/psql.sh B        # 터미널 2
observe/psql.sh C        # (C 를 쓰는 장면에서만) 터미널 3 — 구경꾼. 아무 락도 잡지 않는다
observe/down.sh          # 끝나면
```

`psql.sh` 는 컨테이너 안의 psql 을 연다 — 로컬 psql 이 없어도 된다. 테이블 구조는 psql 에서 `\d 테이블명` 으로 본다 (`\dt` 는 목록).

프롬프트의 `*` 는 "트랜잭션 안", `!` 는 "실패한 트랜잭션 안(ROLLBACK 해야 함)" 이다.
각 장면 시작 전에 아무 psql(보통 A)에서 초기화: `UPDATE account SET balance = 100; UPDATE on_call SET on_call = true;` (autocommit). 트랜잭션이 열려 있으면 먼저 `ROLLBACK;` (이 레슨의 두 테이블 `account` · `on_call` 을 모두 덮는다)

---

## 장면 1 — write skew 를 눈으로 (Q08 · Q09)

| 순서 | A | B |
|---|---|---|
| 1 | `BEGIN ISOLATION LEVEL REPEATABLE READ;` | |
| 2 | | `BEGIN ISOLATION LEVEL REPEATABLE READ;` |
| 3 | `SELECT count(*) FROM on_call WHERE on_call;` | |
| 4 | | `SELECT count(*) FROM on_call WHERE on_call;` |
| 5 | `UPDATE on_call SET on_call = false WHERE doctor = 'alice';` | |
| 6 | | `UPDATE on_call SET on_call = false WHERE doctor = 'bob';` ← 기다리나? |
| 7 | `COMMIT;` | |
| 8 | | `COMMIT;` |
| 9 | `SELECT * FROM on_call;` | |

→ 초기화 SQL 을 다시 돌린 뒤(두 행이 이미 `false`) 같은 순서를 `SERIALIZABLE` 로 다시. 8번에서 무슨 메시지가 나오나? 메시지 원문을 NOTES "관찰 메모" 칸에 옮겨 적는다.

> 관찰 포인트: 6번에서 B 는 **기다리지 않는다**. 서로 다른 행이라 행 락이 겹치지 않는다 — 그래서 행 락으로는 write skew 를 못 막는다.

## 장면 2 — 쓰는 중인 행을 읽으면 (Q10)

| 순서 | A | B |
|---|---|---|
| 1 | `BEGIN;` | |
| 2 | `SELECT ctid, xmin, xmax, * FROM account;` | |
| 3 | `UPDATE account SET balance = 0 WHERE id = 1;` | |
| 4 | `SELECT ctid, xmin, xmax, * FROM account;` ← ctid · xmin 이 바뀌었나 | |
| 5 | | `SELECT ctid, xmin, xmax, * FROM account;` ← 기다리나? 무엇이 보이나? xmax 는? |
| 6 | `SELECT txid_current();` ← B 가 본 xmax 와 같은 번호인가 | |
| 7 | `ROLLBACK;` | |
| 8 | | `SELECT ctid, xmin, xmax, * FROM account;` ← 롤백 후에도 xmax 가 남아 있나? 그래도 보이는 이유는? |

## 장면 3 — 누가 누구를 기다리나 (Q06)

| 순서 | A | B |
|---|---|---|
| 1 | `BEGIN; UPDATE account SET balance = balance - 30 WHERE id = 1;` | |
| 2 | | `BEGIN; UPDATE account SET balance = balance - 50 WHERE id = 1;` ← 멈춘다 |

세 번째 터미널(`observe/psql.sh C`)에서:

```sql
-- psql C 에서
SELECT pid, state, wait_event_type, wait_event, left(query, 60) AS query
FROM pg_stat_activity WHERE datname = 'lab' AND pid <> pg_backend_pid();

SELECT pid, locktype, mode, granted, relation::regclass, transactionid
FROM pg_locks WHERE pid <> pg_backend_pid() ORDER BY pid, granted DESC;
```

→ B 는 무엇(`transactionid`)을 기다리나? 그 번호는 누구의 것인가? A 에서 `COMMIT;` 하면 B 의 결과 잔고는?

---

관찰이 끝나면 README ④ 로. 본 것은 NOTES "관찰 메모"(§1-2)에, 예측과 달랐던 지점은 "틀린 예측" 칸(§1)에 남긴다.
