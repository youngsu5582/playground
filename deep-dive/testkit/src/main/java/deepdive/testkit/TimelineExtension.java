package deepdive.testkit;

import org.junit.jupiter.api.extension.AfterAllCallback;
import org.junit.jupiter.api.extension.AfterEachCallback;
import org.junit.jupiter.api.extension.ExtensionContext;

/**
 * 테스트가 끝나면 모아 둔 {@link Timeline} 을 찍는다.
 *
 * <p>레슨 테스트에 따로 달 필요 없다 — {@code META-INF/services} 로 등록돼 있고,
 * testkit 의 {@code junit-platform.properties} 가 자동 등록(autodetection)을 켠다. Gradle 이든 IntelliJ 든 같다.
 */
public final class TimelineExtension implements AfterEachCallback, AfterAllCallback {

    @Override
    public void afterEach(ExtensionContext context) {
        Timeline.flush();
    }

    /** @BeforeAll · @AfterAll 처럼 테스트 밖에서 남긴 줄. */
    @Override
    public void afterAll(ExtensionContext context) {
        Timeline.flush();
    }
}
