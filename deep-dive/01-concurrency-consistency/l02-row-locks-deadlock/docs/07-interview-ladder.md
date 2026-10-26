# 07. 면접 사다리 — 행 락 · 데드락

> 외우는 순서: 30초 답 → 2분 답 → 사다리. 답은 접혀 있다 — 먼저 소리 내어 답한다.
> 근거는 문서 01 ~ 06 에 있다. 이 문서의 숫자 · 동작은 거기서 확인한 것만 쓴다.

## 30초 답 (첫 질문용)

**Q. 같은 행을 동시에 고치는 트랜잭션은 어떻게 처리되고, 데드락은 어떻게 다루나요?**

<details><summary>답</summary>

PostgreSQL 은 UPDATE · DELETE · `SELECT FOR UPDATE` 가 대상 행에 행 락을 잡고, 같은 행의 쓰는 쪽 · 잠그는 쪽은 락을 쥔 트랜잭션이 끝날 때까지 줄을 섭니다. 읽기는 MVCC 라서 막히지 않습니다. 줄을 서기 싫으면 `NOWAIT` · `lock_timeout` 으로 `55P03` 에러를 받거나, 작업 큐라면 `SKIP LOCKED` 로 잡힌 행을 건너뜁니다. 서로의 락을 기다리는 원이 생기면 엔진이 `deadlock_timeout`(기본 1초) 뒤에 감지해 한쪽을 `40P01` 로 끊는데, 누가 끊기는지는 보장이 없으니 앱은 여러 행을 잠글 때 순서를 하나로 정해 예방하고, 끊긴 트랜잭션은 통째로 재시도합니다.
</details>

## 2분 답 (화이트보드 · 그림 없이 말로)

<details><summary>답</summary>

1. 락은 두 층입니다. 테이블 수준은 `SELECT` 가 ACCESS SHARE, `UPDATE` 가 ROW EXCLUSIVE 처럼 평범한 DML 끼리 충돌하지 않게 되어 있고, `ACCESS EXCLUSIVE` 만 `SELECT` 까지 막습니다. 행 수준은 `FOR UPDATE` · `NO KEY UPDATE` · `SHARE` · `KEY SHARE` 네 모드와 충돌표가 있고, 키가 아닌 열 UPDATE 는 NO KEY UPDATE, DELETE · 키 UPDATE 는 FOR UPDATE 입니다. 행 락은 메모리 락 테이블이 아니라 튜플의 xmax 에 적히고, 둘 이상이 잡으면 MultiXact 를 씁니다.
2. 기다리는 세션은 `pg_stat_activity` 에서 `Lock` 대기로 보이고, 행 락이면 상대 트랜잭션 ID 를 기다리는 모양입니다. 누가 막는지는 `pg_blocking_pids` 로 보고, 사슬의 루트가 원인인데 대개 `idle in transaction` 입니다.
3. 기다림에는 상한이 없는 게 기본이라 NOWAIT · `lock_timeout` 을 쓰고, 실패하면 트랜잭션이 중단 상태(25P02)가 되므로 롤백하거나 SAVEPOINT 를 씁니다. 작업 큐는 `FOR UPDATE SKIP LOCKED` 로 워커들이 서로 다른 행을 집게 합니다 — 단 일관되지 않은 뷰라 큐 용도만입니다.
4. 데드락은 대기 그래프의 사이클입니다. 락을 기다리다 `deadlock_timeout` 이 지나면 그 프로세스가 사이클을 찾고, 있으면 `40P01` 로 abort 합니다. 누가 끊기는지는 문서가 의존하지 말라고 했고, 1차 방어는 모든 코드가 같은 순서(예: 작은 id 먼저)로 잠그는 것, 2차는 전체 재시도입니다.
5. MySQL InnoDB 는 락이 인덱스 레코드에 걸리고 갭 · 넥스트키 락이 있으며, 락 대기는 기본 50 초 뒤 문장만 롤백, 데드락은 전체 롤백입니다.
</details>

## 사다리 — 한 질문에서 꼬리가 이어지는 길

### 갈래 A: "작업 큐를 DB 로 만들면 어떻게 짜나요?"

1. Q. 워커 여럿이 "다음 작업 하나"를 집는 쿼리를 어떻게 쓰나요?
   <details><summary>답</summary>
   한 트랜잭션에서 `SELECT id FROM jobs WHERE status = 'pending' ORDER BY id LIMIT 1 FOR UPDATE SKIP LOCKED` 로 집고, 같은 트랜잭션에서 `running` 으로 UPDATE 한 뒤 커밋합니다. 잠금이 커밋까지 가야 집은 뒤 표시하기 전의 틈이 안 생깁니다.
   </details>
2. 꼬리 Q. `SKIP LOCKED` 없이 `FOR UPDATE` 만 쓰면요?
   <details><summary>답</summary>
   중복은 막힙니다 — 두 번째 워커는 기다렸다가 조건에서 탈락한 행 대신 다음 행을 받습니다. 하지만 워커들이 같은 행 앞에 한 줄로 서서 처리량이 직렬화됩니다. `SKIP LOCKED` 는 잡힌 행을 건너뛰어 줄을 없앱니다 (이 레슨 Q06 · 구현 1 의 방법 검사).
   </details>
3. 꼬리 Q. `SKIP LOCKED` 의 위험은?
   <details><summary>답</summary>
   문서가 경고합니다 — 잠긴 행을 건너뛰므로 일관되지 않은 뷰라 범용에는 부적합하고 큐에서만 씁니다. 그래서 합계 · 개수 쿼리에 쓰면 안 됩니다.
   </details>
4. 꼬리 Q. 워커가 일하다 죽으면요? 외부 API 호출도 하는 작업이라면요?
   <details><summary>답</summary>
   집기와 처리를 한 트랜잭션에 넣으면 외부 호출 동안 락을 쥐고 풀 커넥션도 점유합니다. 그래서 집기 → 커밋 → 처리 → 결과 기록으로 나누는 설계가 흔한데(02.03 outbox), 그러면 죽은 워커가 남긴 `running` 을 되돌리는 재집기(lease 만료 등) 설계가 따로 필요합니다 (설계 판단 — 이 레슨은 구현하지 않았고 문서로 확인한 것은 아닙니다).
   </details>

### 갈래 B: "데드락이 왜 나고 어떻게 막나요?"

1. Q. 데드락은 언제 생기나요?
   <details><summary>답</summary>
   둘 이상의 트랜잭션이 각자 락을 쥔 채 서로가 쥔 락을 기다릴 때입니다. 행 락에서도 생깁니다 — 이체에서 A→B 와 B→A 가 각자 출금 계좌를 먼저 잠그고 입금 계좌를 잠그려 할 때 (문서 13.3.4 의 예와 같은 모양).
   </details>
2. 꼬리 Q. PostgreSQL 은 어떻게 감지하고 누구를 끊나요?
   <details><summary>답</summary>
   락을 기다리는 프로세스가 `deadlock_timeout`(기본 1초)만큼 기다린 뒤 대기 그래프를 검사해, 사이클이면 보통 자기 트랜잭션에 `40P01` 을 냅니다(소스 README: "usually" 감지한 프로세스의 트랜잭션을 abort). 문서는 누가 끊기는지 "예측하기 어렵고 의존하지 말라"고 합니다. 
   <details><summary>실측 — 관찰(장면 4)을 끝낸 뒤 펼친다</summary>이 랩에서는 먼저 기다린 쪽의 타이머가 먼저 울려 그쪽이 끊겼습니다.</details>
   </details>
3. 꼬리 Q. 앱에서는 어떻게 예방하죠?
   <details><summary>답</summary>
   모든 코드가 여러 행을 **같은 순서**로 잠급니다. 이체면 방향이 아니라 계좌 id 가 작은 쪽 먼저. 이 레슨 테스트는 "엔진이 감지한 데드락 0회" 로 예방을 확인합니다(재시도로 때운 구현은 빨강).
   </details>
4. 꼬리 Q. 락 순서를 정할 수 없으면요? 읽고 나서 나중에 고치는 코드는요?
   <details><summary>답</summary>
   순서를 못 정하면 `40P01` 을 SQLSTATE 로 판정해 트랜잭션 바깥에서 전체 재시도(상한 · 지터)합니다. "읽으면서 `FOR SHARE` → 나중에 UPDATE" 는 두 세션이 동시에 하면 데드락이 나는 것을 실측했고(psql 2026-10-13), 처음부터 `FOR UPDATE` 로 잡으면 줄을 서서 원이 안 생깁니다 (문서: 처음 잡는 락은 가장 제한적인 모드).
   </details>
5. 꼬리 Q. 데드락 원인을 어떻게 분석하나요?
   <details><summary>답</summary>
   클라이언트 에러에는 두 프로세스의 대기 관계(DETAIL)만 있고, 각 프로세스가 실행한 쿼리는 서버 로그에 남습니다("See server log for query details"). 그래서 서버 로그에서 해당 시각의 `deadlock detected` 를 찾아 두 쿼리를 확인하고 락 순서 차이를 찾습니다. `log_lock_waits` 를 켜 두면 `deadlock_timeout` 이상 기다린 락 대기도 로그에 남습니다 (문서 20.12 · 문서 05).
   </details>

### 갈래 C: "락 때문에 서비스가 느려졌어요"

1. Q. 어디부터 보나요?
   <details><summary>답</summary>
   `pg_stat_activity` 에서 `wait_event_type = 'Lock'` 인 세션과 `pg_blocking_pids(pid)` 를 봅니다. 대기 세션은 피해자이고 원인은 사슬의 루트 — 남을 막지만 자신은 안 막힌 세션입니다 (문서 02 의 쿼리).
   </details>
2. 꼬리 Q. 루트가 `idle in transaction` 이면?
   <details><summary>답</summary>
   락을 쥔 채 아무 일도 안 하는 트랜잭션입니다 — 외부 호출 중이거나 커밋을 빠뜨린 경우가 흔합니다. `last_query` 로 그 트랜잭션이 마지막으로 한 일을 보고, 급하면 `pg_terminate_backend`(세션 종료 — 롤백되어 락이 풀림)를 씁니다. `pg_cancel_backend` 는 현재 쿼리만 취소하는데 idle in transaction 에는 취소할 쿼리가 없어 `true` 를 돌려줘도 소용없다 (실측: [공통 · 02](../../docs/02-observability-playbook.md) — 상태 그대로 `idle in transaction`). 권한은 [문서 9.27.2 Server Signaling Functions](https://www.postgresql.org/docs/16/functions-admin.html): 기본은 슈퍼유저 제한이되 GRANT 로 위임할 수 있고, 같은 역할의 구성원이거나 `pg_signal_backend` 권한이 있으면 호출할 수 있다(슈퍼유저 백엔드는 슈퍼유저만). 재발 방지는 `idle_in_transaction_session_timeout`(기본 0 = 꺼짐, 문서 20.11: 유휴 세션이 락을 과도하게 쥐지 않게 하는 용도) 과 트랜잭션 안의 외부 호출 제거입니다.
   </details>
3. 꼬리 Q. 읽기 쿼리까지 멈췄는데 쓰기 락과는 무관해 보여요.
   <details><summary>답</summary>
   ACCESS EXCLUSIVE 를 요청한 DDL(`ALTER TABLE` 등)이 오래 열린 트랜잭션 때문에 큐에서 기다리면, 그 뒤에 오는 평범한 `SELECT` 도 큐 뒤에 막힙니다(실측: 문서 02). DDL 앞에 짧은 `lock_timeout` 을 걸어 오래 서 있지 않게 하고 오래 열린 트랜잭션부터 치웁니다.
   </details>

### 갈래 D: "외래키가 있으면 락이 어떻게 달라지나요?"

1. Q. 자식 INSERT 가 부모에 락을 거나요?
   <details><summary>답</summary>
   네. 부모 행에 `FOR KEY SHARE` 표시를 남깁니다(실측: 부모 튜플 xmax 에 자식 INSERT 트랜잭션이 LOCK_ONLY 로 적힘).
   </details>
2. 꼬리 Q. 그럼 부모를 UPDATE 하면 막히나요?
   <details><summary>답</summary>
   키가 아닌 열 UPDATE 는 `FOR NO KEY UPDATE` 라 `FOR KEY SHARE` 와 충돌하지 않아 안 막힙니다. DELETE · 키 UPDATE 는 `FOR UPDATE` 라 기다립니다 (표 13.3, Q08).
   </details>
3. 꼬리 Q. 자식 쪽 FK 열에 인덱스는?
   <details><summary>답</summary>
   외래키 선언이 자동으로 만들지 않고, 부모 DELETE · 참조 열 UPDATE 가 자식 스캔을 필요로 하므로 인덱스를 두는 것이 대개 좋다고 문서가 씁니다 (ddl-constraints).
   </details>

### 갈래 E: "MySQL 이라면?"

1. Q. InnoDB 의 락 단위는?
   <details><summary>답</summary>
   인덱스 레코드입니다 — 레코드 락 · 갭 락 · 넥스트키 락. 범위를 잠가 팬텀을 막습니다. READ COMMITTED 에서는 갭 락이 꺼집니다 (17.7.1).
   </details>
2. 꼬리 Q. 락 대기 타임아웃과 데드락 처리 차이는?
   <details><summary>답</summary>
   `innodb_lock_wait_timeout` 기본 50 초 뒤 **문장만** 롤백(전체는 `--innodb-rollback-on-timeout`), 데드락은 감지되어 **트랜잭션 전체** 롤백 · 전체 재시도. 희생자는 "작은 트랜잭션" 을 고르려 합니다. PostgreSQL 은 대기 기본 무한정이고 에러가 트랜잭션을 중단 상태로 만듭니다.
   </details>

## 모를 때 — 정직하게 아는 데까지 말하는 법

- "행 락이 정확히 어떤 구조로 줄을 세우는지(tuple 락의 소스 구현)는 확인하지 못했지만, `pg_stat_activity` 에서 세 번째 대기자는 `tuple` 을 기다리고 `blocked_by` 가 두 번째 대기자인 것을 관찰했습니다."
- "누가 데드락 희생자가 되는지는 문서가 의존하지 말라고 합니다." <details><summary>실측 — 관찰(장면 4)을 끝낸 뒤 펼친다</summary>덧붙이는 말: "제가 본 것은 먼저 기다린 쪽의 타이머가 먼저 울려 그쪽이 끊긴 경우였습니다."</details>
- "Hibernate 6.4 · 6.6 에서 PostgreSQL 은 0 이 NOWAIT, -2 가 SKIP LOCKED 로 나가고 양의 타임아웃은 SQL 에 안 나가는 것을 로그로 봤습니다. 7.x 와 다른 DB 는 확인하지 못했습니다."
- "MySQL 은 직접 돌려 보지 않았고 매뉴얼 기준으로 말씀드립니다."
- 숫자를 외워서 틀리느니 "기본값은 `SHOW deadlock_timeout` 으로 확인합니다" 라고 말한다 (확실한 것: `deadlock_timeout` 1s, `lock_timeout` · `statement_timeout` 0, `innodb_lock_wait_timeout` 50s).

## 실무 장애 시나리오

### 1. "API 응답이 점점 느려지고 커넥션 풀이 마른다"

- **증상**: 앱 로그에 풀 타임아웃. DB CPU 는 낮다. 같은 테이블에 대한 쿼리가 모두 느리다.
- **확인**:
  ```sql
  -- 막힌 쪽과 막는 쪽
  SELECT pid, state, wait_event_type, wait_event, pg_blocking_pids(pid) AS blocked_by,
         now() - query_start AS waiting_for, left(query, 60) AS query
  FROM pg_stat_activity WHERE cardinality(pg_blocking_pids(pid)) > 0;
  -- 루트 원인
  SELECT pid, state, now() - xact_start AS xact_age, left(query, 60) AS last_query
  FROM pg_stat_activity
  WHERE pid IN (SELECT unnest(pg_blocking_pids(pid)) FROM pg_stat_activity)
    AND cardinality(pg_blocking_pids(pid)) = 0;
  ```
- **원인 후보**: 루트가 `idle in transaction` — 외부 호출 중이거나 커밋 누락. 또는 루트가 긴 배치 UPDATE.
- **조치**: 루트 세션이 idle in transaction 이면 `pg_terminate_backend` 로 정리(`pg_cancel_backend` 는 소용없다), 락 대기 중인 쪽은 cancel 로도 끝낼 수 있다 → 재발 방지로 `idle_in_transaction_session_timeout`, 락 대기에 `lock_timeout`, 트랜잭션 안 외부 호출 제거.

### 2. "배포 중 ALTER TABLE 때문에 서비스 전체가 몇 분 멈췄다"

- **증상**: 마이그레이션이 도는 동안 해당 테이블 읽기까지 전부 대기.
- **확인**: 위 첫 쿼리 — 읽기 세션들의 `blocked_by` 가 ALTER 세션이고, ALTER 의 `blocked_by` 가 오래 열린 트랜잭션. `pg_locks` 에서 `AccessExclusiveLock granted = f` 가 보인다.
- **원인**: ALTER 가 ACCESS EXCLUSIVE 요청으로 큐에 서서, 뒤에 오는 SELECT 까지 막았다 (실측: 문서 02).
- **조치**: 오래 열린 트랜잭션 종료 후 재시도 · DDL 세션에 `SET lock_timeout = '2s'` 같은 짧은 상한을 걸고 실패하면 다시 시도 (해석 — 운영 판단).

### 3. "이체 API 가 간헐적으로 500 — `deadlock detected`"

- **증상**: 로그에 `ERROR: deadlock detected`, SQLSTATE `40P01`. 트래픽이 높을 때만.
- **확인**: 서버 로그의 DETAIL 에서 두 프로세스가 실행한 쿼리 · 각자 잠근 계좌 순서를 확인.
- **원인**: 한 경로는 출금 → 입금 순서, 다른 경로는 반대 순서로 잠근다.
- **조치**: 모든 이체 경로에서 id 오름차순으로 잠그기(1차) + `40P01` 에 대한 트랜잭션 바깥 재시도(2차). 확인은 데드락 로그가 사라지는지.
