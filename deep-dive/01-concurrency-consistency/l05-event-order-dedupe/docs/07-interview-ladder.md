# 07. 면접 사다리 — 이벤트 중복 · 순서

> 외우는 순서: 30초 답 → 2분 답 → 사다리. 답은 접혀 있다 — 먼저 소리 내어 답한다.
> 근거는 문서 01~06 에 있다. 이 문서의 숫자 · 동작은 거기서 확인한 것만 쓴다.

## 30초 답 (첫 질문용)

**Q. 이벤트가 중복으로 오고 순서가 뒤집혀도 상태가 맞게 하려면 어떻게 하나요?**

<details><summary>답</summary>

브로커는 기본이 at-least-once 라 같은 메시지가 다시 오고, 순서는 파티션 안에서만 보장되니 늦은 과거 이벤트도 옵니다. 그래서 DB 쪽에서 두 가지를 막습니다. 재전달은 처리한 messageId 를 PK 로 가진 inbox 테이블에 `INSERT … ON CONFLICT DO NOTHING` 해서 영향 행 수가 0 이면 건너뜁니다. 역전은 엔티티별 version 을 두고 `ON CONFLICT DO UPDATE … WHERE 저장된 version < 이벤트 version` 으로 큰 것만 반영합니다. 이 둘을 **같은 트랜잭션**에 묶어야 반영이 실패했을 때 inbox 기록도 함께 롤백돼 재전달이 곧 재시도가 되고, 따로 커밋하면 "처리됨" 인데 반영 안 된 이벤트가 영영 사라집니다.
</details>

## 2분 답 (화이트보드 · 그림 없이 말로)

<details><summary>답 (구조: 전달 보장 → 순서 → inbox → version → 한 트랜잭션 → 설계 · 운영)</summary>

1. **전달 보장**: Kafka 문서는 at-most-once(유실 가능) · at-least-once(중복 가능) · exactly-once 를 구분하고 기본은 at-least-once 입니다. 처리 후 오프셋 커밋 전에 죽으면 마지막 커밋 위치부터 다시 읽어 중복이 납니다. idempotent producer 와 트랜잭션은 Kafka 안의 중복을 막지만, DB 같은 외부 시스템은 협조가 필요해 앱이 직접 멱등하게 만듭니다.
2. **순서**: 보장은 한 파티션 안(같은 키는 같은 파티션)입니다. 키를 잘못 잡거나 병렬 처리 · 재시도 큐 · 여러 생산자가 끼면 도착 순서와 사건 순서가 달라집니다.
3. **inbox**: messageId PK 에 `ON CONFLICT DO NOTHING` — 영향 행 수가 신호입니다. SELECT 후 INSERT 는 사이에 끼어드니 한 문장으로. 동시에 같은 id 가 오면 PK 가 줄을 세워 둘째가 첫째의 커밋 · 롤백을 기다립니다.
4. **version**: 조건부 upsert 한 문장. 동시에 와도 행 락 + READ COMMITTED 재평가로 큰 version 이 남습니다. `<` 면 같은 version 은 무시.
5. **한 트랜잭션**: inbox 와 반영은 함께 커밋되거나 함께 사라져야 합니다. 안 그러면 유실(기록만 남음) 또는 중복(기록 없이 반영).
6. **설계 · 운영**: 부수 효과는 APPLIED 일 때만, DB 밖이면 outbox · 멱등 키. inbox 는 보관 기간을 정해 지우고, 지워져도 version 이 상태를 지킵니다. Spring Kafka 에서는 에러 핸들러 재시도마다 같은 레코드가 다시 오므로 처음부터 멱등하게.
</details>

## 사다리 — 한 질문에서 꼬리가 이어지는 길

### 갈래 A: "Kafka 가 exactly-once 를 지원한다던데, 그럼 중복 처리는 필요 없나요?"

1. Q. exactly-once 가 보장하는 범위는?
   <details><summary>답</summary>
   Kafka 문서 기준으로 Kafka 안 — Kafka Streams, 또는 transactional producer + `read_committed` 컨슈머로 토픽에서 읽어 토픽에 쓰는 처리. 외부 시스템에 대해서는 "그 시스템의 협조가 필요하다" 고 문서가 쓴다 (문서 01).
   </details>
2. 꼬리 Q. idempotent producer 가 막는 건 정확히 무엇인가요?
   <details><summary>답</summary>
   프로듀서 재시도로 같은 레코드가 로그에 두 번 쓰이는 것 — 브로커가 프로듀서 ID 와 시퀀스 번호로 버립니다 (0.11.0.0 이후, `enable.idempotence` 기본 true). 컨슈머가 한 레코드를 두 번 **읽는** 것은 막지 않고, 앱이 같은 이벤트를 새로 두 번 send 한 것도 별개 레코드라 못 막습니다 (후자는 해석).
   </details>
3. 꼬리 Q. 그럼 컨슈머가 DB 에 쓸 때 현실적인 구조는요?
   <details><summary>답</summary>
   at-least-once 로 받고 DB 에서 멱등 처리 — inbox 로 재전달을 거르고 version 으로 역전을 거르며 같은 트랜잭션에 묶습니다. 효과가 한 번인 것처럼 보이게 하는 것이고, 문서가 말하는 대안(오프셋을 출력과 함께 저장)과 같은 방향입니다.
   </details>
4. 꼬리 Q. 처리 후 커밋 vs 커밋 후 처리를 고르라면?
   <details><summary>답</summary>
   처리 후 커밋(at-least-once)이고 중복은 멱등 처리로 흡수합니다. 커밋 후 처리(at-most-once)는 죽으면 건너뛰어 유실됩니다 — 결제 · 배송 상태 같은 이벤트에는 유실이 더 나쁩니다 (판단 부분은 해석).
   </details>

### 갈래 B: "inbox 기록과 상태 갱신을 왜 한 트랜잭션에 묶나요?"

1. Q. 따로 커밋하면 어떤 시나리오에서 무엇이 깨지나요?
   <details><summary>답</summary>
   inbox 를 먼저 커밋하고 반영이 실패(장애 · 크래시)하면 inbox 는 "처리됨" 이고 상태는 그대로입니다. 재전달에서 inbox INSERT 가 충돌해 0행 → DUPLICATE 로 건너뛰어 그 이벤트는 영영 반영되지 않습니다 (실측: Q05 — status 가 READY 로 남음).
   </details>
2. 꼬리 Q. 반대로 반영만 하고 inbox 를 안 쓰면?
   <details><summary>답</summary>
   재전달마다 중복 반영 — 상태 값은 같아도 부수 효과(알림 · 적립)가 두 번 납니다 (Q01 에서 반영 횟수 2).
   </details>
3. 꼬리 Q. 한 트랜잭션이면 반영 실패 후에 무슨 일이 일어나나요?
   <details><summary>답</summary>
   롤백으로 inbox 기록도 사라지고, 재전달이 처음 보는 메시지로 통과해 정상 반영됩니다 — 재전달이 곧 재시도 (실측: Q06). 그래서 오프셋 커밋은 처리 후여야 하고 예외는 삼키지 말고 던져야 합니다.
   </details>
4. 꼬리 Q. 처리 안에 외부 알림 API 호출이 있으면요?
   <details><summary>답</summary>
   DB 롤백으로 되돌릴 수 없어서 커밋 실패 시 재전달에서 또 나갑니다. outbox 에 "보낼 것" 을 같은 트랜잭션으로 기록하고 별도 발송기가 보내거나(02.03), 상대 API 의 멱등 키로 messageId 를 보냅니다 (해석).
   </details>

### 갈래 C: "순서가 뒤집혀 온 이벤트는 어떻게 처리하나요?"

1. Q. version 없이 그냥 덮어쓰면?
   <details><summary>답</summary>
   마지막에 쓴 것이 이깁니다 — DELIVERED(v3) 다음에 늦게 온 IN_TRANSIT(v2) 가 상태를 과거로 되돌립니다 (실측: Q02). 에러도 없고 messageId 는 새것이라 inbox 도 통과합니다.
   </details>
2. 꼬리 Q. 어떻게 막죠? 동시에 오면요?
   <details><summary>답</summary>
   `WHERE 저장된 version < 이벤트 version` 조건부 upsert 로 작거나 같은 것은 0행(STALE). 동시에 오면 행 락이 줄을 세우고, 기다린 쪽은 갱신된 버전에 WHERE 를 다시 평가합니다 (13.2 Read Committed) — v3 · v2 어느 순서로 와도 최종 3 (실측: Q07 · Q08).
   </details>
3. 꼬리 Q. 같은 version 이 또 오면? `<=` 는 왜 안 쓰죠?
   <details><summary>답</summary>
   `<` 는 같은 version 을 무시합니다 (실측: Q03). `<=` 는 같은 이벤트가 inbox 를 뚫고 와도 반영 횟수가 또 오릅니다 (실측: psql — change_count 증가). 단, 같은 version 에 다른 내용이 오는 소스라면 그건 version 계약 위반이라 소스를 먼저 고칩니다 (해석).
   </details>
4. 꼬리 Q. version 을 소스가 안 주면?
   <details><summary>답</summary>
   시각은 시계 오차 때문에 위험하고, 전이표 · rank 는 정당한 후퇴를 놓칠 수 있습니다. 이벤트를 신호로만 쓰고 소스에서 최신 상태를 조회해 덮어쓰거나, 소스에 순번을 요청합니다 (해석).
   </details>
5. 꼬리 Q. 이벤트가 변경분(delta)이면 `<` 로 충분한가요?
   <details><summary>답</summary>
   아닙니다. 큰 version 이 먼저 와서 중간 version 이 STALE 로 버려지면 그 변경이 유실됩니다. delta 면 version 연속성을 확인해 보류하거나 상태 스냅샷을 요구합니다 (해석).
   </details>

### 갈래 D: "inbox 는 영원히 커지는데요? 그리고 MySQL 이면요?"

1. Q. inbox 보관 기간은 어떻게 정하나요?
   <details><summary>답</summary>
   브로커 재전달 · 리플레이가 가능한 최대 지연보다 길게 (해석). 지운 뒤에도 version 이 상태를 지킵니다 — 실측: inbox 를 비우고 과거 version 을 upsert 하면 0행. 부수 효과를 APPLIED 일 때만 일으키면 부수 효과도 안전합니다 (해석).
   </details>
2. 꼬리 Q. MySQL 에서 같은 패턴을 짠다면?
   <details><summary>답</summary>
   inbox 는 `INSERT IGNORE`(중복 행은 버려지고 에러 없음)나 `ON DUPLICATE KEY UPDATE`, version 조건부는 `ON DUPLICATE KEY UPDATE` 의 `IF()` 대입 (`WHERE` 가 없음 · 해석). 영향 행 수가 삽입 1 · 갱신 2 · 변화 없음 0 이라 PostgreSQL 과 다릅니다 (MySQL 8.0 문서).
   </details>
3. 꼬리 Q. MySQL 에서 동시에 같은 messageId 를 넣으면?
   <details><summary>답</summary>
   중복 키 에러는 공유 락을 잡아, 첫 세션이 롤백하면 대기 세션들이 데드락 날 수 있다는 것이 InnoDB 문서의 예입니다. ODKU 는 배타 락. 데드락은 재시도가 필요합니다 (이 레슨에서 MySQL 을 실행하지 않았다 · 해석).
   </details>

### 갈래 E: "메시지를 보냈는데 브로커에서 사라질 수 있나요? (유실 쪽)"

1. Q. `acks` 는 무엇이고 기본값은?
   <details><summary>답</summary>
   프로듀서가 요청 완료로 치기 전에 리더가 받아야 하는 확인의 수준. `0` 은 안 기다림, `1` 은 리더 로컬 쓰기까지(팔로워 복제 전 리더가 죽으면 유실), `all` 은 ISR 전체. Kafka 4.0 기본은 `all` 입니다 (문서 01 · 브로커 쪽 유실 절).
   </details>
2. 꼬리 Q. `acks=all` 이면 안 잃나요?
   <details><summary>답</summary>
   "현재 ISR 전체" 라서 ISR 이 리더 하나로 줄었으면 그 하나의 확인으로 성공합니다. `min.insync.replicas`(기본 1)를 2 로(복제 계수 3 기준) 올리면 ISR 이 2 미만일 때 쓰기가 `NotEnoughReplicas` 로 거부됩니다 — 가용성을 내주고 일관성을 삽니다. 그래도 ISR 이 전부 죽으면 보장이 없습니다.
   </details>
3. 꼬리 Q. 리더가 죽으면 새 리더는 누가 되고, 언제 유실이 나나요?
   <details><summary>답</summary>
   컨트롤러가 ISR 의 남은 멤버 중에서 뽑아 커밋된 메시지는 유지됩니다. `unclean.leader.election.enable=true`(기본 false)이면 ISR 밖 복제본이 리더가 될 수 있고 그 복제본에 없는 커밋 메시지는 유실됩니다.
   </details>
4. 꼬리 Q. 이걸 다 맞춰도 "주문은 저장됐는데 이벤트가 없다" 가 날 수 있나요?
   <details><summary>답</summary>
   네. 그건 브로커 유실이 아니라 DB 커밋과 발행이 따로인 dual write 문제입니다. 발행할 내용을 같은 DB 트랜잭션에 outbox 로 쓰고 릴레이가 발행합니다 — 대신 at-least-once 라 소비자 멱등이 필요합니다 ([01 트랙 문서 06](../../docs/06-outbox-dual-write.md)).
   </details>

## 모를 때 — 정직하게 아는 데까지 말하는 법

- "리밸런스 때 정확히 어떤 시점에 겹치는지는 프로토콜을 확인해 봐야 하지만, 마지막 커밋 위치부터 다시 읽는다는 것은 문서에 있고, 그래서 처리를 멱등하게 둡니다."
- "MySQL 의 영향 행 수 판정은 드라이버 설정(`CLIENT_FOUND_ROWS`)에 따라 달라질 수 있어서 직접 확인해야 하고, PostgreSQL 에서 관찰한 것은 삽입 · 갱신된 행만 센다는 것입니다."
- "Spring Kafka 에서 재시도가 정확히 몇 번 나가는지는 설정에 달렸는데, 기본 `DefaultErrorHandler` 는 `FixedBackOff(0L, 9)` — 재시도 9회, 최초 포함 열 번입니다 (열 번은 계산)."

## 실무 장애 시나리오

### 1. 재배포 중 리밸런스로 같은 이벤트가 대량으로 다시 처리됨

- **증상**: 배포 직후 고객에게 "배송 완료" 알림이 두 번 가고, 컨슈머 lag 이 잠깐 올랐다 내려간다.
- **확인할 것**: 컨슈머 그룹의 리밸런스 로그 · 시각, 같은 messageId 의 처리 이력, DUPLICATE/STALE/APPLIED 카운터.
  ```sql
  -- inbox 가 있다면: 같은 시각대에 DUPLICATE 가 급증했는지는 앱 카운터로 본다
  -- 알림 발송 로그에서 같은 messageId 가 두 번인지
  SELECT message_id, count(*) FROM notification_log GROUP BY 1 HAVING count(*) > 1;   -- (가상의 테이블)
  ```
- **원인 후보**: (1) 배치 단위 커밋이라 배포로 죽은 컨슈머의 미커밋 배치 전체가 다시 전달됨 (문서 01 · 06) (2) 알림 호출이 inbox 트랜잭션 밖 (3) inbox 를 따로 커밋해 DUPLICATE 가 정상 이벤트를 삼킴 (반대 증상: 알림이 **안** 감 — Q05).
- **조치**: 알림은 APPLIED 일 때만 · outbox/멱등 키로 이동, inbox 와 반영을 한 트랜잭션으로, 정적 멤버십(`group.instance.id`) 으로 재시작 리밸런스를 줄이는 것을 검토 (Kafka consumer configs: 문서: 더 큰 session timeout 과 함께 쓰면 일시적 중단으로 인한 리밸런스를 피할 수 있다 — 효과 크기는 해석).

### 2. 순서 역전으로 상태가 과거로 돌아감

- **증상**: 배송 완료된 건이 "배송 중" 으로 보이고 새 이벤트는 더 안 온다.
- **확인할 것**: 해당 shipment 의 이벤트 도착 순서 · version, 저장된 version.
  ```sql
  SELECT id, version, status, change_count FROM shipment WHERE id = 's1';
  -- version 이 이벤트 version 보다 낮은데 status 가 과거라면 version 비교가 빠진 경로가 있다
  ```
- **원인 후보**: 반영 경로 중 하나가 조건 없이 UPDATE(블라인드 덮어쓰기) · 재시도 큐 · 병렬 소비로 역전 · 소스가 version 을 같은 값으로 재사용 (문서 02 · 04).
- **조치**: 모든 반영 경로를 조건부 upsert 로 통일, STALE 카운터를 지표로, 소스에 version 계약을 확인.
