# 07. 면접 사다리 — 격리수준 · MVCC

> 외우는 순서: 30초 답 → 2분 답 → 사다리. 답은 접혀 있다 — 먼저 소리 내어 답한다.
> 근거는 문서 01~06 에 있다. 이 문서의 숫자·동작은 거기서 확인한 것만 쓴다.

## 30초 답 (첫 질문용)

**Q. PostgreSQL 의 격리수준과 MVCC 를 설명해 보세요.**

<details><summary>답</summary>

PostgreSQL 은 행을 덮어쓰지 않고 UPDATE 때마다 새 버전을 만듭니다. 각 트랜잭션은 스냅샷, 즉 "내 시점에 끝난 트랜잭션 목록" 으로 자기에게 보이는 버전만 읽기 때문에 읽기는 쓰기를 막지 않습니다. 기본 READ COMMITTED 는 문장마다 스냅샷을 새로 잡고, REPEATABLE READ 는 첫 문장에서 한 번 잡아 고정합니다 — 표준과 달리 팬텀도 막는 스냅샷 격리입니다. 다만 서로 다른 행을 고치는 write skew 는 REPEATABLE READ 에서 남고, SERIALIZABLE(SSI)이 읽기-쓰기 의존성을 추적해 막습니다. 대신 막을 때 `40001` 로 한쪽을 실패시키므로 앱이 트랜잭션 전체를 재시도해야 합니다.
</details>

## 2분 답 (화이트보드 · 그림 없이 말로)

<details><summary>답 (구조: 저장 → 스냅샷 → 쓰기 경쟁 → SERIALIZABLE → 운영)</summary>

1. **저장**: 튜플 헤더에 만든 트랜잭션(`xmin`)과 지운 트랜잭션(`xmax`)이 있습니다. UPDATE 는 새 튜플을 만들고 옛 튜플의 `xmax` 에 자기 번호를 적습니다. 커밋 여부는 `pg_xact` 에 있습니다.
2. **스냅샷**: `xmin:xmax:xip` — 이보다 작은 번호는 끝났고, xmax 이상은 아직 시작 안 했고, xip 는 진행 중입니다. 읽기는 튜플의 xmin/xmax 를 이 스냅샷과 비교해 보이는 버전을 고릅니다. 락이 필요 없습니다.
3. **격리수준**: READ COMMITTED 는 문장마다, REPEATABLE READ · SERIALIZABLE 은 트랜잭션 첫 문장에서 스냅샷을 잡습니다. 더티 리드는 어느 수준에서도 안 생기고(READ UNCOMMITTED 는 READ COMMITTED 로 취급), RR 은 팬텀도 막습니다.
4. **같은 행 쓰기**: 행 락으로 줄을 세웁니다(락은 튜플의 xmax 에 적힙니다). READ COMMITTED 는 기다린 뒤 최신 버전에 WHERE 를 다시 평가해 계속하므로 **단일 행**에 상대값 갱신(`SET balance = balance - x`)이면 안전하고(여러 행을 한 UPDATE 로 고칠 때는 행마다 최신 버전을 보는 시점이 달라 일관되지 않은 스냅샷이 될 수 있다 — 문서 04), 앱에서 읽고 계산해 쓰면 갱신 손실이 납니다. REPEATABLE READ 는 스냅샷 이후 바뀐 행을 고치면 `40001` 입니다.
5. **write skew**: 둘이 같은 근거를 읽고 서로 다른 행을 고치면 행 락이 안 겹쳐 REPEATABLE READ 가 통과시킵니다. SERIALIZABLE 은 SIREAD 락으로 읽은 범위를 기록해 rw-의존성이 위험한 구조(pivot 양쪽에 화살표, 한쪽이 먼저 커밋)가 되면 UPDATE 나 COMMIT 에서 `40001` 로 취소합니다. 오탐이 있고, 재시도가 필수입니다.
6. **운영**: 옛 버전은 VACUUM 이 치우는데, 열린 트랜잭션이 horizon 을 붙잡으면 못 치웁니다 — `idle in transaction` 이 대표적이고 `idle_in_transaction_session_timeout`(기본 꺼짐)이 방어선입니다. XID 는 32비트라 freeze 가 필요합니다.
</details>

## 사다리 — 한 질문에서 꼬리가 이어지는 길

### 갈래 A: "REPEATABLE READ 에서 write skew 가 왜 생기고 어떻게 막나요?"

1. Q. 당직 의사 둘이 동시에 "2명이니 빠져도 되겠지" 하면 REPEATABLE READ 에서 무슨 일이 일어나나요?
   <details><summary>답</summary>
   둘 다 자기 스냅샷에서 2명을 읽고 서로 다른 행(alice, bob)을 고칩니다. 행 락이 겹치지 않아 기다림도 없고, 스냅샷 이후 바뀐 행을 고친 것도 아니라 `40001` 도 없습니다. 둘 다 커밋해 당직이 0명이 됩니다 (이 레슨 Q08). 표 13.1 에서 RR 의 직렬화 이상 칸이 "Possible" 입니다.
   </details>
2. 꼬리 Q. 막는 방법을 셋 말해 보세요.
   <details><summary>답</summary>
   ① SERIALIZABLE (SSI) + 재시도, ② 판단 근거 행을 `SELECT … FOR UPDATE` 로 잠그기 — 존재하는 행만 잠그므로 새로 들어올 행(팬텀)은 못 막고, RR 에서는 상대가 먼저 커밋했으면 `FOR UPDATE` 자리에서 40001, ③ 충돌 구체화(인원 수를 담는 행 하나를 모두가 UPDATE). 셋 다 "서로 다른 행" 을 "같은 자원" 으로 바꾸거나 엔진이 감지하게 한다는 원리입니다.
   </details>
3. 꼬리 Q. SERIALIZABLE 은 어떻게 알아채나요? 락을 거나요?
   <details><summary>답</summary>
   읽은 범위에 SIREAD 락(predicate lock)을 표시합니다. 이 락은 블로킹하지 않고 데드락에도 참여하지 않으며 `pg_locks` 에 `SIReadLock` 으로 보입니다. 내가 읽은 것을 동시 트랜잭션이 쓰면 rw-의존성이 생기고, 두 트랜잭션이 서로 이런 관계면(또는 pivot 양쪽에 화살표가 있고 한쪽이 먼저 커밋하면) 한쪽을 취소합니다.
   </details>
4. 꼬리 Q. 에러는 정확히 언제 나나요? 오탐도 있나요?
   <details><summary>답</summary>
   COMMIT 에서도 나고 UPDATE 중에도 납니다 — 실측으로 둘 다 봤습니다 (`Canceled on identification as a pivot, during commit attempt / during write`). 오탐은 있습니다 (README-SSI "some false positives"). 실제로 읽고 쓰는 행이 달라도 SIREAD 락이 페이지·릴레이션 단위로 커지면 실패했습니다 — 시퀀셜 스캔 읽기에서 재현했고, 문서도 시퀀셜 스캔은 릴레이션 수준 락이 필요하다고 설명합니다.
   </details>
5. 꼬리 Q. 40001 을 받았을 때 앱은 무엇을 해야 하나요? 재시도 안에 결제 API 호출이 있으면요?
   <details><summary>답</summary>
   rollback 후 트랜잭션 **전체**를 처음부터 다시 합니다 — 앞서 읽은 값에 근거한 판단이 무효이고, 실패한 트랜잭션은 중단 상태(25P02)라 이어갈 수 없기 때문입니다. 상한(예: 5회)과 지터를 둡니다. 결제 호출이 안에 있으면 시도마다 중복되므로 커밋 이후로 미루거나 outbox 에 기록하고, 멱등 키로 상대가 중복을 흡수하게 합니다. Spring 에서는 재시도를 `@Transactional` 경계 바깥에 둡니다.
   </details>

### 갈래 B: "READ COMMITTED 에서 잔고 차감을 안전하게 하려면?"

1. Q. `balance = findById().getBalance() - x` 후 저장하면 안 되는 이유는?
   <details><summary>답</summary>
   읽을 때는 락이 없어서 둘이 같은 값(예: 100)을 읽고 각자 계산한 절대 값을 쓰면 한쪽 출금이 사라지는 갱신 손실입니다 (Q05).
   </details>
2. 꼬리 Q. 그럼 어떻게 하죠? 왜 그게 안전하죠?
   <details><summary>답</summary>
   `UPDATE account SET balance = balance - :x WHERE id = :id AND balance >= :x` 로 계산을 DB 안에서, 영향 행 수로 성공을 판정합니다. 같은 행의 행 락이 줄을 세우고, 기다린 쪽은 문서 13.2.1 의 재평가 규칙으로 갱신된 최신 버전에 WHERE 를 다시 평가합니다 — 실측: 잔고가 70 이 된 뒤 `balance >= 80` 조건은 0행.
   </details>
3. 꼬리 Q. 같은 UPDATE 를 REPEATABLE READ 에서 하면요?
   <details><summary>답</summary>
   스냅샷 이후 다른 트랜잭션이 커밋한 행을 고치려 하면 `could not serialize access due to concurrent update` (40001) 로 실패합니다. 상대가 아직 열려 있으면 기다린 뒤 상대가 커밋하는 순간 실패합니다. 앱 재시도가 필요합니다.
   </details>
4. 꼬리 Q. 행 락은 어디에 저장되나요? 락을 건 행을 읽으면 막히나요?
   <details><summary>답</summary>
   튜플의 xmax 에 잠근 트랜잭션 ID 가 적힙니다(`SELECT … FOR UPDATE` 실측으로 확인, 문서 13.3.2 는 "메모리에 기억하지 않아 행 수 제한이 없고 디스크 쓰기가 생길 수 있다"). 일반 SELECT 는 안 막힙니다 — 행 락은 쓰는 쪽과 잠그는 쪽만 막습니다. 기다리는 모양은 `pg_stat_activity` 의 `wait_event = transactionid`, `pg_locks` 의 ShareLock 대기로 보입니다.
   </details>

### 갈래 C: "MVCC 가 뭔가요?" → 운영

1. Q. UPDATE 하면 디스크에서 무슨 일이 일어나나요?
   <details><summary>답</summary>
   새 튜플이 만들어지고(`ctid` 가 바뀜) 옛 튜플의 xmax 에 내 트랜잭션 ID 가 적힙니다. 인덱스된 컬럼을 안 바꾸고 같은 페이지에 자리가 있으면 HOT 이라 새 인덱스 항목이 없습니다. 옛 튜플은 지워지지 않고 VACUUM 이 나중에 치웁니다.
   </details>
2. 꼬리 Q. 다른 세션이 고치는 중인 행을 읽으면 어떻게 되나요?
   <details><summary>답</summary>
   기다리지 않고 옛 버전을 읽습니다 — xmax 에 적힌 트랜잭션이 아직 커밋하지 않았으므로 그 삭제는 내 스냅샷에서 없는 일입니다. 보이는 버전의 xmax 가 0 이 아닐 수 있다고 문서 5.5 가 명시합니다 (Q10).
   </details>
3. 꼬리 Q. VACUUM 이 안 지워지는 경우는?
   <details><summary>답</summary>
   열린 트랜잭션의 스냅샷이 "아직 볼 수 있다" 고 horizon 을 붙잡을 때. 실측으로 REPEATABLE READ 트랜잭션이 열려 있는 동안 `VACUUM (VERBOSE)` 가 "100 are dead but not yet removable", 끝나자 100개를 제거했습니다.
   </details>
4. 꼬리 Q. 그래서 서비스에서 무엇을 설정하나요?
   <details><summary>답</summary>
   `idle_in_transaction_session_timeout` (기본 0=꺼짐) 을 롤 단위로, 앱에서는 트랜잭션 안에서 외부 호출을 하지 않기와 `@Transactional(timeout)`, `pg_stat_activity` 감시 (`xact_start`, `state = 'idle in transaction'`, `backend_xmin`). 풀 뒤에서 `idle_session_timeout` 은 조심합니다(문서 경고).
   </details>
5. 꼬리 Q. XID wraparound 는 뭐죠?
   <details><summary>답</summary>
   XID 가 32비트라 순환하므로 모든 테이블을 20억 트랜잭션 안에 VACUUM 해서 오래된 행을 frozen 으로 표시해야 합니다. `autovacuum_freeze_max_age`(기본 2억)을 넘기면 autovacuum 이 꺼져 있어도 강제 실행되고, 4천만 남으면 경고, 300만 미만이면 새 XID 발급을 거부합니다 (문서 25.1).
   </details>

### 갈래 D: "MySQL InnoDB 와 비교하면?"

1. Q. 기본 격리수준과 그 의미가 둘 다 같나요?
   <details><summary>답</summary>
   PostgreSQL 은 READ COMMITTED, InnoDB 는 REPEATABLE READ 가 기본입니다 (MySQL 17.7.2.1 · PostgreSQL 20.11). 둘 다 읽기는 스냅샷 기반입니다.
   </details>
2. 꼬리 Q. InnoDB RR 에서 남이 방금 커밋한 행을 UPDATE 하면요?
   <details><summary>답</summary>
   InnoDB 는 스냅샷이 SELECT 에 적용되고 DML 에는 필수가 아니라고 문서가 말합니다 (17.7.2.3) — UPDATE/DELETE 는 방금 커밋된 행에도 영향을 줄 수 있고 이후 그 변경이 보입니다. PostgreSQL RR 은 같은 상황에서 40001 입니다.
   </details>
3. 꼬리 Q. 일반 SELECT 와 `FOR UPDATE` 가 InnoDB 에서 다른 세상을 볼 수 있다는 건?
   <details><summary>답</summary>
   일반 SELECT 는 일관된 읽기(스냅샷), `FOR UPDATE`/`FOR SHARE` 는 최신 데이터를 읽고 락을 겁니다 (17.7.2.4). 범위 조건이면 next-key(레코드+간격) 락으로 삽입을 막아 팬텀을 방지합니다 (17.7.4).
   </details>
4. 꼬리 Q. InnoDB RR 에서도 write skew 가 생기나요?
   <details><summary>답</summary>
   문서가 그 단어로 단정하지 않으므로 추론이라고 밝히고 답합니다: 일반 SELECT 는 락을 안 걸고 UPDATE 가 PK 같은 유니크 조건으로 행을 찾으면 그 레코드만 잠그므로 서로 다른 행을 고치는 두 트랜잭션은 안 막힐 것입니다(범위 조건이면 gap/next-key 락이라 달라집니다). 직접 돌려 확인하지는 않았습니다.
   </details>

## 모를 때 — 정직하게 아는 데까지 말하는 법

- "정확한 내부 구현은 확인해 봐야 하지만, 관찰한 것은 `pg_locks` 에서 대기자가 `transactionid` ShareLock 을 기다리고 있었다는 겁니다."
- "SIREAD 락이 어느 단위로 합쳐지는지의 정확한 규칙은 모르지만, 시퀀셜 스캔이면 릴레이션 락이 된다고 문서가 설명하고, 실제로 행이 안 겹쳐도 `40001` 이 났습니다."
- "MySQL 에서 그 장면을 직접 돌려 보지는 않았습니다. 문서 기준으로는 …, 이 부분은 추론입니다."
- "hint bit 라는 용어는 공식 문서에 정의가 없고(`wal_log_hints` 설명에 이름만 나온다), 튜플의 infomask 에 커밋 여부를 캐시하는 플래그가 있다는 것까지는 소스 헤더로 확인했습니다."
- 숫자를 외워서 틀리느니 "기본값은 `SHOW` 로 확인합니다" 라고 말한다 (기본값은 `idle_in_transaction_session_timeout = 0`, `autovacuum_freeze_max_age = 200,000,000` 정도만 확실히).

## 실무 장애 시나리오

### 1. "테이블이 계속 커지고 쿼리가 점점 느려진다"

- **증상**: 주문 상태 테이블이 하루 만에 수 배로 커짐. autovacuum 은 돌고 있다.
- **확인**:
  ```sql
  SELECT pid, state, now() - xact_start AS xact_age, backend_xmin, age(backend_xmin) AS xmin_age, left(query, 60)
  FROM pg_stat_activity WHERE xact_start IS NOT NULL ORDER BY xact_start;
  -- 테이블 단위
  SELECT relname, n_dead_tup, n_live_tup, last_autovacuum FROM pg_stat_user_tables ORDER BY n_dead_tup DESC LIMIT 10;
  VACUUM (VERBOSE) 문제테이블;   -- 'dead but not yet removable' 확인
  ```
- **원인 후보**: 한 배치가 트랜잭션을 연 채 외부 호출·대기 중 (`idle in transaction`) → 그 `backend_xmin` 이 horizon 을 묶어 모든 테이블의 죽은 튜플이 안 치워짐.
- **조치**: 해당 세션/배치를 중단(커밋/롤백) → autovacuum 이 치우는지 확인 → `idle_in_transaction_session_timeout` 을 앱 롤에 설정 → 트랜잭션 안의 외부 호출 제거. 이미 부풀었으면 일반 VACUUM, 공간 반환이 꼭 필요하면 `VACUUM FULL`(배타 락).

### 2. "SERIALIZABLE 로 올렸더니 사용자 요청이 간헐적으로 500"

- **증상**: 로그에 `could not serialize access due to read/write dependencies among transactions`, SQLState `40001`.
- **확인**: 해당 트랜잭션 경계의 재시도 존재 여부(SQLState 로 판정하는가) · 실패율 · 어느 쿼리가 풀 스캔인지. `pg_locks` 에서 `mode = 'SIReadLock'` 의 `locktype` 이 `relation` 이 많은지:
  ```sql
  SELECT locktype, relation::regclass, count(*) FROM pg_locks WHERE mode = 'SIReadLock' GROUP BY 1, 2 ORDER BY 3 DESC;
  ```
- **원인**: 재시도가 없거나(에러가 호출자에게 샘), 읽기 쿼리가 시퀀셜 스캔이라 SIREAD 락이 릴레이션 단위로 커져 오탐이 늘었거나, 트랜잭션이 너무 길어 겹칠 확률이 커짐.
- **조치**: 트랜잭션 경계 바깥에 재시도(전체 재실행 · 상한 · 지터 · 부수효과는 커밋 이후) · 읽기 전용은 `READ ONLY`(긴 리포트는 `DEFERRABLE`) · 인덱스 스캔이 되도록 쿼리/인덱스 점검 · 트랜잭션을 짧게. (문서 13.2.3 성능 팁)
