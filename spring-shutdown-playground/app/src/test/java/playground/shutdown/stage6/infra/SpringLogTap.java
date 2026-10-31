package playground.shutdown.stage6.infra;

import ch.qos.logback.classic.Level;
import ch.qos.logback.classic.LoggerContext;
import ch.qos.logback.classic.spi.ILoggingEvent;
import ch.qos.logback.classic.spi.IThrowableProxy;
import ch.qos.logback.core.AppenderBase;
import org.slf4j.LoggerFactory;
import playground.shutdown.timeline.Timeline;

import java.util.List;

/**
 * Spring 이 남기는 WARN 이상 로그를 타임라인에 "  spring {레벨}: {메시지} ({예외})" 로 옮긴다.
 * 코드의 catch 가 아니라 Spring 내부에서 처리된 실패도 타임라인에서 보이게 하려는 것이다.
 */
public final class SpringLogTap extends AppenderBase<ILoggingEvent> {

    /** logback.xml 에서 additivity=false 인 하위 로거는 위로 올라오지 않으므로 따로 붙인다. */
    private static final List<String> LOGGERS = List.of("org.springframework", "org.springframework.scheduling.concurrent");

    public static SpringLogTap attach() {
        LoggerContext context = (LoggerContext) LoggerFactory.getILoggerFactory();
        SpringLogTap tap = new SpringLogTap();
        tap.setContext(context);
        tap.start();
        LOGGERS.forEach(name -> context.getLogger(name).addAppender(tap));
        return tap;
    }

    public void detach() {
        LoggerContext context = (LoggerContext) getContext();
        LOGGERS.forEach(name -> context.getLogger(name).detachAppender(this));
        stop();
    }

    @Override
    protected void append(ILoggingEvent event) {
        if (!event.getLevel().isGreaterOrEqual(Level.WARN)) {
            return;
        }
        IThrowableProxy thrown = event.getThrowableProxy();
        String cause = thrown == null ? "" : " (" + simpleName(thrown.getClassName()) + ")";
        Timeline.record("  spring " + event.getLevel() + ": " + event.getFormattedMessage() + cause);
    }

    private static String simpleName(String className) {
        return className.substring(className.lastIndexOf('.') + 1);
    }
}
