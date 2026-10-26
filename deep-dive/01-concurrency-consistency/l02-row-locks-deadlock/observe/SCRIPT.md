# 관찰 대본 — psql 세 개로 직접

| | |
|---|---|
| 접속 | `localhost:55433` · DB `lab` · 사용자 `lab` · 컨테이너 `deepdive-01.02-pg` |
| 실행 위치 | 이 레슨 폴더 (`01-concurrency-consistency/l02-row-locks-deadlock/`) |
| 테이블 | `jobs`(id, status, claimed_by) · `account`(id, balance) · `parent`(id, name) · `child`(id, parent_id → parent) |

```bash
# 레슨 폴더(01-concurrency-consistency/l02-row-locks-deadlock)에서
observe/up.sh            # 한 번
observe/psql.sh A        # 터미널 1
observe/psql.sh B        # 터미널 2
observe/psql.sh C        # 터미널 3 — 구경꾼. 아무 락도 잡지 않는다
observe/down.sh          # 끝나면
```

`psql.sh` 는 컨테이너 안의 psql 을 연다 — 로컬 psql 이 없어도 된다. 테이블 구조는 psql 에서 `\d 테이블명` 으로 본다 (`\dt` 는 목록).

프롬프트의 `*` 는 "트랜잭션 안", `!` 는 "실패한 트랜잭션 안(ROLLBACK 해야 함)" 이다.
이 컨테이너는 `deadlock_timeout=5s` — 데드락이 5초 뒤에 풀리니, 그 사이에 C 에서 볼 수 있다.
각 장면 시작 전에 아무 psql(보통 A)에서 초기화 (autocommit, 열린 트랜잭션은 먼저 `ROLLBACK;`) — 네 테이블 모두 덮는다:
`UPDATE jobs SET status='pending', claimed_by=NULL; UPDATE account SET balance=100; DELETE FROM child; INSERT INTO parent VALUES (1, 'orig') ON CONFLICT (id) DO UPDATE SET name = 'orig';`

C 에서 쓸 조회 (장면마다 붙여 넣는다):

```sql
-- psql C 에서
-- 누가 누구를 기다리나
SELECT pid, state, wait_event_type, wait_event, pg_blocking_pids(pid) AS blocked_by, left(query, 50) AS query
FROM pg_stat_activity WHERE datname = 'lab' AND pid <> pg_backend_pid();

-- 락 목록 (granted = false 가 기다리는 쪽)
SELECT pid, locktype, mode, granted, relation::regclass, transactionid
FROM pg_locks WHERE pid <> pg_backend_pid() AND locktype IN ('transactionid', 'tuple', 'relation') ORDER BY pid, granted DESC;
```

---

## 장면 1 — 줄 서기와 읽기 (Q01 · Q02 · Q09)

| 순서 | A | B |
|---|---|---|
| 1 | `BEGIN; SELECT * FROM jobs WHERE id = 1 FOR UPDATE;` | |
| 2 | | `BEGIN; SELECT * FROM jobs WHERE id = 1;` ← 기다리나? |
| 3 | | `UPDATE jobs SET status = 'running' WHERE id = 1;` ← 멈춘다 |
| 4 | C 에서 위 두 조회 ← B 의 `wait_event` 는? `blocked_by` 는 누구? `granted = false` 인 행은? | |
| 5 | `COMMIT;` | ← B 가 풀린다. 끝낸 뒤 `COMMIT;` |

> 관찰 포인트: 2번은 안 멈추고 3번만 멈춘다. B 가 기다리는 `transactionid` 는 **A 의 트랜잭션 번호**다 — 락의 주인이 행이 아니라 트랜잭션이라서, A 가 끝나야 풀린다.
> A 의 pid 는 `SELECT pg_backend_pid();` 로 알 수 있다.

## 장면 2 — 줄 서지 않기 (Q03 · Q04 · Q05)

A 는 장면 1 의 1번처럼 1번 행을 `FOR UPDATE` 로 잡아 둔다. B 에서 차례로:

B 의 1~4 는 `BEGIN` 없이 autocommit 으로 친다 (2번만 예외).

| 순서 | B |
|---|---|
| 1 | `SELECT * FROM jobs WHERE id = 1 FOR UPDATE NOWAIT;` ← 메시지 원문은? 바로 돌아오나? |
| 2 | 이번엔 `BEGIN;` 후 1번을 다시 → `SELECT 1;` ← 무슨 에러? → `ROLLBACK;` |
| 3 | `SET lock_timeout = '2s'; UPDATE jobs SET status='running' WHERE id = 1;` ← 얼마 뒤 무슨 메시지? |
| 4 | `SELECT id FROM jobs WHERE status='pending' ORDER BY id LIMIT 1 FOR UPDATE SKIP LOCKED;` ← 몇 번? |

## 장면 3 — 락 종류와 외래키 (Q07 · Q08)

| 순서 | A | B |
|---|---|---|
| 1 | `BEGIN; INSERT INTO child VALUES (1, 1);` | |
| 2 | | `UPDATE parent SET name = 'x' WHERE id = 1;` ← 기다리나? |
| 3 | | `DELETE FROM parent WHERE id = 1;` ← 기다리나? |
| 4 | C 에서 `SELECT * FROM pg_locks WHERE locktype='transactionid';` | |

끝나면 A · B 에서 `ROLLBACK;` — A 의 INSERT 가 열려 있으면 다음 장면 초기화가 막힌다.

> 자식 INSERT 는 부모 행을 읽기만 하는데도 `FOR KEY SHARE` 를 건다. 이름만 바꾸는 UPDATE 와는 충돌하지 않고, DELETE 와는 충돌한다.

## 장면 4 — 데드락을 눈으로 (Q10)

| 순서 | A | B |
|---|---|---|
| 1 | `BEGIN; UPDATE account SET balance = balance - 10 WHERE id = 1;` | |
| 2 | | `BEGIN; UPDATE account SET balance = balance - 10 WHERE id = 2;` |
| 3 | `UPDATE account SET balance = balance + 10 WHERE id = 2;` ← 멈춘다 | |
| 4 | | `UPDATE account SET balance = balance + 10 WHERE id = 1;` ← 멈춘다 |
| 5 | C 에서 두 조회 ← 서로를 가리키는 `blocked_by` 를 확인 | |

원은 4번부터 엔진이 끊을 때까지만 보인다. 기다리는 세션마다 `deadlock_timeout`(5초) 타이머가 **기다리기 시작한 순간부터** 돌고, 타이머가 울린 세션이 원을 찾으면 한쪽이 끊긴다. 그래서 4번 뒤 남은 시간은 5초보다 짧을 수 있다. 그러니 C 에 두 조회를 미리 붙여 넣어 두고, B 의 4번을 친 직후 C 에서 Enter 만 친다. 끊기면 한쪽에 `ERROR: deadlock detected` 와 DETAIL(프로세스·트랜잭션 번호, 어느 쪽이 누구를 기다렸나)이 찍힌다.
→ 어느 쪽이 끊겼나? 메시지 원문을 NOTES "관찰 메모" 칸에 옮겨 적는다. 4번을 5초 넘겨서(예: 7초 뒤) 하면 어느 쪽이 끊기나?

---

관찰이 끝나면 README ④ 로. 본 것은 NOTES "관찰 메모"(§1-2)에, 예측과 달랐던 지점은 "틀린 예측" 칸(§1)에 남긴다.
