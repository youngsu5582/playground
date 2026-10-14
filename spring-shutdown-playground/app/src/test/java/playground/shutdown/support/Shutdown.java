package playground.shutdown.support;

import org.springframework.context.ConfigurableApplicationContext;
import playground.shutdown.executor.TracingThreadPoolTaskExecutor;

import java.util.Collection;
import java.util.List;
import java.util.concurrent.TimeUnit;

/**
 * 컨텍스트를 닫고, 그 컨텍스트의 풀 스레드가 모두 끝날 때까지 기다린다.
 * 타임라인은 static 이라, 닫힌 뒤에도 잠깐 살아 있는 풀 스레드가 다음 테스트의 타임라인에 이벤트를 남길 수 있다.
 */
public final class Shutdown {

    private Shutdown() {
    }

    public static void closeAndSettle(ConfigurableApplicationContext context) {
        // 닫힌 컨텍스트에서는 빈을 꺼낼 수 없어 먼저 모아 둔다
        Collection<TracingThreadPoolTaskExecutor> pools = List.copyOf(context.getBeansOfType(TracingThreadPoolTaskExecutor.class).values());
        context.close();
        for (TracingThreadPoolTaskExecutor pool : pools) {
            try {
                pool.getThreadPoolExecutor().awaitTermination(5, TimeUnit.SECONDS);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                return;
            }
        }
    }
}
