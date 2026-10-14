# 03. ThreadPoolTaskExecutor 의 종료 방식

Spring 6.1 부터 `ThreadPoolTaskExecutor` 는 `SmartLifecycle` 이다. 설정에 따라 세 단계에서 하는 일이 달라진다.

| 설정 | ① 종료 이벤트 | ② lifecycle (MAX/2) | ③ destroy |
|---|---|---|---|
| **기본값** | `markShutdown()` 표시만. 계속 접수 | 실행 중 작업이 0 이 될 때까지 대기 (phase timeout 까지). 대기열 작업도 계속 실행 | `shutdownNow()` — 남은 대기열 취소, 실행 중 interrupt |
| **strictEarlyShutdown** | `shutdown()` — 새 작업 거절 | 남은 작업 대기 | `shutdownNow()` |
| **waitForTasksToCompleteOnShutdown** (PR 4341) | `lateShutdown` 표시. 계속 접수 | **건너뜀** — 계속 실행 | `shutdown()` + `awaitTermination` (빈마다 차례로) |

## 기본값 (T-04)

```java
// ExecutorConfigurationSupport.onApplicationEvent (6.2)
if (this.acceptTasksAfterContextClose || this.waitForTasksToCompleteOnShutdown) {
    this.lateShutdown = true;                 // ② 를 건너뛰고 ③ 에서 종료
} else {
    this.lifecycleDelegate.markShutdown();    // "일시정지해도 작업을 막지 않는다"
    initiateEarlyShutdown();
}

// ThreadPoolTaskExecutor
protected void initiateEarlyShutdown() {
    if (this.strictEarlyShutdown) {           // 6.1.4 부터 기본값 false → 아무것도 안 함
        super.initiateEarlyShutdown();
    }
}
```

② 에서는 `stop(callback)` 이 불리고, **실행 중인 작업 수가 0 이 되는 순간** callback 이 불린다.

```java
// ExecutorLifecycleDelegate.beforeExecute — markShutdown 뒤에는 일시정지여도 막지 않는다
while (this.paused && !this.shutdown && !this.executor.isShutdown()) { this.unpaused.await(); }
```

> 📊 **측정** (2026-10-14, T-04a, `./gradlew s2`) — 실행 중 작업 500ms
> ```
> [   11ms] [Test worker] ② pool-a lifecycle stop 시작
> [  512ms] [pool-a-1   ]   task a1 끝
> [  512ms] [pool-a-1   ] ② pool-a lifecycle stop 완료   ← callback 은 풀 스레드에서 불린다
> [  513ms] [Test worker] ② redis(phase 0) stop          ← 작업이 끝난 뒤에야 Redis 가 멈춘다
> [  513ms] [Test worker] ③ destroy 단계 시작 (marker)
> ```

> ⚠️ **함정** (T-04b): "실행 중 0" 은 **순간**이다. 스레드 1개에 a1 실행 중 + a2 대기열이면, a1 이 끝나는 순간 callback 이 불리고 lifecycle 은 다음으로 넘어간다. a2 는 ③ 의 `shutdownNow()` 에 끊긴다. 비동기 작업이 다음 비동기 작업을 넘기는 체인에서도 같은 틈이 생긴다 → [05](05-chain-and-drain.md).

> ✗→✓ **오해**: "기본값이면 종료 이벤트 때 바로 접수를 닫고 거절한다"
> → 6.1.4 이후 `ThreadPoolTaskExecutor` 는 `strictEarlyShutdown=false` 가 기본이라 접수를 닫지 않는다 (T-04d). 6.1 이전 글(예: Baeldung)은 "기본은 interrupt" 라고 적는데, 지금 버전과 맞지 않는다.

## waitForTasksToCompleteOnShutdown (T-05)

```java
// ExecutorConfigurationSupport (6.2)
public void destroy() { shutdown(); }                 // ③ 에서 불림
public void shutdown() {
    this.executor.shutdown();                         // 접수 마감 (대기열은 계속 실행)
    awaitTerminationIfNecessary(this.executor);       // awaitTerminationMillis 만큼 대기, 넘기면 warn 만
}
```

> 📊 **측정** (2026-10-14, T-05, `./gradlew s2`) — 풀 2개에 1.5s 작업, await 1s
> ```
> [   13ms] ② pool-a lifecycle stop 시작
> [   13ms] ② pool-a lifecycle stop 완료       ← 같은 ms. 기다리지 않는다
> [   13ms] ② redis(phase 0) stop              ← 작업이 도는 중에 Redis 가 멈춘다
> [   13ms] ③ destroy 단계 시작 (marker)
> [   13ms] ③ pool-b destroy 시작               ← 생성 역순: pool-b 먼저
>   spring  TracingThreadPoolTaskExecutor - Timed out while waiting for executor 'poolB' to terminate
> [ 1019ms] ③ pool-b destroy 끝                 ← 1초 뒤. 작업은 끊지 않았다
> [ 1020ms] ③ pool-a destroy 시작               ← pool-b 를 다 기다린 뒤에야 시작
> [ 1515ms]   task a1 끝
> [ 1515ms]   task b1 끝                        ← pool-a 를 기다리는 동안 pool-b 작업도 마저 끝났다
> [ 1515ms] ③ pool-a destroy 끝
> ```

- 기다리는 곳이 **③** 이다. 그때는 ② 에서 멈추는 자원(Redis 등)이 이미 멈춰 있다 → [04](04-resources.md).
- 풀마다 상한이 따로 걸리고 **차례로** 기다린다. 풀 4개 × 30초면 최악 120초다. 다만 뒤 풀도 앞 풀을 기다리는 동안 자기 작업을 계속 실행하므로, 보통은 가장 느린 풀이 끝나는 시각 정도에 끝난다.
- 아직 자기 destroy 차례가 오지 않은 풀은 **계속 접수**한다. 접수를 닫는 곳은 자기 `destroy()` 하나뿐이다.

> 📖 **근거** — Javadoc 원문 (`setWaitForTasksToCompleteOnShutdown`)
> > The executor will not go through a coordinated lifecycle stop phase then but rather only stop and wait for task completion on its own shutdown.
>
> (`setAcceptTasksAfterContextClose`)
> > … replacing the early soft shutdown in the concurrent managed stop phase with a serial soft shutdown in the executor's destruction step, with individual awaiting according to the "awaitTerminationSeconds" property.
>
> - [ExecutorConfigurationSupport Javadoc (6.2.x)](https://docs.spring.io/spring-framework/docs/6.2.x/javadoc-api/org/springframework/scheduling/concurrent/ExecutorConfigurationSupport.html)
> - [ThreadPoolTaskExecutor Javadoc — setStrictEarlyShutdown](https://docs.spring.io/spring-framework/docs/6.2.x/javadoc-api/org/springframework/scheduling/concurrent/ThreadPoolTaskExecutor.html)
> - [spring-framework #30831 — executor 가 SmartLifecycle 로 일시정지·재개하게 된 6.1 변경](https://github.com/spring-projects/spring-framework/issues/30831)

## 진짜 SIGTERM 으로 보기

`./scripts/02-sigterm-demo.sh wait|default|drain` 은 풀에 "400ms 마다 Redis 를 부르는 작업" 을 넣고 SIGTERM 을 보낸다. 종료는 `SpringContextShutdownHook` 스레드에서 진행된다.

> 📊 **측정** (2026-10-14, `./scripts/02-sigterm-demo.sh wait`)
> ```
> [ 1216ms] [pool-a-1                 ]   redis 호출 4회차 → 성공
> >>> kill -TERM
> [ 1329ms] [SpringContextShutdownHook] ② pool-a lifecycle stop 시작
> [ 1330ms] [SpringContextShutdownHook] ② pool-a lifecycle stop 완료
> [ 1330ms] [SpringContextShutdownHook] ② redis(phase 0) stop → 이후 연결 거절
> [ 1330ms] [SpringContextShutdownHook] ③ pool-a destroy 시작
> [ 1619ms] [pool-a-1                 ]   redis 호출 5회차 → 실패 … has been STOPPED
>   … 8회차까지 실패
> [ 3239ms] [SpringContextShutdownHook] ③ pool-a destroy 끝
> ```
> `default` 는 ② 에서 작업 끝(3237ms)까지 기다린 뒤 Redis 를 멈춰 8회 모두 성공했고, `drain` 도 8회 모두 성공했다.

## strictEarlyShutdown (T-06)

종료 이벤트 때 `shutdown()` 을 불러 접수를 닫는다. 이후 넘긴 작업은 `TaskRejectedException` 이다. `ThreadPoolTaskScheduler` 의 6.1 기본 동작과 같다.
