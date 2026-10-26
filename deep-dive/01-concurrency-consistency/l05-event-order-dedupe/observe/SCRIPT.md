# 관찰 대본 — psql 두 개(A · B) + 구경꾼 C

| | |
|---|---|
| 접속 | `localhost:55436` · DB `lab` · 사용자 `lab` · 컨테이너 `deepdive-01.05-pg` |
| 실행 위치 | 이 레슨 폴더 (`01-concurrency-consistency/l05-event-order-dedupe/`) |
| 테이블 | `shipment`(id, version, status, change_count) · `inbox`(message_id PK) |

```bash
# 레슨 폴더(01-concurrency-consistency/l05-event-order-dedupe)에서
observe/up.sh            # 한 번
observe/psql.sh A        # 터미널 1
observe/psql.sh B        # 터미널 2
observe/psql.sh C        # (C 를 쓰는 장면에서만) 터미널 3 — 구경꾼. 아무 락도 잡지 않는다
observe/down.sh          # 끝나면
```

`psql.sh` 는 컨테이너 안의 psql 을 연다 — 로컬 psql 이 없어도 된다. 테이블 구조는 psql 에서 `\d 테이블명` 으로 본다 (`\dt` 는 목록).

프롬프트의 `*` 는 "트랜잭션 안", `!` 는 "실패한 트랜잭션 안(ROLLBACK 해야 함)" 이다.
각 장면 시작 전에 아무 psql(보통 A)에서 초기화 (autocommit, 열린 트랜잭션은 먼저 `ROLLBACK;`) — 두 테이블과 장면 3 의 제약을 모두 덮는다:
`ALTER TABLE shipment DROP CONSTRAINT IF EXISTS maintenance; DELETE FROM inbox; UPDATE shipment SET version = 0, status = 'READY', change_count = 0;`

---

## 장면 1 — 같은 messageId 두 번 (Q04)

| 순서 | A |
|---|---|
| 1 | `INSERT INTO inbox VALUES ('m-1') ON CONFLICT DO NOTHING;` ← `INSERT 0 1` |
| 2 | 같은 문장을 한 번 더 ← 에러인가? 뭐라고 나오나 |
| 3 | `INSERT INTO inbox VALUES ('m-1');` ← `ON CONFLICT` 없이. 이번엔? 에러 코드(SQLSTATE)는? (`\set VERBOSITY verbose`) |

> 관찰 포인트: `INSERT 0 N` 의 N 이 앱이 읽는 "처음 보는 메시지인가" 신호다.

## 장면 2 — 역전과 조건부 UPDATE (Q02 · Q03)

| 순서 | A |
|---|---|
| 1 | `UPDATE shipment SET version = 3, status = 'DELIVERED' WHERE id = 's1';` |
| 2 | `UPDATE shipment SET version = 2, status = 'IN_TRANSIT' WHERE id = 's1';` ← 되돌아갔다 |
| 3 | 초기화 후 `… SET version = 3, status = 'DELIVERED' WHERE id = 's1' AND version < 3;` → `UPDATE 1` |
| 4 | `… SET version = 2, status = 'IN_TRANSIT' WHERE id = 's1' AND version < 2;` → `UPDATE 0` |

## 장면 3 — 따로 커밋 vs 한 트랜잭션 (Q05 · Q06)

실패는 제약으로 흉내 낸다: `ALTER TABLE shipment ADD CONSTRAINT maintenance CHECK (status <> 'DELIVERED');`

| 순서 | A (따로 커밋) |
|---|---|
| 1 | `INSERT INTO inbox VALUES ('m-9') ON CONFLICT DO NOTHING;` (autocommit) |
| 2 | `UPDATE shipment SET version = 1, status = 'DELIVERED' WHERE id = 's1';` ← 실패 |
| 3 | `ALTER TABLE shipment DROP CONSTRAINT maintenance;` (장애 해소) |
| 4 | 재전달: `INSERT INTO inbox VALUES ('m-9') ON CONFLICT DO NOTHING;` ← 몇 행? 앱은 무엇을 하나? `SELECT * FROM shipment;` |

→ 위 초기화 문장을 돌리고 제약을 다시 추가한 뒤 같은 일을 `BEGIN;` 안에서. 2번에서 프롬프트가 `!` 로 바뀐다 → `ROLLBACK;` → 3번 → `BEGIN; INSERT …; UPDATE …; COMMIT;`. 4번의 행 수는?

## 장면 4 — 같은 messageId 동시에 (Q09)

| 순서 | A | B |
|---|---|---|
| 1 | `BEGIN; INSERT INTO inbox VALUES ('m-1') ON CONFLICT DO NOTHING;` | |
| 2 | | `BEGIN; INSERT INTO inbox VALUES ('m-1') ON CONFLICT DO NOTHING;` ← 멈추나? |
| 3 | `ROLLBACK;` (다음엔 `COMMIT;` 로 바꿔서도) | |
| 4 | | 결과 행 수는? `COMMIT;` |

세 번째 터미널 `observe/psql.sh C` 에서 B 가 멈춰 있는 동안:
`SELECT pid, wait_event_type, wait_event, left(query, 50) FROM pg_stat_activity WHERE datname = 'lab' AND pid <> pg_backend_pid();`
→ B 는 무엇(`transactionid`)을 기다리나?

---

관찰이 끝나면 README ④ 로. 본 것은 NOTES "관찰 메모"(§1-2)에, 예측과 달랐던 지점은 "틀린 예측" 칸(§1)에 남긴다.
