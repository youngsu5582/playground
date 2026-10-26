import org.gradle.api.tasks.testing.logging.TestExceptionFormat

// 레슨 = ":NN-트랙:lNN-레슨" 프로젝트. 공통 의존성·테스트 설정·단축 태스크를 여기서 건다.
val lessonPattern = Regex(""":(\d\d)-[^:]+:l(\d\d)-.+""")

subprojects {
    if (childProjects.isNotEmpty() && !lessonPattern.matches(path)) return@subprojects // 트랙 폴더 자체는 빌드 대상 아님

    apply(plugin = "java")
    repositories { mavenCentral() }
    extensions.configure<JavaPluginExtension> { toolchain { languageVersion = JavaLanguageVersion.of(21) } }
    tasks.withType<JavaCompile>().configureEach {
        options.encoding = "UTF-8"
        options.compilerArgs.add("-parameters")
    }

    dependencies {
        "testImplementation"(platform("org.junit:junit-bom:5.11.4"))
        "testImplementation"("org.junit.jupiter:junit-jupiter")
        "testImplementation"("org.assertj:assertj-core:3.27.2")
        "testRuntimeOnly"("org.junit.platform:junit-platform-launcher")
        if (lessonPattern.matches(path)) {
            "testImplementation"(project(":testkit"))
        }
    }

    fun Test.readable() {
        useJUnitPlatform()
        // 60초 제한 · 타임라인 출력(TimelineExtension)은 testkit 의 junit-platform.properties 에 있다 — IntelliJ 로 돌려도 같게.
        testLogging {
            events("passed", "skipped", "failed")
            exceptionFormat = TestExceptionFormat.FULL
            showStackTraces = false   // 실패 메시지가 핵심 — 스택은 소음
            showCauses = false
            showStandardStreams = true // Session 타임라인(A: BEGIN … / B: UPDATE …)을 보여 준다
        }
    }
    tasks.withType<Test>().configureEach { readable() }

    // 레슨 안: ./gradlew :…:predict (예측) · :…:implement (구현)
    if (lessonPattern.matches(path)) {
        val sourceSets = extensions.getByType<SourceSetContainer>()
        mapOf("predict" to "*PredictTest", "implement" to "*ImplementTest").forEach { (name, pattern) ->
            tasks.register<Test>(name) {
                group = "deep-dive"
                description = "$pattern 만"
                testClassesDirs = sourceSets["test"].output.classesDirs
                classpath = sourceSets["test"].runtimeClasspath
                filter { includeTestsMatching(pattern) }
                outputs.upToDateWhen { false }
            }
        }
        tasks.named<Test>("test") { outputs.upToDateWhen { false } }
    }
}

// 루트 단축 태스크 — 문서의 레슨 번호 그대로:
//   ./gradlew 01.01            레슨 전체          ./gradlew 01.01-predict     예측만
//   ./gradlew 01.01-implement  구현만             ./gradlew 01                트랙 전체
// (줄여 써도 된다: 01.01-pre, 01.01-impl)
gradle.projectsEvaluated {
    val lessons = subprojects.mapNotNull { p -> lessonPattern.matchEntire(p.path)?.let { m -> Triple(p, m.groupValues[1], m.groupValues[2]) } }
    lessons.forEach { (p, track, lesson) ->
        val id = "$track.$lesson"
        tasks.register(id) { group = "deep-dive"; description = "${p.path} 전체 (예측 + 구현)"; dependsOn("${p.path}:test") }
        tasks.register("$id-predict") { group = "deep-dive"; description = "${p.path} 예측 테스트"; dependsOn("${p.path}:predict") }
        tasks.register("$id-implement") { group = "deep-dive"; description = "${p.path} 구현 테스트"; dependsOn("${p.path}:implement") }
    }
    lessons.groupBy { it.second }.forEach { (track, ls) ->
        tasks.register(track) { group = "deep-dive"; description = "트랙 $track 전체"; dependsOn(ls.map { "${it.first.path}:test" }) }
    }
}
