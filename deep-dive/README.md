# deep-dive

> **완료 기준(1줄)**: 지금 만들어진 트랙(01)의 레슨마다 `./gradlew NN.NN` 이 전부 초록이고, NOTES 를 채워 3분 설명을 하고, 꼬리질문 5개를 해설을 보기 전에 답한다. (정의는 [LOOP.md](LOOP.md) 한 곳)

## 처음이면 이 순서로 (자세한 따라 하기: [GUIDE.md](GUIDE.md))

1. JDK 21 과 Docker(Rancher Desktop / Docker Desktop)가 떠 있는지 확인한다.
2. (권장, 1회) 손대기 전에 빈칸 상태를 보관한다 — deep-dive 의 부모 폴더에서 `cp -R deep-dive deep-dive-blank`. 나중에 정답을 돌려 볼 때 쓴다 ([GUIDE §5-4](GUIDE.md#5-4-정답과-비교하고-싶다--정답을-돌려-보고-싶다)).
3. `cd deep-dive` — 모든 `./gradlew` 는 이 폴더에서 실행한다.
4. [LOOP.md](LOOP.md) 를 읽는다 (레슨 하나를 도는 4단계, 약 2시간 반). 모르는 말은 아래 [용어](#용어) 표에서 찾는다.
5. **[01.01 README](01-concurrency-consistency/l01-isolation-mvcc/README.md) 부터 시작한다.** 01.02 이후는 01.01 의 결론을 전제로 한다.
6. 레슨은 **읽기 전에 감으로 먼저 예측**하고(① 질문 · 첫 예측), 틀린 문항을 안고 필수 글을 읽는다(② 원리). 읽은 뒤 되짚고 구현 · 관찰한다(③).
7. 레슨을 끝낼 때마다 [PROGRESS.md](PROGRESS.md) 에 체크한다.

흩어져 있던 playground 들을 **주제별 트랙**으로 다시 짠 딥다이브 실험장이다. 원본 폴더(`../order-flow-playground` 등)는 그대로 두었다.
모든 레슨은 같은 **학습 루프**를 돈다 — [LOOP.md](LOOP.md).

```
① 질문 · 첫 예측 (읽기 전에 감으로) → ② 원리 (필수 글 + 1차 자료 + 그림) → ③ 재현 (되짚기 · 구현 · 관찰) → ④ 내 말로 (NOTES + 꼬리질문)
```

진짜 미들웨어로 확인한다 — 테스트가 컨테이너(Testcontainers)를 직접 띄운다. 트랙 01 은 PostgreSQL 16, Kafka 는 트랙 02(준비 중)부터다. 흉내 낸 결과가 아니다.

---

## 실행

준비: 위 1번 (JDK 21 · Docker). 아래 명령은 모두 deep-dive 폴더에서 친다.

```bash
# deep-dive 폴더에서
./gradlew 01.01              # 레슨 01.01 전체
./gradlew 01.01-predict      # 예측만 — 읽기 전에 감으로 답부터 적는다
./gradlew 01.01-implement    # 구현만 — TODO(구현) 을 채운다
./gradlew 01                 # 트랙 01 전체
```

처음 상태에서 예측·구현은 **빨간 게 정상**이다. 레슨 README 의 ③ 을 따라 하나씩 초록으로 만든다.

## 용어

| 말 | 뜻 |
|---|---|
| **예측** | 테스트를 돌리기 **전에** `String 예측 = "?";` 자리에 답을 적는 손 작업. ① 에서 읽기 전에 감으로 먼저 적고, ③ 에서 틀린 문항을 되짚는다. 틀린 예측이 제일 남는다 |
| **구현** | `src/main` 의 `TODO(구현)` 을 채워 테스트를 초록으로 만드는 손 작업 |
| **관찰** | 진짜 엔진(psql · 측정 출력)에서 직접 보고 NOTES 의 "관찰 메모" 에 적는 손 작업 |
| **빈칸** | 학습자가 처음 받는 **시작 상태**. 정답 코드가 비어 있어 구현 테스트가 처음엔 빨갛다 (정상) |
| **예측 칸** | 예측 테스트의 `String 예측 = "?";` 자리. 한 문항에 둘 이상일 수 있다 |
| **정답 상태** | 정답 patch 를 적용한 상태(= 구현이 끝나 모든 테스트가 초록). 내 코드가 아니라 비교용이다 |
| **정답 patch** | `solutions/NN.NN.patch`. 구현 정답에 **예측 답까지 들어 있다 → 예측 전에 열지 말 것.** 보는 법 (deep-dive 폴더에서) `less solutions/01.01.patch`. 적용해 돌려 보고 싶으면 빈칸 상태 **사본**에서 `patch -p1` (GUIDE §5-4) |
| **결과 검사 / 방법 검사 / 가드** | 결과 검사 = 결과가 맞는지(예: 초과 판매 0). 방법 검사 = 의도한 방법(예: SKIP LOCKED)으로 풀었는지. 가드 = 빈칸에서도 초록인 안전장치 테스트(깨뜨리지 말라는 표지) |
| **Qnn** | 예측 테스트의 문항 번호 = 테스트 메서드 이름 앞자리 (`Q05_…`). 점수 단위도 문항(메서드) 수다 |
| **관찰 테스트** | 01.04 에만 있는 측정 출력 테스트(`*Observation*`). 단언이 없고, 숫자를 NOTES 에 옮겨 적고 해석한다 |
| **`/kata:discuss`** | Claude Code 스킬. 없으면 아무 AI 에게 "면접관처럼 꼬리질문해 줘" 라고 하면 된다 |

---

## 트랙

| 트랙 | 레슨 | 상태 |
|---|---|---|
| [01 동시성 · 정합성](01-concurrency-consistency/README.md) (PostgreSQL) | [01.01 격리수준 · MVCC](01-concurrency-consistency/l01-isolation-mvcc/README.md) · [01.02 행 락 · 데드락](01-concurrency-consistency/l02-row-locks-deadlock/README.md) · [01.03 멱등성](01-concurrency-consistency/l03-idempotency/README.md) · [01.04 재고·잔고 동시 차감](01-concurrency-consistency/l04-stock-concurrency/README.md) · [01.05 이벤트 중복·순서](01-concurrency-consistency/l05-event-order-dedupe/README.md) · [01.06 원장과 대사](01-concurrency-consistency/l06-ledger-reconciliation/README.md) | ✅ 6개 완성 |
| 02 메시징 (Kafka · RabbitMQ) | 02.01 파티션 키 · 순서 · 02.02 컨슈머 그룹 · 오프셋 · 02.03 outbox · 멱등 소비 · 02.04 재시도 · DLQ · 02.05 Kafka vs RabbitMQ | 준비 중 |
| 03 런타임 · 트러블슈팅 | 03.01 커넥션 풀 · 03.02 풀 크기 · 컨보이 · 03.03 스레드 모델(Tomcat vs Netty) · 03.04 off-heap OOM · 03.05 JVM DNS 캐시 | 준비 중 |
| 04 네트워크 · 실시간 | 04.01 WebSocket 생존 확인 · 04.02 실시간 팬아웃 | 준비 중 |
| 05 인증 | [../oauth-oidc-playground](../oauth-oidc-playground/README.md) (이미 같은 형식 — 복사하지 않음) | 별도 |
| 06 인프라 · 클라우드 | dynamodb · ecs · eks · kubernetes · dns-cache(AWS) 색인 | 준비 중 |

개념 정리: [트랙 01 docs](01-concurrency-consistency/docs/README.md) — 레슨마다 `docs/` 가 있고(**필수** 글은 ② 에서, **심화** 글은 레슨을 마친 뒤 · 면접 전에, 면접 사다리는 ④ 에서), 트랙 공통으로 엔진 지도 · 장애 대응 쿼리 · 도구 고르기 · 꼬리질문 색인이 있다. 문항의 답은 접혀 있다.

진행판: [PROGRESS.md](PROGRESS.md) — **테스트 ✅ 와 내 말로 ✅ 를 따로** 센다. 테스트만 초록이고 NOTES 가 비어 있으면 끝난 게 아니다.

## 주차 계획 (2026 하반기)

| 기간 | 할 일 |
|---|---|
| ~10/15 | 이력서 마감이 최우선. 짬이 나면 01.01 |
| 10/16 ~ 10/22 | 트랙 01 (정합성) — 공고의 "동시성 · 유실 없는 정합성" |
| 10/23 ~ 10/29 | 트랙 02 (메시징) — Kafka 가 공고에 명시 |
| 10/30 ~ 11/06 | 트랙 03 (런타임) — "Spring · Tomcat · JVM · OS 트러블슈팅" |
| 11/07 이후 | 트랙 04 (실시간) + 모의 면접 (`/kata:discuss`) |

매일 30분은 알고리즘(코딩 테스트)에 따로 둔다 — 이 저장소 범위 밖.

## 구조

```
deep-dive/
├── testkit/          PostgresLab(진짜 PG 16) · Session(두 세션 타임라인) · Predict(예측 먼저 — 안 적으면 타임라인도 숨김) · SqlFailure · ConcurrencyHarness(N 스레드 동시 출발)
├── NN-트랙/docs/     트랙 공통 개념 정리 — 엔진 지도 · 장애 대응 쿼리 · 도구 고르기 · 꼬리질문 색인
├── NN-트랙/lNN-레슨/  README(루프 4단계) · docs/(개념 정리 + 면접 사다리) · src/main(TODO(구현)) · src/test(*PredictTest 예측 · *ImplementTest 구현) · observe/ · NOTES.md · diagrams/
├── solutions/        01.01.patch … — 레슨별 정답 patch (예측 · 구현을 끝낸 뒤 비교)
└── tools/            make_blanks.py(만든 사람용: 정답 → 빈칸 + patch) · diagram.py(그림 → .excalidraw + .svg)
```

새 레슨은 `NN-트랙/lNN-이름/build.gradle.kts` 만 있으면 자동으로 빌드에 들어가고, `./gradlew NN.NN` 단축 태스크가 생긴다.

---

## 만든 사람 메모

학습자는 읽지 않아도 된다. 이 저장소의 레슨은 아래 이전 실험장(상위 폴더의 원본)을 옮겨 온 것이고, 원본은 그대로 두었다.

| 원본 playground | 옮겨 간 곳 |
|---|---|
| postgres-tx | 01.01 · 01.02 |
| order-flow (stage2~4) | 01.03 · 01.04 · 01.05 |
| comic-entitlement | 01.05 · 02.03 · 02.04 |
| kafka · rabbitmq · modulith | 02.01 ~ 02.05 |
| connection-pool · db-convoy | 03.01 · 03.02 |
| netty · nio-buffer · dns-cache | 03.03 · 03.04 · 03.05 |
| websocket | 04.01 |
