# 07. 면접 사다리 — 재고 · 잔고 동시 차감

> 외우는 순서: 30초 답 → 2분 답 → 사다리. 답은 접혀 있다 — 먼저 소리 내어 답한다.
> 근거는 문서 01~06 에 있다. 이 문서의 숫자 · 동작은 거기서 확인한 것만 쓴다.

## 30초 답 (첫 질문용)

**Q. 재고 10개에 50명이 동시에 사면 어떻게 막나요?**

<details><summary>답</summary>

뚫리는 곳은 "읽고 → 확인 → 쓰기" 가 서로 다른 문장이라 그 사이에 남이 끼어드는 틈입니다. 모두 "재고 있네" 를 보고 읽은 값에서 1 을 뺀 값을 덮어쓰면 재고 숫자는 멀쩡한데 판 약속만 늘어납니다. 막는 길은 셋입니다. 기본은 `UPDATE … SET qty = qty - 1 WHERE … AND qty >= 1` 로 확인과 차감을 한 문장에 붙이고 영향 행 수로 성공을 판정하는 겁니다 — 먼저 온 쪽이 행 락을 잡고, 늦은 쪽은 기다렸다가 커밋된 최신 값에 조건을 다시 평가합니다(READ COMMITTED). 읽고 복잡하게 판단해야 하면 `SELECT … FOR UPDATE` 로 읽는 순간 잠그는 비관 락, 읽기와 쓰기 사이가 긴 편집이면 version 으로 충돌을 감지하고 재시도하는 낙관 락입니다. 같은 행에 몰리면 어느 전략이든 한 행에서 줄을 서므로 재고 분할 · 큐 · 예약 같은 설계로 나눕니다.
</details>

## 2분 답 (화이트보드 · 그림 없이 말로)

<details><summary>답 (구조: 문제 → 원자 UPDATE → 비관 락 → 낙관 락 → 선택 → 핫 로우)</summary>

1. **문제**: 앱이 읽은 값에서 계산한 절대 값을 쓰면 갱신 손실입니다. 음수가 안 되어서 눈에 안 띕니다. 불변식(팔린 수 = 줄어든 재고)으로 검사합니다.
2. **원자 UPDATE**: 조건과 계산을 문장 안으로. UPDATE 는 행 락을 잡고 같은 행의 두 번째는 첫 트랜잭션이 끝나기를 기다립니다. 첫 쪽이 커밋하면 갱신된 버전에 WHERE 를 다시 평가해(READ COMMITTED) 안 맞으면 0 행, 롤백하면 원래 행으로 진행해 1 행입니다. REPEATABLE READ 에서는 재평가 대신 `40001` 이라 앱이 트랜잭션을 재시도해야 합니다.
3. **비관 락**: `FOR UPDATE` 가 선택한 행을 커밋까지 잠급니다. 다른 UPDATE · DELETE · FOR UPDATE 는 막히지만 평범한 SELECT 는 안 막힙니다(MVCC). 락을 쥔 구간이 곧 줄의 길이이므로 외부 호출을 넣지 않고, 여러 상품은 ID 순서로 잠가 데드락을 피합니다.
4. **낙관 락**: 읽을 때는 락 없이 version 을 같이 읽고 `WHERE version = ?` 로 씁니다. 0 행이면 누가 먼저 고친 것이라 처음부터 다시 읽습니다. UPDATE 순간에는 행 락을 기다리고, 상한 없이 돌면 안 끝날 수 있어 재시도 상한과 backoff 가 필요합니다. version 이 판매 성공 때만 오르는 이 레슨 구현에서는 재고 N 이면 한 구매자는 최대 N 번 집니다.
5. **선택**: 단순 증감이면 원자 UPDATE, 읽고 복잡히 판단하면 비관 락, 사람이 오래 편집하는 흐름이면 낙관 락.
6. **핫 로우**: 한 행은 서버를 늘려도 직렬입니다. 락 보유를 줄이고, 그래도 병목이면 재고 버킷 분할 · 큐 직렬화 · 예약 후 만료로 줄 자체를 나눕니다. 어느 경우든 DB 의 원자 조건부 UPDATE 를 마지막 방어선으로 둡니다.
</details>

## 사다리 — 한 질문에서 꼬리가 이어지는 길

### 갈래 A: "조건부 UPDATE 는 락을 안 쓰는데 왜 안전한가요?"

1. Q. `UPDATE … SET qty = qty - 1 WHERE sku = ? AND qty >= 1` 두 개가 동시에 오면 두 번째는 무엇을 하나요?
   <details><summary>답</summary>
   UPDATE 는 행 락을 자동으로 잡습니다. 첫 트랜잭션이 아직 끝나지 않았으면 두 번째는 그 트랜잭션이 끝나기를 기다립니다. 커밋하면 갱신된 버전에 `WHERE` 를 다시 평가해 조건이 맞으면 진행하고 아니면 0 행입니다 (문서 13.2.1 · 이 레슨 Q02 · 실측: psql 장면 2).
   </details>
2. 꼬리 Q. 첫 트랜잭션이 롤백하면요?
   <details><summary>답</summary>
   롤백하면 그 효과가 없으니 두 번째는 원래 찾은 행으로 갱신을 진행해 1 행이 됩니다 (문서 13.2.1 · Q03). 영향 행 수로 성공 여부를 읽는 이유입니다.
   </details>
3. 꼬리 Q. 그럼 이 문장을 REPEATABLE READ 에서 돌리면요?
   <details><summary>답</summary>
   스냅샷 이후 다른 트랜잭션이 커밋한 같은 행을 고치려 하면 재평가 대신 `ERROR: could not serialize access due to concurrent update`(`40001`) 입니다 (문서 13.2.2 · 실측: psql 2026-10-13). 앱이 트랜잭션 전체를 재시도해야 합니다. READ COMMITTED 에서는 필요 없습니다.
   </details>
4. 꼬리 Q. 락을 직접 안 쓰는데 `pg_stat_activity` 에서 기다리는 모습은 어떻게 보이나요?
   <details><summary>답</summary>
   기다리는 쪽은 `state = active`, `wait_event_type = Lock`, `wait_event = transactionid` 이고 `pg_blocking_pids()` 가 막고 있는 세션을 돌려줍니다. 세 세션이 줄을 서면 첫 대기자만 `transactionid` 이고 그 뒤 대기자는 `tuple` 이벤트로 앞 대기자를 기다리는 모양이었습니다 (실측: psql 2026-10-13). 왜 `tuple` 인지의 내부 구조는 이 레슨에서 확인하지 않았습니다. 같은 행 UPDATE 대기의 모양이고, 유니크 INSERT 대기는 전부 삽입자 하나를 가리킵니다 (실측: psql 2026-10-13).
   </details>

### 갈래 B: "낙관 락과 비관 락, 언제 무엇을 쓰나요?"

1. Q. 낙관 락은 락이 없다는 말이 맞나요?
   <details><summary>답</summary>
   읽는 동안 락이 없다는 뜻입니다. `UPDATE … WHERE version = ?` 는 일반 UPDATE 라 행 락을 잡고 앞선 쓰기를 기다립니다 (Q04). 기다린 뒤 version 이 바뀌어 있으면 0 행이 충돌 신호입니다.
   </details>
2. 꼬리 Q. 경합이 심하면 왜 불리한가요?
   <details><summary>답</summary>
   진 쪽은 읽기 · 계산을 전부 버리고 처음부터 다시 하기 때문입니다. 관찰 테스트에서 구매자 50 · 재고 1000 일 때 낙관 락은 재시도가 450 회 안팎이었고 걸린 시간이 원자 UPDATE 의 2~4 배였습니다 (실측: 관찰 테스트 3회 — 숫자는 실행마다 다름).
   </details>
3. 꼬리 Q. 재시도 상한은 어떻게 정하나요? 넘으면요?
   <details><summary>답</summary>
   진 횟수는 "내가 읽고 쓰는 사이 성공한 다른 판매의 수" 라서(version 은 판매 성공 때만 오르는 이 레슨 구현에서 — 문서 04) 재고 N 이면 최대 N 번이고, 구매자가 한 번씩 사면 구매자 - 1 도 상한입니다. 상한이 그보다 작고 경합이 심하면 재고가 있는데도 포기하는 구매자가 생깁니다(관찰 표의 재시도소진). 넘으면 품절(`false`)과 구분되는 명확한 실패(예외)를 줍니다 — 재고가 있는데 품절이라고 하면 거짓말입니다. 대기 없이 바로 재시도하면 같이 진 사람이 같이 부딪히므로 backoff 와 jitter 를 더합니다 (해석 — 이 레슨 코드에는 없음).
   </details>
4. 꼬리 Q. JPA 에서는 어떻게 하나요?
   <details><summary>답</summary>
   `@Version` 속성을 두면 영속성 공급자가 쓸 때 갱신하고 앱은 수정하지 않습니다. 충돌하면 `OptimisticLockException` 인데 flush 나 커밋 시점에 던져질 수 있고 던져지면 트랜잭션은 롤백 표시됩니다 (Jakarta Persistence 3.1 3.4.2 · 3.4.5). 그래서 재시도는 트랜잭션 바깥에서 전체를 다시 합니다. Hibernate 가 내는 UPDATE 는 `update … set qty=?,version=? where id=? and version=?` 이고, 충돌하면 네이티브 `Session` 이든 JPA 든 `OptimisticLockException`(cause `StaleObjectStateException`)이 나옵니다 (실측: Hibernate 6.4.10 · 6.6.58, 2026-10-13).
   </details>

### 갈래 C: "선착순 이벤트에 한 상품으로 수만 명이 몰리면요?"

1. Q. 서버를 늘리면 되나요?
   <details><summary>답</summary>
   한 행은 행 락 때문에 서버 수와 무관하게 직렬입니다. 락 보유 시간 + 커밋이 처리량의 한계이고, 서버를 늘리면 대기자(와 커넥션)만 늘어납니다 (해석 — 행 락의 직렬성에서 이은 결론).
   </details>
2. 꼬리 Q. 그럼 무엇부터 하나요?
   <details><summary>답</summary>
   락 보유 시간을 줄입니다 — 원자 UPDATE 로 바꾸고 트랜잭션 안의 외부 호출을 뺍니다. `lock_timeout` 으로 대기 상한을 걸어(실측: psql — `canceling statement due to lock timeout`) 풀이 마르지 않게 합니다.
   </details>
3. 꼬리 Q. 그래도 한 행이 병목이면?
   <details><summary>답</summary>
   줄을 나눕니다(모두 해석 · 일반 설계). ① 재고를 K 개 버킷 행으로 쪼개 K 줄로, ② 같은 SKU 요청을 큐로 모아 한 소비자가 순서대로(응답은 비동기), ③ 재고 확정 전에 예약(만료 시각)으로 잡았다가 결제에서 확정(만료 시 복구). 각각 합계 조회 · 비동기 응답 · 만료 보상 로직이라는 대가가 있고, 마지막 방어선으로 원자 조건부 UPDATE 를 남깁니다.
   </details>
4. 꼬리 Q. 버킷 분할에서 `FOR UPDATE SKIP LOCKED` 로 빈 버킷을 고르면 되지 않나요?
   <details><summary>답</summary>
   문서는 `SKIP LOCKED` 가 "일관되지 않은 뷰를 주므로 범용 작업에는 부적합하고, 큐 같은 테이블을 여러 소비자가 읽을 때 락 경합을 피하는 용도" 라고 합니다 (SELECT 레퍼런스). 재고처럼 정합성이 핵심이면 건너뛴 버킷에 재고가 남아 있을 수 있다는 점을 설계에서 감수해야 합니다 (해석).
   </details>

### 갈래 D: "여러 상품을 한 주문에서 차감하면요? MySQL 이면요?"

1. Q. 주문 A 는 상품 1→2, 주문 B 는 2→1 순서로 차감한다. 어떻게 되나요?
   <details><summary>답</summary>
   서로의 행 락을 기다리는 데드락입니다. 엔진이 `deadlock_timeout`(기본 1초) 뒤 검사해 한쪽을 `40P01 deadlock detected` 로 취소합니다 (실측: psql 2026-10-13 · 문서 20.12). 문서의 처방은 모든 애플리케이션이 락을 일관된 순서로 얻는 것이므로 상품 ID 를 정렬해서 차감합니다 (문서 13.3.4).
   </details>
2. 꼬리 Q. 취소된 쪽은요?
   <details><summary>답</summary>
   트랜잭션 전체를 처음부터 재시도합니다. 데드락의 원인 분석과 락 모드는 01.02 docs 에서 다룹니다.
   </details>
3. 꼬리 Q. InnoDB 의 REPEATABLE READ 에서 일반 SELECT 로 읽고 UPDATE 하면요?
   <details><summary>답</summary>
   InnoDB 문서에 따르면 스냅샷은 SELECT 에 적용되고 UPDATE 는 방금 커밋된 행에도 영향을 줍니다 (17.7.2.3). 그래서 옛 값으로 계산한 절대 값이 덮어쓸 수 있습니다 (해석 — 직접 재현하지 않음). PostgreSQL RR 은 같은 상황에서 `40001` 입니다. 처방은 같은 세 가지(원자 UPDATE · `FOR UPDATE` · version)이고, InnoDB 에서는 `WHERE` 의 인덱스가 락 범위를 좌우합니다 (17.7.3).
   </details>

## 모를 때 — 정직하게 아는 데까지 말하는 법

- "`@Version` UPDATE 는 `where id=? and version=?` 로 나가고 충돌 시 `OptimisticLockException` 인 것까지는 로그로 봤습니다. 다만 Hibernate 6.4 · 6.6 · PostgreSQL 16 에서만 확인했습니다."
- "`FOR UPDATE` 를 `ORDER BY` 와 같이 쓰면 락을 얻는 순서가 정렬 순서라는 보장은 문서에서 못 찾았습니다. 그래서 ID 를 정렬해 한 건씩 잠그는 방식으로 말씀드립니다."
- "MySQL 에서 그 장면을 직접 돌려 보지는 않았고, 공식 문서 기준으로 UPDATE 는 최신 커밋 행에 적용된다는 것까지 근거로 말씀드립니다."
- "버킷 분할 · 큐 · 예약은 직접 구현해 측정하지 않았고, 대가가 무엇인지까지만 설계로 설명할 수 있습니다."
- 숫자는 외우지 말고 "기본값은 `SHOW` 로 확인합니다" 라고 말한다 (확실한 것: `deadlock_timeout` 기본 1초).

## 실무 장애 시나리오

### 1. "선착순 이벤트 시작 직후 DB CPU · 락 대기가 급증하고 응답이 느려진다"

- **증상**: 이벤트 시작과 함께 한 상품 API 의 p99 가 치솟고 DB 커넥션 풀이 고갈된다. 다른 API 도 느려진다. 로그에 `lock timeout` 이나 풀 대기 타임아웃.
- **확인**:
  ```sql
  -- 누가 누구를 막고 있나 (한 세션이 줄 앞을 쥐고 있나)
  SELECT pid, state, wait_event_type, wait_event, pg_blocking_pids(pid) AS blocked_by,
         now() - xact_start AS xact_age, left(query, 60) AS query
  FROM pg_stat_activity WHERE datname = current_database() AND pid <> pg_backend_pid()
  ORDER BY xact_start;
  -- 대기 이벤트별 개수 — Lock/transactionid · Lock/tuple 이 몰려 있으면 같은 행의 줄
  SELECT wait_event_type, wait_event, count(*) FROM pg_stat_activity
  WHERE state = 'active' GROUP BY 1, 2 ORDER BY 3 DESC;
  ```
  `idle in transaction` 세션이 줄의 맨 앞에 있는지(외부 호출 중?), `xact_age` 가 긴 세션이 있는지 본다. `log_lock_waits` 를 켜 두었다면 대기 로그를 본다 (이 레슨 컨테이너는 켜 둠).
- **원인 후보**: (1) 한 SKU 행 하나에 모든 요청이 몰려 직렬화 — 행 락 줄 (2) 비관 락 트랜잭션 안에서 외부 API(결제 · 알림)를 호출해 락 보유가 길다 (3) 낙관 락 + 즉시 재시도로 재시도 폭풍 (4) 풀 크기 < 대기자 수여서 무관한 API 까지 커넥션을 못 얻는다 (해석 — 일반 원인 분석).
- **조치**: 락 구간에서 외부 호출 제거 · `FOR UPDATE`/낙관 락을 원자 조건부 UPDATE 로 · `lock_timeout` 설정해 풀 고갈 방지 · 즉시 재시도에 backoff · 그래도 한 행이 병목이면 버킷 분할/큐/예약(05). 확인할 것: 변경 뒤 대기 이벤트 개수가 줄었나.

### 2. "재고 숫자는 정상인데 주문 건수가 재고보다 많다"

- **증상**: 이벤트 후 정산에서 주문 12 건 · 재고 감소 7 개 같은 불일치. 에러 로그는 없다.
- **확인**: 대사 쿼리 — `초기 재고 - 현재 재고` 와 `확정 주문 수` 비교. 차감 코드가 `SET qty = ?` 로 앱이 계산한 값을 쓰는지(갱신 손실), 차감과 주문 INSERT 가 같은 트랜잭션인지 본다.
- **원인**: 읽고 계산해서 쓰는 코드(01). 음수가 안 되어서 알림에 안 걸렸다.
- **조치**: 차감을 원자 조건부 UPDATE 로 (영향 행 수 판정) · CHECK 제약으로 음수 방지 안전망 · 정기 대사 잡 · 틀어진 재고는 주문 기준으로 보정.
