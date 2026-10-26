plugins { `java-library` }

// 진짜 미들웨어를 띄우는 공용 도구. 레슨은 이 모듈만 testImplementation 으로 가져다 쓴다.
dependencies {
    api(platform("org.testcontainers:testcontainers-bom:1.21.4"))
    api("org.testcontainers:postgresql")
    api("org.postgresql:postgresql:42.7.4")
    api(platform("org.junit:junit-bom:5.11.4"))
    api("org.junit.jupiter:junit-jupiter-api")
    api("org.assertj:assertj-core:3.27.2")
}
