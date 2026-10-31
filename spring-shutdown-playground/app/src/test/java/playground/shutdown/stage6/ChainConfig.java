package playground.shutdown.stage6;

import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.context.ApplicationEventPublisher;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.DependsOn;
import org.springframework.context.support.DefaultLifecycleProcessor;
import org.springframework.data.redis.connection.RedisStandaloneConfiguration;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.transaction.annotation.EnableTransactionManagement;
import playground.shutdown.executor.Pools;
import playground.shutdown.executor.TracingThreadPoolTaskExecutor;
import playground.shutdown.stage6.chain.Holds;
import playground.shutdown.stage6.chain.JobCreateListener;
import playground.shutdown.stage6.chain.JobProduceListener;
import playground.shutdown.stage6.chain.JobStore;
import playground.shutdown.stage6.chain.UserJobQueue;
import playground.shutdown.stage6.infra.ChainInfra;
import playground.shutdown.stage6.infra.TracedResources;
import playground.shutdown.support.DestroyMarker;

import java.time.Duration;

/**
 * stage6 테스트가 공유하는 컨텍스트 구성. 하위 @Configuration 이 풀의 종료 설정과 "어느 순간에 커밋·발행할지" 만 바꾼다.
 *
 * <pre>
 * 생성 순서: redis · rabbit · dataSource → poolA → 리스너 → destroyMarker
 * destroy 순서는 그 역순: destroyMarker → poolA → (자원들)
 * </pre>
 * 프록시는 Spring Boot 기본값처럼 클래스 기반(CGLIB)이다.
 */
@EnableAsync(proxyTargetClass = true)
@EnableTransactionManagement(proxyTargetClass = true)
public abstract class ChainConfig {

    protected abstract Pools.Mode mode();

    /** WAIT_FOR_TASKS 일 때 풀이 destroy 에서 기다리는 상한. */
    protected Duration awaitTermination() {
        return Duration.ofSeconds(1);
    }

    /** create 의 커밋 · produce 의 발행을 종료의 어느 순간까지 미룰지. 기본은 미루지 않는다. */
    protected Holds holds(TracingThreadPoolTaskExecutor poolA) {
        return Holds.none();
    }

    /** spring.lifecycle.timeout-per-shutdown-phase 에 해당한다. 테스트가 빨리 끝나게 1초로 둔다. */
    @Bean(name = "lifecycleProcessor")
    public DefaultLifecycleProcessor lifecycleProcessor() {
        DefaultLifecycleProcessor processor = new DefaultLifecycleProcessor();
        processor.setTimeoutPerShutdownPhase(1000);
        return processor;
    }

    @Bean
    public TracedResources.Redis redis() {
        return new TracedResources.Redis(
                new RedisStandaloneConfiguration(ChainInfra.REDIS.getHost(), ChainInfra.REDIS.getFirstMappedPort()));
    }

    @Bean
    public StringRedisTemplate redisTemplate() {
        return new StringRedisTemplate(redis());
    }

    @Bean
    public TracedResources.Rabbit rabbit() {
        TracedResources.Rabbit factory = new TracedResources.Rabbit(ChainInfra.RABBIT.getHost(), ChainInfra.RABBIT.getAmqpPort());
        factory.setUsername(ChainInfra.RABBIT.getAdminUsername());
        factory.setPassword(ChainInfra.RABBIT.getAdminPassword());
        return factory;
    }

    @Bean
    public RabbitTemplate rabbitTemplate() {
        return new RabbitTemplate(rabbit());
    }

    @Bean
    public TracedResources.Db dataSource() {
        TracedResources.Db dataSource = new TracedResources.Db();
        dataSource.setJdbcUrl(ChainInfra.POSTGRES.getJdbcUrl());
        dataSource.setUsername(ChainInfra.POSTGRES.getUsername());
        dataSource.setPassword(ChainInfra.POSTGRES.getPassword());
        dataSource.setMaximumPoolSize(2);
        return dataSource;
    }

    @Bean
    public TracedResources.TxManager transactionManager() {
        return new TracedResources.TxManager(dataSource());
    }

    @Bean
    public JobStore jobStore() {
        return new JobStore(new JdbcTemplate(dataSource()));
    }

    @Bean
    @DependsOn({"redis", "rabbit", "dataSource"})
    public TracingThreadPoolTaskExecutor poolA() {
        return Pools.create("pool-a", mode(), awaitTermination());
    }

    @Bean
    public Holds chainHolds() {
        return holds(poolA());
    }

    @Bean
    public UserJobQueue userJobQueue() {
        return new UserJobQueue(redisTemplate(), rabbitTemplate());
    }

    @Bean
    public JobCreateListener jobCreateListener(ApplicationEventPublisher events) {
        return new JobCreateListener(jobStore(), events, chainHolds());
    }

    @Bean
    public JobProduceListener jobProduceListener() {
        return new JobProduceListener(userJobQueue(), jobStore(), chainHolds());
    }

    @Bean
    @DependsOn({"poolA", "jobCreateListener", "jobProduceListener"})
    public DestroyMarker destroyMarker() {
        return new DestroyMarker();
    }
}
