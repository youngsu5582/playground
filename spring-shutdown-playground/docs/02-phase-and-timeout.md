# 02. phase 와 timeout-per-shutdown-phase

`SmartLifecycle.getPhase()` 가 ② 단계 안의 순서를 정한다. **시작은 작은 phase 부터, 종료는 큰 phase 부터.**
같은 phase 의 빈은 한 묶음으로 `stop(callback)` 을 받고, 묶음 전체의 callback 이 올 때까지 기다린다.

## 생태계의 phase 사다리

| phase | 빈 | 역할 | 근거 |
|---|---|---|---|
| `Integer.MAX_VALUE` | Rabbit 리스너 컨테이너 | 일을 만드는 쪽 | spring-rabbit `AbstractMessageListenerContainer` |
| `MAX − 100` | Kafka 리스너 컨테이너 | 일을 만드는 쪽 | spring-kafka `AbstractMessageListenerContainer.DEFAULT_PHASE` |
| `MAX − 1024` (2147482623) | 웹 graceful | 일을 만드는 쪽 | Boot `WebServerGracefulShutdownLifecycle` |
| `MAX − 2048` (2147481599) | 웹 서버 정지 | 일을 만드는 쪽 | Boot `WebServerStartStopLifecycle` |
| `MAX / 2` (1073741823) | `ThreadPoolTaskExecutor` · `ThreadPoolTaskScheduler` | 일을 처리하는 쪽 | `ExecutorConfigurationSupport.DEFAULT_PHASE` (6.2) |
| `0` | `LettuceConnectionFactory`, 일반 `Lifecycle` | 일이 쓰는 자원 | spring-data-redis 3.2+ |
| `Integer.MIN_VALUE` | Rabbit `CachingConnectionFactory`, Kafka `DefaultKafkaProducerFactory` | 일이 쓰는 자원 | spring-rabbit · spring-kafka |

**만드는 쪽 → 처리하는 쪽 → 자원** 순서로 멈춘다. Spring 6.2 Javadoc 이 executor 의 phase 를 이렇게 설명한다.

> executor/scheduler beans into … a later shutdown phase while still leaving room for regular Lifecycle components with the common phase 0. … for stopping after other SmartLifecycle implementations.

> ✗→✓ **오해**: "Lifecycle 을 구현하지 않은 빈은 phase 0 이다"
> → lifecycle 대상이 아니다. phase 가 없고, ③ destroy 만 받는다. phase 0 은 `SmartLifecycle` 이 아닌 일반 `Lifecycle` 의 값이다.

## timeout-per-shutdown-phase 의 정확한 뜻 (T-03)

**phase 묶음마다** callback 을 기다리는 상한이다. 앱 전체 종료 시간이 아니다. 시간이 지나면 남은 빈을 그대로 두고 다음 phase 로 넘어간다.

> 📊 **측정** (2026-10-14, T-03, `./gradlew s1`) — callback 을 끝내 부르지 않는 빈(phase 100), timeout 500ms
> ```
> [    0ms] ② stuck(phase 100) stop 시작 — callback 을 부르지 않는다
>   spring  DefaultLifecycleProcessor - Shutdown phase 100 ends with 1 bean still running after timeout of 500ms: [stuck]
> [  511ms] ② stop phase=0 after-stuck
> ```

| 어디서 정하나 | 기본값 |
|---|---|
| Spring Framework `DefaultLifecycleProcessor.setTimeoutPerShutdownPhase` | 10초 (6.2 소스 `timeoutPerShutdownPhase = 10000`) |
| Spring Boot `spring.lifecycle.timeout-per-shutdown-phase` | Boot 가 덮어쓴다 |

> ⚠️ **함정**: 레퍼런스 문서는 기본값을 30초로 적고 있지만 6.2 소스는 10초다. Boot 를 쓰면 Boot 설정값이 적용된다.

> 💡 **실무**: ECS 는 SIGTERM 뒤 `stopTimeout`(EC2 기본 30초)이 지나면 SIGKILL 을 보낸다. phase 마다 상한이 따로 걸리고 ③ destroy 대기까지 더해지므로, **모든 대기의 합**이 stopTimeout 안에 들어야 한다.
> ```
> graceful(phase timeout) + 풀 비우기 + 빈 정리 여유 ≤ ECS stopTimeout
> ```

> 📖 **근거**
> - [ExecutorConfigurationSupport Javadoc — DEFAULT_PHASE](https://docs.spring.io/spring-framework/docs/6.2.x/javadoc-api/org/springframework/scheduling/concurrent/ExecutorConfigurationSupport.html)
> - [Spring Boot — Graceful Shutdown](https://docs.spring.io/spring-boot/3.3/reference/web/graceful-shutdown.html)
> - [안종혁 — Graceful Shutdown 과 Async 쓰레드 풀](https://dkswhdgur246.tistory.com/102) (timeout-per-shutdown-phase 실험이 같은 결론)
