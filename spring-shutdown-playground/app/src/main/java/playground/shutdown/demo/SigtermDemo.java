package playground.shutdown.demo;

import org.springframework.context.annotation.AnnotationConfigApplicationContext;
import playground.shutdown.executor.Tasks;
import playground.shutdown.executor.TracingThreadPoolTaskExecutor;
import playground.shutdown.resource.FakeRedisConnectionFactory;
import playground.shutdown.timeline.Timeline;

/**
 * 진짜 SIGTERM 으로 종료 순서를 본다. 테스트는 context.close() 를 직접 부르고, 여기서는 JVM shutdown hook 이 부른다.
 *
 * <p>풀에 "400ms 마다 Redis 를 부르는 작업" 하나를 넣어 두고 SIGTERM 을 기다린다.
 * 타임라인에서 Redis 호출이 어느 단계부터 실패하는지 보면 된다.
 *
 * <pre>
 * 사용: ./scripts/02-sigterm-demo.sh [wait|default|drain]
 * </pre>
 */
public final class SigtermDemo {

    private SigtermDemo() {
    }

    public static void main(String[] args) throws InterruptedException {
        String scenario = args.length > 0 ? args[0] : "wait";
        Class<?> config = switch (scenario) {
            case "default" -> DemoConfigs.DefaultMode.class;
            case "drain" -> DemoConfigs.IdleDrain.class;
            default -> DemoConfigs.WaitForTasks.class;
        };

        AnnotationConfigApplicationContext context = new AnnotationConfigApplicationContext(config);
        context.registerShutdownHook();   // SIGTERM → JVM shutdown hook → context.close()
        Timeline.reset();

        TracingThreadPoolTaskExecutor pool = context.getBean("poolA", TracingThreadPoolTaskExecutor.class);
        FakeRedisConnectionFactory redis = context.getBean(FakeRedisConnectionFactory.class);
        pool.execute(() -> {
            for (int i = 1; i <= 8; i++) {
                Tasks.attempt("redis 호출 " + i + "회차", () -> redis.get("k"));
                if (!Tasks.sleepQuietly(400)) {
                    Timeline.record("  task interrupt 됨");
                    return;
                }
            }
            Timeline.record("  task 끝");
        });

        Timeline.record("시나리오=" + scenario + " PID=" + ProcessHandle.current().pid() + " — SIGTERM 을 기다린다");
        Thread.sleep(Long.MAX_VALUE);
    }
}
