# spring-shutdown-playground

> **완료 기준(1줄)**: s2~s4 의 `todo()` 를 전부 예측으로 채우고 `IdleDrainLifecycle` 을 직접 구현해서, `./gradlew test` 가 통과하고 `./scripts/03-progress.sh` 가 0 을 보인다.

배포 때 "커밋 뒤 `@Async` 로 넘긴 작업이 사라진다" 는 문제를 보다가 시작했다.
`waitForTasksToCompleteOnShutdown(true)` 를 켜면 해결될 것 같지만, 실제로는 **풀이 기다리는 시점에 Redis 연결이 이미 끊겨 있다.**
이 저장소는 그 이유를 Spring 의 종료 3단계로 쪼개서 직접 예측하고 확인한다.

새 기술은 배우지 않는다. 이미 쓰고 있는 `ThreadPoolTaskExecutor`·`SmartLifecycle`·`@PreDestroy` 의 **정확한 종료 계약**을 배운다.

---

## 규칙 — 예측 테스트

```java
assertThat(stageOf("  task a1 끝")).isEqualTo(todo());   // Q1 a1 이 끝나는 순간, 종료는 어느 단계에 있나
                                              // ↑ 실행 전에 내 예측(Stage.LIFECYCLE_STOP 등)으로 바꾼다
```

1. 테스트를 읽고 **기대값을 먼저 적는다.** `todo()` 를 그대로 두고 돌리면 "예측값을 아직 적지 않았다" 로 실패한다.
2. **한 번에 테스트 하나**만 돌린다. 통과하면 알던 것이고, **실패하면 그게 배운 것이다.** 타임라인을 읽고 `TESTING.md` 에 한 줄 남긴다.
3. 그다음에야 `docs/NN-*.md` 답지를 펼친다. 정답 코드는 태그로 남겨 두었다. 막혔을 때만 본다.
   ```bash
   git diff spring-shutdown-answers -- app/src     # 이 폴더에서. todo() 자리의 정답과 IdleDrain 구현이 보인다
   ```

**문제 조건은 각 테스트 클래스 머리말에 있다.** 종료 단계(①②③)가 무엇을 하는지, 컨텍스트에 어떤 빈이 어떤 phase 로 있는지, 질문이 가리키는 이벤트 이름이 무슨 뜻인지를 먼저 읽는다.

**보기는 enum 이다.** 자동완성으로 고르고, 상수에 마우스를 올리면 설명이 보인다.

| 질문 | 답의 타입 | 보기 |
|---|---|---|
| `stageOf(event)` | `Stage` | `BEFORE_SHUTDOWN` · `CONTEXT_CLOSED_EVENT`(①) · `LIFECYCLE_STOP`(②) · `BEAN_DESTROY`(③) |
| `order(a, b)` | `Order` | `BEFORE` · `AFTER` |
| `threadOf(event)` | `ThreadRole` | `CLOSING_THREAD` · `POOL_A` · `POOL_B` · `SHUTDOWN_HOOK` |
| `submit(name)` | `Submission` | `ACCEPTED` · `REJECTED` · `NOT_SUBMITTED` |
| `result(name)` | `Outcome` | `SUCCESS` · `FAILURE` · `NOT_ATTEMPTED` |
| `secondsBetween(a, b)` | `long` | 반올림한 정수 초 (`0L`, `1L` …) |
| `happened(event)` | `boolean` | `true` · `false` |

## 학습 순서

| 순서 | 할 일 | 방식 |
|---|---|---|
| 1 | `./gradlew s1` | **관찰.** 종료 3단계 타임라인을 읽는다 (답이 채워져 있다) |
| 2 | s2 → s3 → s4 의 `todo()` | **예측.** 테스트 하나씩 |
| 3 | `IdleDrainLifecycle.stop()` | **구현.** 뼈대의 TODO 를 채운다. 통과 기준은 T-07e · T-08c · T-09b |
| 4 | `./gradlew s5` | **확인.** 가짜 Redis 로 본 결과가 진짜 Lettuce 에서도 같은지 |
| 5 | 새 질문 하나 | **작성.** 예: drain 이 풀에 의존하지 않게 만들면 phase 순서대로 불리나? |

```bash
# 테스트 하나만 (메서드 이름으로 거른다)
./gradlew s2 --tests '*waitsForRunningTaskInLifecycle'      # T-04a
./gradlew s2 --tests '*waitsInDestroyOnePoolAtATime'        # T-05
./gradlew s3 --tests '*waitForTasksMode'                    # T-07b
./gradlew s4 --tests '*waitForTasksRejectsChainedTask'      # T-08a

./scripts/03-progress.sh                 # 남은 예측 수 + drain 구현 여부
./scripts/02-sigterm-demo.sh wait        # 진짜 SIGTERM 으로 종료 (wait | default | drain)
```

전체 메서드 이름은 [TESTING.md](TESTING.md) 표에 있다.

---

## 한눈에 (답지 — 예측을 마친 뒤에 읽는다)

<details>
<summary>펼치기</summary>

```
SIGTERM → JVM shutdown hook → context.close()
 ① ContextClosedEvent        리스너에게 "닫는다" 알림. 아직 아무것도 멈추지 않음
 ② Lifecycle stop            SmartLifecycle 을 phase 큰 순서로 stop()
      MAX − 1024  웹 graceful          (Boot)
      MAX − 2048  웹 서버               (Boot)
      MAX / 2     ThreadPoolTaskExecutor ← 기본값이면 여기서 실행 중 작업을 기다림
      MAX/2 − 1   [수정안] drain         ← 여기서 비우면 모든 자원이 살아 있음 (풀에 의존해 실제로는 풀 직전에 불림)
      0           LettuceConnectionFactory → Redis 끊김
      MIN         Rabbit 연결 · Kafka producer → 끊고 다음 요청 때 재연결
 ③ Bean destroy              @PreDestroy · DisposableBean · close() 를 생성 역순으로, 한 스레드가 차례로
      ← waitForTasksToCompleteOnShutdown(true) 면 풀이 여기서 기다림 (Redis 는 이미 끊김)
      DB 커넥션 풀(Hikari) close
```

</details>

## 사전 준비

- JDK 21 (`java -version`)
- Docker — stage5 (진짜 Redis) 에만 필요. 없으면 stage5 는 건너뛴다.

## 콘솔 읽는 법

```
timeline [  512ms] [pool-a-1      ]   task a1 끝                  ← 이 저장소가 남기는 타임라인
             spring  [main] DefaultLifecycleProcessor - Stopping beans in phase 1073741823   ← Spring 자신의 로그
```

`①` 종료 이벤트 · `②` lifecycle stop · `③` destroy · 들여쓴 줄은 풀 안의 작업. 테스트 판정도 이 타임라인으로 한다.

---

## 구조

```
app/src/main/java/playground/shutdown/
├── timeline/Timeline.java                 종료 과정을 [경과ms][스레드] 로 기록
├── executor/TracingThreadPoolTaskExecutor  ThreadPoolTaskExecutor 그대로 + 세 단계 진입 시점 기록
├── executor/Pools, Tasks                   종료 설정별 풀 생성 / 작업·자원 호출 도구
├── resource/FakeRedis·FakeMq·FakeDataSource  Lettuce·Rabbit·Hikari 의 "종료 동작만" 흉내
├── drain/ShutdownFirstDrainLifecycle       비교용 완성본: 접수 마감 → 대기 (체인 작업 거절)
├── drain/IdleDrainLifecycle                ✍️ 직접 구현: 접수 유지 → 풀이 빌 때까지 대기
└── demo/SigtermDemo                        진짜 SIGTERM 데모 (drain 시나리오는 IdleDrain 구현 뒤에 의미가 있다)
app/src/test/java/playground/shutdown/
├── support/Predict, TimelineQuery          todo() 와 예측 질문용 조회
├── stage1                                  관찰 (답 채워져 있음)
├── stage2~4                                ✍️ 예측 (todo())
└── stage5                                  확인 (진짜 Lettuce)
docs/                                       답지 + 학습 노트 (README 가 지도)
```

## 비용 · 정리

- 비용 0 (로컬).
- stage5 의 Redis 컨테이너는 Testcontainers 가 테스트 끝에 지운다. 남았으면 `docker ps -a | grep testcontainers` 로 확인한다.

## 출처

- PR 4341 리뷰에서 시작 (회사 `aicreation` 저장소, `temp/CPDEVK-524_shutdown_repro` 브랜치에 같은 재현을 실제 앱으로 해 둠)
- 답지와 학습 노트: [docs/README.md](docs/README.md)
