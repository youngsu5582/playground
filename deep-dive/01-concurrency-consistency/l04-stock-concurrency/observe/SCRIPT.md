# 관찰 대본 — psql 두 개(A · B) + 구경꾼 C

| | |
|---|---|
| 접속 | `localhost:55435` · DB `lab` · 사용자 `lab` · 컨테이너 `deepdive-01.04-pg` |
| 실행 위치 | 이 레슨 폴더 (`01-concurrency-consistency/l04-stock-concurrency/`) |
| 테이블 | `stock`(sku, qty, version) |

```bash
# 레슨 폴더(01-concurrency-consistency/l04-stock-concurrency)에서
observe/up.sh            # 한 번
observe/psql.sh A        # 터미널 1
observe/psql.sh B        # 터미널 2
observe/psql.sh C        # (C 를 쓰는 장면에서만) 터미널 3 — 구경꾼. 아무 락도 잡지 않는다
observe/down.sh          # 끝나면
```

`psql.sh` 는 컨테이너 안의 psql 을 연다 — 로컬 psql 이 없어도 된다. 테이블 구조는 psql 에서 `\d 테이블명` 으로 본다 (`\dt` 는 목록).

프롬프트의 `*` 는 "트랜잭션 안", `!` 는 "실패한 트랜잭션 안(ROLLBACK 해야 함)" 이다.
각 장면 시작 전에 아무 psql(보통 A)에서 초기화 (autocommit, 열린 트랜잭션은 먼저 `ROLLBACK;`): `UPDATE stock SET qty = 1, version = 0;` (`stock` 하나뿐이라 이것으로 충분)

---

## 장면 1 — 틈을 눈으로 (Q01)

autocommit 상태에서 한 줄씩 번갈아:

| 순서 | A | B |
|---|---|---|
| 1 | `SELECT qty FROM stock WHERE sku = 'A';` ← 1 | |
| 2 | | `SELECT qty FROM stock WHERE sku = 'A';` ← 1 |
| 3 | `UPDATE stock SET qty = 0 WHERE sku = 'A';` ← 앱이 1 - 1 을 계산해서 넣었다 | |
| 4 | | `UPDATE stock SET qty = 0 WHERE sku = 'A';` ← 기다리지 않는다. 왜? |

> 관찰 포인트: 4번이 막히지 않는다 — A 의 UPDATE 는 이미 끝났다(autocommit). 둘 다 "성공" 이고 재고는 0. 2개를 판 흔적이 DB 어디에도 없다.

## 장면 2 — 원자 UPDATE 는 줄을 세운다 (Q02 · Q03)

| 순서 | A | B |
|---|---|---|
| 1 | `BEGIN; UPDATE stock SET qty = qty - 1 WHERE sku = 'A' AND qty >= 1;` | |
| 2 | | `BEGIN; UPDATE stock SET qty = qty - 1 WHERE sku = 'A' AND qty >= 1;` ← 멈춘다 |
| 3 | `COMMIT;` | ← 풀린다. 영향 행 수(`UPDATE 0`)를 읽는다 |

→ 초기화 SQL 을 다시 돌린 뒤(qty 가 이미 0 이다) 3번을 `ROLLBACK;` 으로 바꿔 같은 순서를 다시. 이번엔 `UPDATE 1` 이다.
세 번째 터미널(`observe/psql.sh C`)에서 B 가 멈춰 있는 동안:

```sql
-- psql C 에서
SELECT pid, state, wait_event_type, wait_event, left(query, 50) AS query
FROM pg_stat_activity WHERE datname = 'lab' AND pid <> pg_backend_pid();
```

→ B 의 `wait_event_type` 은? (`Lock` / `transactionid` — 01.01 장면 3 과 같다)

## 장면 3 — 낙관 락 (Q04 · Q05)

| 순서 | A | B |
|---|---|---|
| 1 | `BEGIN;` `SELECT qty, version FROM stock WHERE sku = 'A';` | |
| 2 | | `BEGIN;` `SELECT qty, version FROM stock WHERE sku = 'A';` |
| 3 | `UPDATE stock SET qty = 0, version = version + 1 WHERE sku = 'A' AND version = 0;` | |
| 4 | | 같은 UPDATE ← 멈춘다 (낙관 락도 이 순간엔 행 락을 기다린다) |
| 5 | `COMMIT;` | ← `UPDATE 0`. 이 0 이 "충돌했다, 다시 읽어라" 의 신호 |

→ 초기화 SQL 을 다시 돌린 뒤(qty 가 이미 0 이다) 같은 순서를 B 만 `BEGIN ISOLATION LEVEL REPEATABLE READ;` 로 바꿔 다시. 4번에서 B 는 무슨 메시지를 받나? (Q05)

## 장면 4 — FOR UPDATE (Q06 · Q07)

| 순서 | A | B |
|---|---|---|
| 1 | `BEGIN; SELECT qty FROM stock WHERE sku = 'A' FOR UPDATE;` | |
| 2 | | `BEGIN; SELECT qty FROM stock WHERE sku = 'A';` ← 기다리나? (평범한 SELECT) |
| 3 | | `SELECT qty FROM stock WHERE sku = 'A' FOR UPDATE;` ← 기다린다 |
| 4 | `UPDATE stock SET qty = 0 WHERE sku = 'A'; COMMIT;` | ← 풀린다. qty 는 몇으로 보이나? |

세 번째 터미널에서 3번 상태일 때:

```sql
-- psql C 에서
SELECT pid, locktype, mode, granted, transactionid
FROM pg_locks WHERE NOT granted;
```

→ B 는 무엇을 기다리나? (`locktype` · `transactionid` — 그 번호는 누구의 것인가)
행 락 자체는 `pg_locks` 에 행으로 나타나지 않는다 (행의 `xmax` 에 기록된다) — 그래서 기다리는 쪽이 "상대 트랜잭션 번호" 를 기다리는 모습으로 보인다.

---

관찰이 끝나면 README ④ 로. 본 것은 NOTES "관찰 메모"(§1-2)에, 예측과 달랐던 지점은 "틀린 예측" 칸(§1)에 남긴다.
