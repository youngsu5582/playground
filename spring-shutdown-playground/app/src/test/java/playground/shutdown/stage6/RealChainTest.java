package playground.shutdown.stage6;

import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.context.annotation.AnnotationConfigApplicationContext;
import org.springframework.context.annotation.Configuration;
import org.testcontainers.junit.jupiter.Testcontainers;
import playground.shutdown.executor.Pools;
import playground.shutdown.executor.TracingThreadPoolTaskExecutor;
import playground.shutdown.stage6.chain.Holds;
import playground.shutdown.stage6.chain.JobEvents;
import playground.shutdown.stage6.chain.JobStore;
import playground.shutdown.stage6.chain.RequestStatus;
import playground.shutdown.stage6.infra.ChainInfra;
import playground.shutdown.stage6.infra.SpringLogTap;
import playground.shutdown.support.Outcome;
import playground.shutdown.support.Shutdown;
import playground.shutdown.timeline.Timeline;

import java.time.Duration;

import static org.assertj.core.api.Assertions.assertThat;
import static playground.shutdown.support.TimelineQuery.happened;
import static playground.shutdown.support.TimelineQuery.result;

/**
 * stage6: 실서비스 모양의 비동기 체인을 진짜 Redis · RabbitMQ · PostgreSQL 위에 올리고,
 * 종료가 체인 한가운데를 끊으면 코드 · DB · 큐 · 로그에 무엇이 남는지 예측한다.
 *
 * <h2>체인</h2>
 * <pre>
 * 테스트(= API)  요청 행 저장 (REQUESTED) → Requested 이벤트 발행
 *   pool-a  create   (실서비스의 createTask)   @Async @Transactional @EventListener
 *                    job 3건 저장 → Created 이벤트 발행 → 메서드 반환 → 커밋
 *   커밋 뒤          Spring 이 AFTER_COMMIT 리스너를 부른다. @Async 라서 pool-a 에 넘긴다
 *   pool-a  produce  (실서비스의 produceTask)  @Async @TransactionalEventListener(AFTER_COMMIT)
 *                    Redis 사용자 대기열에 RPUSH → 맨 앞이면 Rabbit 에 발행
 *   각 단계의 catch 는 실패를 요청 행에 FAILED 로 남긴다 (markFailed)
 * </pre>
 * stage4 의 "A 가 B 를 넘긴다" 를 실서비스 코드 모양으로 바꾼 것이다.
 * 다른 점: B(produce)를 넘기는 쪽이 내 코드가 아니라 Spring 의 커밋 후 콜백이다.
 *
 * <h2>시나리오</h2>
 * 체인이 끊기는 곳은 두 군데다. 테스트 하나가 한 곳을 맡는다.
 * <pre>
 * T-10b  넘기는 순간에 끊긴다     create 의 커밋이 "풀이 접수를 닫은 직후" 로 밀렸다 → 커밋 뒤 콜백이 produce 를 넘기면?
 * T-10c  넘어간 뒤에 끊긴다       produce 는 이미 돌고 있는데, Redis 에 닿는 순간이 ③ 으로 밀렸다 → RPUSH 는?
 * </pre>
 *
 * <h2>구성 클래스를 읽는 법</h2>
 * 장면 하나는 세 가지로 만든다. 구성 클래스(맨 아래)와 {@code requestThenShutdown} 의 인자를 함께 본다.
 * <pre>
 * mode() · awaitTermination()  풀의 종료 설정. 둘 다 PR 설정 (waitForTasks(true) + 1초)
 * holds()                      체인의 어느 줄에서 멈춰, 종료가 어느 단계에 올 때까지 기다리게 하나
 *                                beforeCommit  = create 가 커밋하기 직전 (트랜잭션은 열린 채)
 *                                beforeEnqueue = produce 가 Redis 에 넣기 직전
 *                              실서비스의 "저장이 오래 걸린다" · "발행 전에 할 일이 길다" 를 sleep 대신 종료 이벤트로 맞춘 것이다
 * requestThenShutdown(         요청을 넣고, shutdownAfter 가 타임라인에 찍히면 종료(context.close)를 시작한다
 *     config, shutdownAfter)   shutdownAfter 를 빼면 "  create 시작" 이 찍힌 뒤
 *
 * 테스트  구성                          멈추는 곳 → 다시 진행하는 순간                    종료 시작
 * T-10b   CommitAfterPoolClosedConfig   create 커밋 직전 → pool-a 가 shutdown() 된 직후   create 시작 뒤
 * T-10c   ProduceInDestroyConfig        produce 의 RPUSH 직전 → ③ pool-a destroy 시작    produce 시작 뒤
 * </pre>
 *
 * <h2>질문이 가리키는 것</h2>
 * <pre>
 * "  create 시작" / "  create 실패 처리"        create 가 시작됨 / create 의 catch 가 돎
 * "  tx 커밋 완료"                               create 의 트랜잭션이 커밋됨
 * "  produce 시작" / "  produce 실패 처리"    produce 가 시작됨 / produce 의 catch 가 돎
 * result("redis push") · result("rabbit publish")   produce 가 큐에 넣어 본 결과
 * result("create markFailed") · result("produce markFailed")   catch 가 DB 에 FAILED 를 써 본 결과
 * 보기: {@link Outcome} (SUCCESS · FAILURE · NOT_ATTEMPTED) · {@link RequestStatus} (REQUESTED · FAILED)
 * "  spring ERROR: …" · "  spring WARN: …"      Spring 이 남긴 로그 ({@link SpringLogTap})
 * ChainInfra.jobCount · requestStatus · redisLength · rabbitDepth   종료 뒤 새 연결로 본 DB · Redis · Rabbit
 * </pre>
 *
 * <p>규칙: 실행하기 전에 {@code todo()} 를 내 예측으로 바꾼다. Docker 가 없으면 건너뛴다.
 */
@Testcontainers(disabledWithoutDocker = true)
class RealChainTest {

    private static final Duration WAIT = Duration.ofSeconds(5);
    private static final String USER = "user-1";

    private SpringLogTap springLog;

    @BeforeEach
    void setUp() {
        ChainInfra.reset();
        Timeline.reset();
        springLog = SpringLogTap.attach();
    }

    @AfterEach
    void tearDown() {
        springLog.detach();
    }

    /**
     * <b>시나리오 — 넘기는 순간에 끊긴다.</b>
     * 실서비스로 치면: 저장이 오래 걸려 createTask 의 커밋이 배포 종료 ③ 까지 밀렸다.
     *
     * <pre>
     * 구성  {@link CommitAfterPoolClosedConfig} — PR 설정 풀
     *       create 는 커밋 직전에 멈춰, pool-a 가 shutdown() 될 때까지 기다린다
     *
     * 순서  1. 테스트가 요청 행을 저장하고 Requested 를 발행한다 → pool-a 에서 create 시작
     *       2. create: job 3건 저장 → Created 발행 → 멈춰 기다림 (트랜잭션은 열린 채, 아직 커밋 전)
     *       3. 그사이 테스트가 context.close() → ① → ② (Redis · Rabbit stop) → ③ pool-a destroy: shutdown()
     *       4. create 가 다시 진행해 반환 → 커밋 → 커밋 뒤 콜백이 produce 를 pool-a 에 넘긴다     ← 여기부터가 질문
     *       5. 종료가 끝나면 새 연결로 DB · Redis · Rabbit 을 본다
     * </pre>
     *
     * <b>확인하는 것</b>: 접수를 닫은 풀에 "커밋 뒤 콜백" 이 다음 작업을 넘길 때,
     * 그 결과를 누가 받고(create 의 catch? Spring?) 시스템에 무엇이 남는지(DB · Redis · Rabbit · 로그).
     *
     * <p>보려는 것: "커밋 뒤 @Async" 한 단계가 끊겼을 때, 그 흔적이 catch · DB · 큐 · 로그 중 어디에 남는지 따라갈 수 있는지
     */
    @Test
    @DisplayName("T-10b PR 설정: create 가 풀이 접수를 닫은 직후에 커밋하면, 커밋 뒤의 produce 는")
    void waitForTasksProduceAfterCommit() throws InterruptedException {
        long requestId = requestThenShutdown(CommitAfterPoolClosedConfig.class);

        // Q1 produce 는 시작됐나?
        // -> destroy 가 시작되며, shutdown 상태이므로 접수를 받지 않는다.
        assertThat(happened("  produce 시작")).isEqualTo(false);
        // Q2 create 의 catch 블록이 돌았나?
        // create 로직은 정상적으로 동작했다.
        // -> Transaction 커밋은 되었으나, TransactionalEventListener 에서 태스크를 넣을 떄 TaskRejectedException
        assertThat(happened("  create 실패 처리")).isEqualTo(false);

        // Q3 종료 뒤 DB 에 이 요청의 job 행은 몇 건이고, 요청 상태는 무엇인가? (보기: RequestStatus)
        // 종료되더라도, 그전에 처리된 create 로직은 제대로 수행되어있다.
        assertThat(ChainInfra.jobCount(requestId)).isEqualTo(3);
        assertThat(ChainInfra.requestStatus(requestId)).isEqualTo(RequestStatus.REQUESTED);

        // Q4 종료 뒤 사용자 대기열(Redis) 길이와 Rabbit 큐의 메시지 수는?
        // -> Q1 에서 이어진다. produce 가 시작도 못 했으니 아무도 넣지 않았다.
        assertThat(ChainInfra.redisLength(USER)).isEqualTo(0);
        assertThat(ChainInfra.rabbitDepth()).isEqualTo(0);

        // Q5 Spring 이 ERROR 로그를 남겼나?
        assertThat(happened("  spring ERROR")).isEqualTo(true);
    }

    /**
     * <b>시나리오 — 넘어간 뒤에 끊긴다.</b>
     * 실서비스로 치면: produceTask 는 이미 돌고 있는데, 발행 전에 할 일(조회 · 조립)이 길어
     * Redis 에 닿는 순간이 배포 종료 ③ 까지 밀렸다.
     *
     * <pre>
     * 구성  {@link ProduceInDestroyConfig} — T-10b 와 같은 PR 설정 풀
     *       produce 는 Redis 에 넣기 직전에 멈춰, "③ pool-a destroy 시작" 이 찍힐 때까지 기다린다
     *       종료는 produce 가 시작된 걸 본 뒤에 시작한다 (requestThenShutdown 의 shutdownAfter = "  produce 시작")
     *
     * 순서  1. 테스트가 요청 행을 저장하고 Requested 를 발행한다
     *       2. create: job 3건 저장 → Created 발행 → 반환 → 커밋 (종료 전이다)
     *       3. 커밋 뒤 콜백이 produce 를 pool-a 에 넘기고, produce 가 시작된다 → 멈춰 기다림 (Redis 에 닿기 전)
     *       4. 그사이 테스트가 context.close() → ① → ② (Redis · Rabbit stop) → ③ pool-a destroy
     *       5. produce 가 다시 진행해 RPUSH → (맨 앞이면) Rabbit 발행 을 시도한다              ← 여기부터가 질문
     *       6. 종료가 끝나면 새 연결로 DB · Redis · Rabbit 을 본다
     * </pre>
     *
     * <b>확인하는 것</b>: ② 에서 멈춘 진짜 LettuceConnectionFactory 를 ③ 에서 쓰려 할 때 체인의 각 줄이 어떻게 되는지,
     * 그 결과를 produce 의 catch 가 DB 에 남길 수 있는지. T-10b 와 같은 질문(DB · 큐)이 어떻게 달라지는지도 비교한다.
     *
     * <p>종료를 produce 가 시작된 뒤에 시작하는 이유: create 를 종료 도중에 커밋시키면, produce 가 접수되느냐가
     * Lettuce 가 멈추는 데 걸리는 시간(약 100ms)에 달린다. 그 경합을 없애고 "넘어간 뒤" 만 본다.
     *
     * <p>보려는 것: 커밋 뒤 작업이 "넘어가긴 했는데 자원이 먼저 멈춘" 경우, 실패가 어디서 나고 무엇이 그걸 기록하는지 — T-10b 와 무엇이 다른지
     */
    @Test
    @DisplayName("T-10c PR 설정: 종료 전에 넘어간 produce 가 ③ 에서야 대기열에 넣으면")
    void waitForTasksProduceRunsInDestroy() throws InterruptedException {
        long requestId = requestThenShutdown(ProduceInDestroyConfig.class, "  produce 시작");

        // Q1 produce 의 Redis RPUSH 와 Rabbit 발행은 각각 어떻게 됐나? (보기: Outcome)
        // -> Redis 가 실패하고, MQ 발행은 시도조차 되지 않았다.
        assertThat(result("redis push")).isEqualTo(Outcome.FAILURE);
        assertThat(result("rabbit publish")).isEqualTo(Outcome.NOT_ATTEMPTED);

        // Q2 produce 의 catch 블록이 돌았나? 돌았다면 그 안의 markFailed(DB 쓰기)는 어떻게 됐나? (보기: Outcome)
        // -> produce 가 Redis 예외 덕분에 실패했다.
        assertThat(happened("  produce 실패 처리")).isEqualTo(true);
        // -> DB 처리는 destory 시점에 남아있으므로, 성공한다.
        assertThat(result("produce markFailed")).isEqualTo(Outcome.SUCCESS);

        // Q3 종료 뒤 DB 에 이 요청의 job 행은 몇 건이고, 요청 상태는 무엇인가? (보기: RequestStatus)
        // -> (실측) job 은 종료 전에 커밋된 그대로 3건, produce 의 catch 가 FAILED 를 남겼다.
        assertThat(ChainInfra.jobCount(requestId)).isEqualTo(3);
        assertThat(ChainInfra.requestStatus(requestId)).isEqualTo(RequestStatus.FAILED);

        // Q4 종료 뒤 사용자 대기열(Redis) 길이와 Rabbit 큐의 메시지 수는?
        // -> (실측) RPUSH 가 실패했으니 대기열도 큐도 비어 있다.
        assertThat(ChainInfra.redisLength(USER)).isEqualTo(0);
        assertThat(ChainInfra.rabbitDepth()).isEqualTo(0);
    }

    /**
     * 요청 하나를 넣고, create 가 시작된 걸 본 뒤 컨텍스트를 닫는다. 요청 id 를 돌려준다.
     */
    private static long requestThenShutdown(Class<?> config) throws InterruptedException {
        return requestThenShutdown(config, "  create 시작");
    }

    /**
     * 요청 하나를 넣고, shutdownAfter 가 타임라인에 찍힌 뒤 컨텍스트를 닫는다. 요청 id 를 돌려준다.
     */
    private static long requestThenShutdown(Class<?> config, String shutdownAfter) throws InterruptedException {
        AnnotationConfigApplicationContext context = new AnnotationConfigApplicationContext(config);
        long requestId = context.getBean(JobStore.class).newRequest(USER);
        context.publishEvent(new JobEvents.Requested(requestId, USER, 3));
        Timeline.awaitEvent(shutdownAfter, WAIT);

        Shutdown.closeAndSettle(context);
        return requestId;
    }

    // ---------------------------------------------------------------- 구성

    /**
     * T-10b 의 장면. PR 설정 풀에서 create 의 커밋을 "pool-a 가 shutdown() 된 직후" 로 미룬다.
     * produce 는 멈추지 않는다.
     */
    @Configuration
    static class CommitAfterPoolClosedConfig extends ChainConfig {
        @Override
        protected Pools.Mode mode() {
            return Pools.Mode.WAIT_FOR_TASKS;
        }

        @Override
        protected Holds holds(TracingThreadPoolTaskExecutor poolA) {
            // "③ pool-a destroy 시작" 을 찍은 뒤에 shutdown() 이 불린다. 실제로 닫힐 때까지 기다려 경합을 없앤다
            return Holds.beforeCommit(Holds.Hold.until("③ pool-a destroy 시작")
                    .and(() -> poolA.getThreadPoolExecutor().isShutdown()));
        }
    }

    /**
     * T-10c 의 장면. PR 설정 풀에서 produce 의 RPUSH 를 "③ pool-a destroy 시작" 까지 미룬다.
     * create 는 멈추지 않는다 — 종료 전에 커밋까지 끝난다 (종료 시작 시점은 테스트의 requestThenShutdown 이 정한다).
     */
    @Configuration
    static class ProduceInDestroyConfig extends ChainConfig {
        @Override
        protected Pools.Mode mode() {
            return Pools.Mode.WAIT_FOR_TASKS;
        }

        @Override
        protected Holds holds(TracingThreadPoolTaskExecutor poolA) {
            return Holds.beforeEnqueue(Holds.Hold.until("③ pool-a destroy 시작"));
        }
    }
}
