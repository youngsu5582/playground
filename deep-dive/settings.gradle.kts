rootProject.name = "deep-dive"

// 공용 도구
include("testkit")

// 레슨 자동 등록: NN-트랙/lNN-레슨/build.gradle.kts 가 있으면 서브프로젝트가 된다.
// 새 레슨은 폴더만 만들면 된다 — 여기를 고칠 필요 없음.
rootDir.listFiles { f -> f.isDirectory && f.name.matches(Regex("""\d\d-.+""")) }
    ?.sortedBy { it.name }
    ?.forEach { track ->
        track.listFiles { f -> f.isDirectory && f.name.matches(Regex("""l\d\d-.+""")) && File(f, "build.gradle.kts").exists() }
            ?.sortedBy { it.name }
            ?.forEach { lesson -> include(":${track.name}:${lesson.name}") }
    }
