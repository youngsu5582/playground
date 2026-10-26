# 08. 면접 사다리 — 멱등성

> 외우는 순서: 30초 답 → 2분 답 → 사다리. 답은 접혀 있다 — 먼저 소리 내어 답한다.
> 근거는 문서 01~07 에 있다. 이 문서의 동작 · 숫자는 거기서 확인한 것만 쓴다.

## 30초 답 (첫 질문용)

**Q. 결제 API 에서 타임아웃 뒤 재시도가 와도 중복 결제가 안 되게 하려면?**

<details><summary>답</summary>

타임아웃은 실패가 아니라 "모름" 이라 재시도는 정상이고 서버가 막아야 합니다. 클라이언트가 요청마다 만든 멱등 키를 DB 의 키 테이블에 유니크 제약으로 두고, `INSERT … ON CONFLICT DO NOTHING` 의 영향 행 수로 선점 여부를 판정합니다. 선점한 쪽만 결제하고, 같은 키가 처리 중이면 DB 가 커밋 · 롤백까지 기다리게 하고, 끝난 키는 저장된 응답을 재생하며, 같은 키에 다른 내용이면 요청 지문을 비교해 거절합니다. 확인하고 넣기는 틈이 있어 안 되고 JVM 락은 서버가 여러 대면 안 됩니다. 마지막으로 외부 결제는 DB 가 되돌리지 못하므로 결제사에도 키를 전달하거나 outbox 로 푸는 틈이 남습니다.
</details>

## 2분 답 (화이트보드 · 그림 없이 말로)

<details><summary>답 (구조: 문제 → 왜 깨지나 → 엔진 → 설계 → 경계)</summary>

1. **문제**: 응답을 못 받은 클라이언트는 처리 여부를 모릅니다. 클라이언트 · 게이트웨이 · 큐가 재시도하므로 같은 요청이 두 번 오는 것이 정상입니다. HTTP 에서 `POST` 는 멱등 메서드가 아니라서 업계는 `Idempotency-Key` 헤더 관례를 씁니다(IETF 초안이 있지만 아직 초안).
2. **왜 깨지나**: "있나 SELECT → INSERT" 는 사이의 틈에서 둘 다 "없다" 를 봅니다. 앱 락은 한 JVM 안만 압니다.
3. **엔진**: 유니크 인덱스는 같은 키의 미커밋 INSERT 를 만나면 그 트랜잭션이 끝나기를 기다립니다(`transactionid` 락 대기). 커밋하면 `23505`, 롤백하면 통과합니다. `ON CONFLICT DO NOTHING` 은 에러 없이 0행으로 알려 주고, `DO UPDATE` 는 원자적 삽입-또는-갱신을 보장합니다. 에러가 나면 트랜잭션이 중단 상태(`25P02`)라서 에러 없는 문장이나 SAVEPOINT 가 필요합니다.
4. **설계**: 선점 → 처리 → DONE + 응답 저장, 지문 비교로 같은 키 다른 내용 거절, 처리 중이면 대기(lock_timeout) 또는 409, 키 만료는 재시도 기간보다 길게. 한 트랜잭션은 단순하지만 커넥션을 쥐고, 키 선커밋은 lease 가 필요합니다.
5. **경계**: 외부 결제는 롤백되지 않아 "결제 성공 후 커밋 실패" 틈이 남습니다. 외부 API 의 멱등 키 · outbox · 정산으로 메웁니다.
</details>

## 사다리 — 한 질문에서 꼬리가 이어지는 길

### 갈래 A: "같은 키로 요청이 동시에 두 번 오면 어떻게 되나요?"

1. Q. 두 요청이 같은 멱등 키로 동시에 INSERT 하면 DB 는 어떻게 하나요?
   <details><summary>답</summary>
   유니크 인덱스에서 뒤의 INSERT 가 앞선 트랜잭션이 끝나길 기다립니다. `pg_stat_activity` 에서 `wait_event_type = Lock`, `wait_event = transactionid` 로 보이고 `pg_locks` 에서 ShareLock 미승인 행으로 나타납니다 (실측: 문서 03). 앞이 커밋하면 뒤는 위반(`23505`), `ON CONFLICT DO NOTHING` 이면 0행. 앞이 롤백하면 뒤가 성공합니다.
   </details>
2. 꼬리 Q. 그 기다림은 얼마나 가나요? 문제는 없나요?
   <details><summary>답</summary>
   `lock_timeout` 기본값이 0(꺼짐)이라 무제한입니다. 느린 외부 호출 동안 같은 키 재시도가 줄줄이 커넥션을 쥐고 기다려 풀이 고갈될 수 있습니다. `SET LOCAL lock_timeout` 으로 바운드를 두고 타임아웃(55P03)을 409 로 매핑하고 롤백하는 것을 권합니다 (설계 권고 — 해석. 타임아웃도 에러라서 트랜잭션이 중단 상태가 됨 — 실측: 문서 06).
   </details>
3. 꼬리 Q. 선점한 쪽이 롤백하면 기다리던 쪽은요?
   <details><summary>답</summary>
   성공해서 새 선점자가 되어 직접 처리합니다. 롤백된 INSERT 의 인덱스 항목은 없던 것이 되기 때문입니다 (문서 64.5). "실패한 요청은 같은 키로 다시 시도할 수 있다" 가 이 성질에서 나옵니다.
   </details>
4. 꼬리 Q. 같은 키인데 금액이 다르면요?
   <details><summary>답</summary>
   요청 지문(해시)을 키와 함께 저장해 비교하고, 다르면 거절합니다 (Stripe 는 에러, IETF 초안은 422). 키만 보고 저장된 응답을 주면 클라이언트는 5만 원 결제를 냈다고 믿는데 실제로는 1만 원이 처리된 상태가 됩니다.
   </details>

### 갈래 B: "확인하고 넣으면 안 되나요? 유니크 제약이면 충분한가요?"

1. Q. `if (!exists) save()` 가 왜 위험한가요?
   <details><summary>답</summary>
   READ COMMITTED 에서 읽기는 남의 미커밋 INSERT 를 못 보고 락도 안 잡아서 둘 다 "없다" 를 보고 둘 다 INSERT 합니다. 제약이 없으면 같은 키 2행이 생깁니다 (Q01).
   </details>
2. 꼬리 Q. `synchronized` 나 `ConcurrentHashMap` 은요?
   <details><summary>답</summary>
   한 JVM 안만 조정합니다. 서버가 둘이면 각자 처음 보는 키라 둘 다 처리합니다. 심판은 공유하는 곳(DB)에 있어야 합니다.
   </details>
3. 꼬리 Q. 유니크 제약을 걸면 다 해결되나요?
   <details><summary>답</summary>
   중복 행은 막지만 두 번째 시도는 `23505` 에러로 돌아오고, 그 에러를 "이미 처리됨" 으로 해석하는 것은 앱 몫입니다. 외부 결제 같은 부수효과는 제약과 무관하게 이미 일어났을 수 있습니다. 그래서 부수효과보다 앞에서 선점하고, `payments` 의 유니크 제약은 안전망으로 같이 둡니다.
   </details>
4. 꼬리 Q. 에러를 catch 하고 기존 행을 SELECT 하면 되지 않나요?
   <details><summary>답</summary>
   PostgreSQL 은 에러 난 트랜잭션을 중단 상태로 두고 이후 문장을 `25P02` 로 거절합니다 (Q09). 에러 없는 `ON CONFLICT DO NOTHING` 이나 SAVEPOINT (Q10), 또는 새 트랜잭션이 필요합니다.
   </details>
5. 꼬리 Q. `ON CONFLICT DO NOTHING` 과 `DO UPDATE` 중 선점에는?
   <details><summary>답</summary>
   `DO NOTHING` — 영향 행 수 1/0 으로 선점을 판정하고 충돌 시 쓰기가 없습니다. `DO UPDATE` 는 충돌 때마다 행을 써서 락 · WAL · 죽은 튜플이 생기지만 한 문장으로 기존 행 값을 `RETURNING` 으로 읽을 수 있고, `WHERE` 로 조건부 재선점도 됩니다. 단 `DO NOTHING RETURNING` 으로는 기존 행을 못 읽고, CTE 로 합쳐도 동시 요청에서 빈 결과가 나올 수 있어 (실측: 문서 04) 별도 SELECT 를 씁니다.
   </details>

### 갈래 C: "결제 승인은 성공했는데 DB 커밋이 실패하면요?"

1. Q. 한 트랜잭션 안에서 외부 결제를 부르면 어떤 문제가 있나요?
   <details><summary>답</summary>
   DB 트랜잭션은 외부 호출을 되돌리지 못합니다. 결제 성공 후 INSERT · COMMIT 이 실패하거나 프로세스가 죽으면 돈은 나갔는데 키 행은 롤백으로 사라져, 같은 키 재시도가 두 번째 결제를 합니다 (문서 06 표). 또 외부 호출 내내 커넥션과 락을 쥡니다.
   </details>
2. 꼬리 Q. 어떻게 메우나요?
   <details><summary>답</summary>
   ① 결제사 API 에도 멱등 키를 전달해 결제사가 중복을 흡수하게 한다. ② 호출 의도를 DB 에 먼저 기록하는 outbox 로 호출과 기록을 분리한다(02.03). ③ 결제사 기록과 대조하는 정산. 이 레슨은 DB 안의 중복까지만 풀고 이 틈은 남긴다고 말합니다 (해석 — 구현하지 않음).
   </details>
3. 꼬리 Q. 키를 먼저 커밋하는 설계는 어떤가요?
   <details><summary>답</summary>
   외부 호출 구간에 커넥션을 안 쥐고 처리 중인 키에 즉시 409 를 줄 수 있지만 (선점이 기다리지 않고 0행, 실측: 문서 06), IN_PROGRESS 가 커밋된 채 남으므로 서버가 죽으면 영영 처리 중입니다. 만료 시각(lease)과 원자적 인수 문장(`UPDATE … WHERE status='IN_PROGRESS' AND 만료 < now()` 의 영향 행 수)이 필요하고 lease 는 처리 시간 상한보다 길어야 합니다.
   </details>
4. 꼬리 Q. 실패한 요청의 결과를 키에 저장하나요?
   <details><summary>답</summary>
   일시 오류면 저장하지 않고 같은 키로 재시도하게 두는 것이 자연스럽습니다 (이 레슨은 롤백). Stripe API v1 은 500 까지 저장해 같은 키에 같은 결과를 줍니다. 어느 쪽이든 계약으로 문서화합니다.
   </details>

### 갈래 D: "Spring · JPA · MySQL 로 오면?"

1. Q. Spring 에서 중복 키는 어떤 예외로 오나요?
   <details><summary>답</summary>
   JDBC 템플릿 경로에서는 PostgreSQL 에러 코드 표가 `23505` 를 중복 키 코드로 두어 `DuplicateKeyException`(`DataIntegrityViolationException` 하위)이 됩니다. JPA 경로의 번역은 직접 확인해 봐야 합니다 (문서 07). 이 예외는 런타임 예외라 `@Transactional` 밖으로 나가면 롤백됩니다.
   </details>
2. 꼬리 Q. JPA `save` 로 선점하면 안 되나요?
   <details><summary>답</summary>
   `save` 는 새 엔티티면 persist, 아니면 merge 이고, 식별자를 수동으로 주면(키가 `@Id`) 새것으로 판정되지 않아 `Persistable` 이 필요하다는 것까지가 공식 문서에서 확인한 내용입니다. merge 의 내부 SELECT 여부는 확인하지 못해서, 선점은 네이티브 `ON CONFLICT` 로 하고 JPA 는 그 뒤에 쓰는 구성을 권합니다 (해석).
   </details>
3. 꼬리 Q. MySQL 이면 어떻게 하나요?
   <details><summary>답</summary>
   `INSERT IGNORE`(중복 키 외 무시 가능한 에러도 경고로 바꿈) 또는 `ON DUPLICATE KEY UPDATE`(영향 행 수 삽입 1 · 갱신 2 · 변화 없음 0, 유니크 키가 여러 개면 한 행만 갱신). 중복 키 에러 경로는 중복 레코드에 공유 락을 걸어 동시 INSERT 후 롤백 때 교착이 날 수 있다고 공식 문서에 예가 있습니다 (문서 07).
   </details>

## 모를 때 — 정직하게 아는 데까지 말하는 법

- 정확한 내부 구현을 모를 때: "소스까지는 못 읽었지만 관찰한 것은 `pg_stat_activity` 에서 `Lock / transactionid` 로 대기하고, 상대가 커밋하면 위반, 롤백하면 성공이었습니다."
- ON CONFLICT 의 RR/SERIALIZABLE 동작: "문서에는 READ COMMITTED 의 의미만 나와 있고, 직접 돌려 보니 스냅샷 이후에 커밋된 키에서 40001 이 났습니다. 이유는 소스를 확인해야 합니다."
- JPA 예외 번역 · `merge` 의 SELECT 여부: "공식 문서로 확인하지 못했습니다. 확인한 것은 JDBC 템플릿 경로의 에러 코드 표입니다."
- Idempotency-Key 표준 여부: "IETF 초안이고 제가 확인했을 때는 만료 상태였습니다. 업계 관례는 Stripe 방식입니다."

## 실무 장애 시나리오

### 시나리오 1 — 중복 결제가 발생했다

- **증상**: 고객이 같은 금액으로 두 번 결제됐다고 문의. 결제사 승인 내역도 2건.
- **확인할 것**:
  ```sql
  -- 같은 고객 · 금액 · 짧은 시간의 중복 (실측: psql 2026-10-13, 이 레슨 payments 에서 동작 확인)
  SELECT customer_id, amount, count(*) FROM payments GROUP BY 1,2 HAVING count(*) > 1;
  ```
  결제 로그에서 두 요청의 멱등 키를 대조한다: 키가 같은가, 다른가? 키가 같은데 둘 다 처리됐다면 선점이 깨진 것이고(확인 후 INSERT · JVM 락 구조), 키가 다르면 클라이언트가 재시도마다 새 키를 만든 것이다. 키가 같고 `idempotency_keys` 에 행이 하나뿐이면 결제 성공 후 커밋 실패로 키가 롤백돼 재시도가 한 번 더 결제한 경로를 의심한다.
- **원인 후보**: ① 선점이 확인 후 INSERT · 앱 락 ② 클라이언트가 재시도마다 새 키 ③ 외부 호출 후 커밋 실패로 키가 롤백 ④ 키 만료가 클라이언트 재시도 기간보다 짧음.
- **조치**: 선점을 `ON CONFLICT DO NOTHING` 한 문장으로 · 클라이언트에 키 재사용 규약 · 결제사 API 에도 키 전달 · 만료 기간 연장 · 정산 배치로 사후 탐지. 중복분은 결제사 취소 API 로 환불.

### 시나리오 2 — 재시도 폭주로 응답이 느려지고 커넥션이 고갈된다

- **증상**: 결제 API 지연 급증, 커넥션 풀 대기, DB 에서 같은 키 INSERT 들이 줄줄이 멈춤.
- **확인할 것**:
  ```sql
  -- 무엇을 기다리나 (실측: psql 2026-10-13: Lock / transactionid 3건 + 선점자 1건)
  SELECT wait_event_type, wait_event, count(*) FROM pg_stat_activity
  WHERE state = 'active' GROUP BY 1, 2 ORDER BY 3 DESC;

  -- 누가 막고 있나 (실측: psql 2026-10-13: 3개 세션이 같은 pid 를 가리켰다)
  SELECT pid, pg_blocking_pids(pid) AS blocked_by, left(query, 60) AS q, now() - xact_start AS xact_age
  FROM pg_stat_activity WHERE cardinality(pg_blocking_pids(pid)) > 0;
  ```
  같은 키의 유니크 INSERT 대기는 대기자 전부가 삽입자의 `transactionid` 를 기다리므로 `blocked_by` 가 모두 같은 pid 하나를 가리킨다 (실측: psql 2026-10-13 — 세 세션 모두 `{삽입자}`). 같은 행 UPDATE 대기는 다르다 — 첫 대기자만 앞 트랜잭션을, 뒤 대기자는 앞 대기자를 가리키는 사슬이 된다 (01.02 문서 02). 선점이 INSERT 이면 그 pid 하나가 대기열의 머리다(보통 느린 외부 호출 중). 그 pid 의 `query` · `xact_start` 로 얼마나 오래 열려 있는지 본다.
- **원인**: 선점 트랜잭션이 느린 외부 호출을 안고 있고, 같은 키의 재시도가 각자 커넥션을 쥔 채 기다린다 (`lock_timeout` 기본 0).
- **조치**: ① 선점 INSERT 에 `SET LOCAL lock_timeout` 을 걸어 409 로 매핑 ② 클라이언트 재시도에 지수 백오프 · 지터 · 상한 ③ 처리 시간이 긴 API 는 키를 먼저 커밋해 즉시 409 (lease 필요) ④ 외부 호출에 타임아웃. 급한 불은 머리 pid 의 작업을 확인해 필요하면 `pg_terminate_backend(pid)` 로 끊을 수 있다 — 이 경우 그 트랜잭션은 롤백되고 키도 같이 사라진다 (해석 — 이 레슨에서 실행해 보지 않았다).
