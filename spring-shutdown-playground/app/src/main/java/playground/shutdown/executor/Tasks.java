package playground.shutdown.executor;

import org.springframework.core.task.TaskRejectedException;
import playground.shutdown.timeline.Timeline;

import java.util.concurrent.Callable;
import java.util.concurrent.Executor;

/**
 * 풀에 넣을 작업과, 작업 안에서 자원을 써 보는 도구. 모든 결과를 타임라인에 남긴다.
 */
public final class Tasks {

    private Tasks() {
    }

    /** millis 동안 일하는 작업. 시작·끝·interrupt 를 남긴다. */
    public static Runnable sleeping(String name, long millis) {
        return () -> {
            Timeline.record("  task " + name + " 시작");
            if (sleepQuietly(millis)) {
                Timeline.record("  task " + name + " 끝");
            } else {
                Timeline.record("  task " + name + " interrupt 됨");
            }
        };
    }

    /** 풀에 넣는다. 거절되면 예외 대신 타임라인에 남긴다. */
    public static void submit(Executor executor, String name, Runnable task) {
        Timeline.record("  submit " + name);
        try {
            executor.execute(task);
        } catch (TaskRejectedException e) {
            Timeline.record("  submit " + name + " 거절됨 (TaskRejectedException)");
        }
    }

    /** 자원을 한 번 써 보고 성공·실패를 남긴다. */
    public static void attempt(String name, Callable<?> call) {
        try {
            Timeline.record("  " + name + " → 성공 " + call.call());
        } catch (Exception e) {
            Timeline.record("  " + name + " → 실패 " + e.getClass().getSimpleName() + ": " + e.getMessage());
        }
    }

    /** 잠든다. interrupt 되면 false. */
    public static boolean sleepQuietly(long millis) {
        try {
            Thread.sleep(millis);
            return true;
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            return false;
        }
    }
}
