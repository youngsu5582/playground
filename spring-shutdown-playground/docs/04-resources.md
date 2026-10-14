# 04. 자원은 각자 다른 단계에서 닫힌다

어느 단계에서 닫히는지는 **그 클래스가 무엇을 구현했는지**로 정해진다. `Lifecycle` 이면 ② 에서 `stop()`, `DisposableBean`·`close()` 면 ③ 에서 destroy. 둘 다 구현하면 두 단계에서 한 번씩 불린다.

| 클래스 | 구현 | ② stop() | ③ destroy | ③ 에서 돌던 작업이 쓰면 |
|---|---|---|---|---|
| `LettuceConnectionFactory` (Redis) | SmartLifecycle phase 0 + DisposableBean | client 해제, 상태 STOPPED | 상태 DESTROYED | **거절** (`assertStarted()`) |
| `CachingConnectionFactory` (Rabbit) | SmartLifecycle phase MIN + DisposableBean | 연결 끊음 (`resetConnection`) | `stopped = true` | 자기 destroy 전까지 **재연결해서 동작** |
| `DefaultKafkaProducerFactory` | SmartLifecycle phase MIN + DisposableBean | producer 닫음 | producer 닫음 | 다음 send 때 새로 만듦 (이 저장소에서 미확인) |
| `HikariDataSource` (DB) | `Closeable` 만 | 없음 | `close()` | 자기 close 전까지 동작 |

이 저장소의 가짜 자원(`FakeRedis`·`FakeMq`·`FakeDataSource`)은 위 표의 **종료 동작만** 흉내 낸다. 진짜 Lettuce 로도 같은 결과인지는 stage5(T-09)가 확인한다.

> 📊 **측정** (2026-10-14, T-07b, `./gradlew s3`) — PR 설정, 풀이 ③ 에서 기다리기 시작한 순간 자원 사용
> ```
> [   15ms] [Test worker] ② redis(phase 0) stop → 이후 연결 거절
> [   15ms] [Test worker] ② mq(phase MIN) stop → 연결 끊음, 다음 요청 때 재연결
> [   16ms] [Test worker] ③ destroy 단계 시작 (marker)
> [   16ms] [Test worker] ③ pool-a destroy 시작
> [   18ms] [pool-a-1   ]   redis → 실패 IllegalStateException: FakeRedisConnectionFactory has been STOPPED
> [   18ms] [pool-a-1   ]   mq 재연결
> [   18ms] [pool-a-1   ]   mq → 성공 published:m
> [   18ms] [pool-a-1   ]   db → 성공 1
> [   18ms] [Test worker] ③ pool-a destroy 끝
> [   18ms] [Test worker] ③ db close                ← DB 는 풀 뒤에 닫혔다 (생성 역순)
> ```
> T-09a 는 진짜 Lettuce 로 `LettuceConnectionFactory has been STOPPED. Use start() to initialize it` 를 낸다.

| 시나리오 | Redis | MQ | DB |
|---|---|---|---|
| T-07a 기본값 (② 에서 대기) | 성공 | 성공 | 성공 |
| T-07b PR 설정 (③ 에서 대기) | **실패** | 성공 (재연결) | 성공 |
| T-07c PR 설정 + DataSource 를 풀보다 늦게 생성 | **실패** | 성공 | **실패** |
| T-07d · T-07e drain (② MAX/2−1 에서 비움) | 성공 | 성공 | 성공 |

> ⚠️ **함정**: T-07b 에서 DB 가 성공한 건 **우연**이다. ③ 은 생성 역순이고, executor 빈은 DataSource 에 의존하지 않는다. 설정 클래스가 늘거나 주입 관계가 바뀌면 T-07c 처럼 조용히 뒤집힌다.

## 버전에 따라 정답이 바뀌었다

| Spring Data Redis | LettuceConnectionFactory | Redis 가 닫히는 단계 |
|---|---|---|
| 3.1.x | `InitializingBean`, `DisposableBean` 뿐 | ③ destroy |
| 3.2.x 부터 | `SmartLifecycle` 추가 (phase 0) | **② lifecycle** |

3.1 까지는 Redis 도 ③ 에서 닫혀서, 풀이 `awaitTermination` 으로 destroy 루프를 붙잡아 두면 Redis 도 같이 살아 있었다 (생성 순서가 맞는다면). 그래서 "`waitForTasksToCompleteOnShutdown(true)` + `setAwaitTerminationSeconds()`" 는 오래 정답이었고, 검색하면 지금도 이 방법이 나온다. Data Redis 3.2 부터 Redis 가 ② 로 옮겨 가면서 이 방법이 Redis 에는 통하지 않게 됐다. 컴파일 에러도 경고도 없다.

> 💡 **실무**: 종료 동작도 의존성 계약의 일부다. 메이저 업그레이드 때 stage3 같은 종료 테스트가 있으면 이런 변화가 드러난다.

> 📖 **근거**
> - [LettuceConnectionFactory Javadoc 3.1.x](https://docs.spring.io/spring-data/redis/docs/3.1.x/api/org/springframework/data/redis/connection/lettuce/LettuceConnectionFactory.html) · [3.2.x](https://docs.spring.io/spring-data/redis/docs/3.2.x/api/org/springframework/data/redis/connection/lettuce/LettuceConnectionFactory.html) — "You can stop and restart this connection factory if needed."
> - [ExecutorConfigurationSupport Javadoc — setWaitForTasksToCompleteOnShutdown](https://docs.spring.io/spring-framework/docs/6.2.x/javadoc-api/org/springframework/scheduling/concurrent/ExecutorConfigurationSupport.html): "in order to keep up other resources that your tasks may need, set the awaitTerminationSeconds property" — ③ 의 자원만 해당한다
