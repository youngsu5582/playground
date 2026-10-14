# 05. 비동기 체인과 drain 설계

## 체인이 끊기는 경로 (T-08)

실서비스에는 비동기 작업이 다음 비동기 작업을 넘기는 체인이 흔하다.

```
CreateTaskListener   @Async + @Transactional
   └ publishEvent(TaskCreatedEvent)        커밋 뒤
ProduceTaskListener  @Async + @TransactionalEventListener(AFTER_COMMIT)   ← 같은 풀에 제출
```

종료 도중 풀이 접수를 닫은 뒤에 A(CreateTask)가 커밋하면, B(ProduceTask) 제출이 `TaskRejectedException` 으로 거절된다.
그리고 이 예외는 **AFTER_COMMIT 콜백 안에서 나서 로그만 남고 사라진다.**

```java
// TransactionSynchronizationUtils.invokeAfterCompletion (spring-tx 6.2)
try {
    synchronization.afterCompletion(completionStatus);
} catch (Throwable ex) {
    logger.error("TransactionSynchronization.afterCompletion threw exception", ex);   // 삼킨다
}
```

결과적으로 태스크는 DB 에 생성됐는데 큐에 들어가지 않고, 에러 상태도 찍히지 않는다. 폴링이 끝나지 않는다.

| 시나리오 | B 접수 | B 의 결과 |
|---|---|---|
| T-08a PR 설정 | **거절** (풀이 ③ 에서 접수 마감) | 실행 안 됨 |
| T-08b ShutdownFirstDrain | **거절** (drain 이 먼저 접수 마감) | 실행 안 됨 |
| T-08c IdleDrain | 접수 | **성공** — drain 이 B 까지 기다린 뒤 Redis 가 멈춘다 |
| T-08d 기본값 | 접수 | lifecycle 이 B 를 기다리지 않는다 (A 가 끝나 실행 중 0 이 되는 순간 통과) |

> 📊 **측정** (2026-10-14, T-08c, `./gradlew s4`)
> ```
> [   14ms] [Test worker] ② drain(idle 대기) 시작
> [   16ms] [pool-a-1   ]   submit B
> [   16ms] [pool-a-1   ]   task A 끝
> [   17ms] [pool-a-1   ]   task B 시작
> [  322ms] [pool-a-1   ]   B redis → 성공 value-of-k
> [  377ms] [Test worker] ② drain(idle 대기) 끝         ← B 까지 끝난 뒤 (연속 2회 idle 확인)
> [  378ms] [Test worker] ② pool-a lifecycle stop 시작
> [  378ms] [Test worker] ② redis(phase 0) stop
> ```
> T-08a(PR 설정)에서는 같은 자리에서 `submit B 거절됨 (TaskRejectedException)` 이 찍힌다.

## drain 두 가지

| | ShutdownFirstDrain | IdleDrain |
|---|---|---|
| 방식 | 접수 마감 → 하나의 마감 시각까지 `awaitTermination` | 접수 유지 → "실행 중 0 + 대기열 0" 이 연속 2회 관측될 때까지 대기 |
| 체인 작업 | 거절 | 받아서 처리 |
| 접수 마감 | drain 이 한다 | ③ destroy 가 한다 |
| phase | `MAX/2 − 1` (Redis 앞). 풀에 의존하므로 실제로는 첫 풀이 멈추기 직전에 불린다 (아래) | 같음 |

**IdleDrain 을 쓴다.** 연속 2회 확인은 작업이 대기열에서 막 꺼내져 아직 실행 중으로 집계되기 전의 틈을 넘기려는 것이다.

```java
private boolean allIdle() {
    return pools.stream().allMatch(pool -> {
        ThreadPoolExecutor executor = pool.getThreadPoolExecutor();
        return executor.getActiveCount() == 0 && executor.getQueue().isEmpty();
    });
}
```

### 예상과 달랐던 것: drain 이 풀보다 먼저 불린다

drain 의 phase 는 `MAX/2 − 1` 이라 풀(`MAX/2`)보다 **뒤에** 멈출 줄 알았다. 실측은 반대였다. 위 T-08c 에서 `drain 시작` 이 `pool-a lifecycle stop 시작` 보다 앞에 있고, Spring 로그로 보면 `Stopping beans in phase 1073741823`(풀의 phase) 안에서 drain 이 불린다.

이유는 의존 관계다. drain 빈은 `List.of(poolA(), poolB())` 로 풀 빈을 참조하므로 풀에 **의존하는 빈**이 된다. `DefaultLifecycleProcessor.doStop()` 은 어떤 빈을 멈추기 전에 그 빈에 의존하는 빈을 먼저 멈추므로, 첫 풀을 멈추려는 순간 drain 이 phase 와 관계없이 먼저 불린다 ([01 의존 관계와 순서](01-three-stages.md#의존-관계와-순서)). T-05 에서 pool-b(pool-a 에 의존)가 pool-a 보다 먼저 멈춘 것도 같은 규칙이다.

결과에는 문제가 없다. drain 이 여전히 ② 안에서, Redis(phase 0)보다 먼저 끝난다. 다만 **"같은 phase 의 스케줄러가 멈춘 뒤" 라는 보장은 없다.** 스케줄러가 drain 도중에 작업을 넘겨도 IdleDrain 은 받아서 처리하지만, ShutdownFirstDrain 이었다면 거절됐을 것이다. IdleDrain 을 고르는 이유가 하나 더 생긴 셈이다.

> ⚠️ **함정**: IdleDrain 은 웹 서버와 MQ 리스너가 ② 에서 먼저 멈춘다는 전제에 기댄다. 그 전제가 깨져 외부에서 작업이 계속 들어오면 timeout 까지 기다린다. phase 를 `MAX/2 − 1` 로 두는 이유다.

## 종료 설정이 해결하지 못하는 것

종료 설정은 모두 **계획된 종료**에서만 효과가 있다. OOM·크래시·SIGKILL 에는 ② 도 ③ 도 불리지 않는다.
커밋 뒤 메모리에서 비동기로 처리하는 구조는 원리상 "최대 한 번" 이다. 반드시 실행돼야 하는 작업은 저장으로 푼다.

- **트랜잭셔널 아웃박스**: 같은 트랜잭션에서 "보낼 것" 을 DB 에 기록하고, 별도 경로가 발행한다.
- **[Spring Modulith 이벤트 레지스트리](https://docs.spring.io/spring-modulith/reference/1.4/events.html)**: 이벤트를 기록하고, 끝나지 않은 것은 재시작 때 다시 발행한다 (`republish-outstanding-events-on-restart`).
- **스위퍼**: 생성 상태로 N초 넘게 머문 작업을 찾아 다시 넣거나 에러로 닫는다.

> 💡 **실무**: 캐시 evict 처럼 유실돼도 되는 작업은 IdleDrain 으로 충분하다. 태스크 발행·크레딧 복구처럼 유실되면 안 되는 작업은 아웃박스가 근본 해결이고, drain 은 배포 때의 빈틈만 줄인다.
