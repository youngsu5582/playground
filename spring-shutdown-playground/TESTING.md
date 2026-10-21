# TESTING — spring-shutdown-playground

T-ID 하나 = 질문 묶음 하나. 예측은 코드의 `todo()` 자리에 적는다.
**통과 여부만 남기면 무가치하다** — "틀린 예측 → 왜 틀렸나" 가 이 파일의 존재 이유다.

---

## 테스트 매트릭스

| T-ID | 방식 | 질문 | 한 개만 실행 |
|---|---|---|---|
| **T-01** | 관찰 | 종료 이벤트 · lifecycle(phase 1000/0/−1000) · destroy(생성 first→second→third) 순서 | `./gradlew s1 --tests '*threeStagesInOrder'` |
| **T-01b** | 관찰 | `@PreDestroy` · `DisposableBean.destroy()` · `destroyMethod` 순서 | `./gradlew s1 --tests '*destroyCallbacksInsideOneBean'` |
| **T-02** | 관찰 | destroy 가 300ms 걸리는 빈 2개 — 동시인가 차례인가, 어느 스레드인가 | `./gradlew s1 --tests '*destroyIsSequentialOnClosingThread'` |
| **T-03** | 관찰 | stop callback 을 안 부르는 빈이 있으면 다음 phase 는 언제 | `./gradlew s1 --tests '*phaseTimeoutMovesOn'` |
| **T-03b** | 관찰 | phase −1000 빈이 phase 1000 빈에 의존하면 언제 멈추나 | `./gradlew s1 --tests '*dependentStopsBeforeItsPhase'` |
| **T-03c** | 관찰 | T-03b 에서 당겨진 빈의 stop 이 비동기(300ms)면 대상 빈 · 다음 phase 는 기다리나 | `./gradlew s1 --tests '*dependentAsyncStopIsNotAwaited'` |
| **T-04a** | 예측 | 기본값: 실행 중 작업(500ms)을 기다려 주나, 어디서 | `./gradlew s2 --tests '*waitsForRunningTaskInLifecycle'` |
| **T-04b** | 예측 | 기본값: a1 실행 중 + a2 대기열 — a2 도 기다려 주나 | `./gradlew s2 --tests '*doesNotWaitForQueuedTask'` |
| **T-04c** | 예측 | 기본값: phase timeout(1s)보다 긴 작업(3s)은 | `./gradlew s2 --tests '*interruptsTaskLongerThanPhaseTimeout'` |
| **T-04d** | 예측 | 기본값: 종료 시작 뒤 넘긴 작업은 거절되나 | `./gradlew s2 --tests '*acceptsTaskSubmittedDuringShutdown'` |
| **T-05** | 예측 | PR 설정: 어디서 기다리나, 풀끼리 동시인가 차례인가, 1s 넘으면 끊나 | `./gradlew s2 --tests '*waitsInDestroyOnePoolAtATime'` |
| **T-06** | 예측 | strictEarlyShutdown: 종료 이벤트 뒤 넘긴 작업은 | `./gradlew s2 --tests '*rejectsAfterContextClosedEvent'` |
| **T-07a** | 예측 | 기본값: 풀이 기다리는 순간 Redis·MQ·DB 는 | `./gradlew s3 --tests '*defaultMode'` |
| **T-07b** | 예측 | PR 설정: 풀이 기다리는 순간 Redis·MQ·DB 는 | `./gradlew s3 --tests '*waitForTasksMode'` |
| **T-07c** | 예측 | PR 설정 + DataSource 를 풀보다 늦게 만들면 | `./gradlew s3 --tests '*waitForTasksModeWithDataSourceCreatedLater'` |
| **T-07d** | 예측 | ShutdownFirstDrain: Redis·MQ·DB 는 | `./gradlew s3 --tests '*shutdownFirstDrain'` |
| **T-07e** | 예측 + 구현 | IdleDrain: Redis 는 (IdleDrain 구현 필요) | `./gradlew s3 --tests '*idleDrain'` |
| **T-08a** | 예측 | PR 설정: 종료 도중 같은 풀에 넘긴 B 는 | `./gradlew s4 --tests '*waitForTasksRejectsChainedTask'` |
| **T-08b** | 예측 | ShutdownFirstDrain: B 는 | `./gradlew s4 --tests '*shutdownFirstDrainRejectsChainedTask'` |
| **T-08c** | 예측 + 구현 | IdleDrain: B 는 (IdleDrain 구현 필요) | `./gradlew s4 --tests '*idleDrainRunsChainedTask'` |
| **T-08d** | 예측 | 기본값: B 는 접수되나, 기다려 주나 | `./gradlew s4 --tests '*defaultModeDoesNotWaitForChainedTask'` |
| **T-09a** | 확인 | PR 설정 + 진짜 Lettuce: ③ 에서 Redis 를 쓰면 | `./gradlew s5 --tests '*waitForTasksWithRealLettuce'` |
| **T-09b** | 확인 | IdleDrain + 진짜 Lettuce (IdleDrain 구현 필요) | `./gradlew s5 --tests '*idleDrainWithRealLettuce'` |

`--tests '*idleDrain'` 처럼 이름이 다른 메서드의 앞부분과 겹치면 여러 개가 같이 돈다. 정확히 하나만 보려면 메서드 이름 전체를 쓴다.

---

## 결과 보는 곳

- **콘솔**: `timeline [경과ms] [스레드] 이벤트` 줄을 위에서 아래로 읽는다. `①` 종료 이벤트 · `②` lifecycle stop · `③` destroy · 들여쓴 줄은 풀 안의 작업
- **Spring 로그**: `Stopping beans in phase …`, `ends with N bean still running after timeout`, `Shutting down ExecutorService`, `Timed out while waiting for executor`
- **스레드 이름**: `Test worker` = close 를 부른 스레드, `pool-a-1` = 풀 스레드, `SpringContextShutdownHook` = SIGTERM 데모의 hook 스레드
- **예측이 틀리면**: AssertJ 가 실제 값을 보여 준다. 그 값이 왜 나왔는지 타임라인에서 찾는다

## 관찰 규율

1. **경과 ms 를 본다.** 순서만 보면 T-02(차례로)와 T-05(풀마다 1s 씩)의 의미를 놓친다.
2. **스레드 이름을 본다.** destroy 가 close 를 부른 스레드 하나에서 도는지, stop callback 이 풀 스레드에서 불리는지가 보인다.
3. **기본값부터 예측한다.** T-04 를 먼저 맞혀야 T-05(PR 설정)가 무엇을 바꾸는지 보인다.
4. **가짜를 의심한다.** s3 는 가짜 자원이다. s5 가 진짜 Lettuce 로 같은 결과를 보여 주는지 확인한다.

---

## 틀린 예측 기록

```markdown
### T-XX Qn — YYYY-MM-DD
- 내 예측:
- 실제:
- 왜 틀렸나: (타임라인 핵심 2~3줄)
- 회사 코드에서는:
```
