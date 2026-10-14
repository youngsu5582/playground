# 학습 지도 — spring-shutdown-playground

**3줄 요약**
1. Spring 은 **종료 이벤트 → Lifecycle stop(phase 큰 순) → Bean destroy(생성 역순)** 순서로 꺼진다. 세 단계는 겹치지 않는다.
2. `@Async` 풀은 기본값이면 **②** 에서 실행 중 작업을 기다리고, `waitForTasksToCompleteOnShutdown(true)` 를 켜면 **③** 에서 기다린다. Redis(Lettuce)는 ② 에서 멈추므로 ③ 에서 도는 작업은 Redis 를 못 쓴다.
3. 풀은 **② 안에서, 일을 만드는 쪽이 멈춘 뒤·자원이 멈추기 전에** 비워야 한다. 반드시 끝나야 하는 작업이라면 종료 설정이 아니라 아웃박스로 푼다.

## 권장 읽는 순서

| # | 노트 | 한 줄 훅 | 테스트 |
|---|---|---|---|
| 01 | [종료의 세 단계](01-three-stages.md) | `@PreDestroy` 는 언제, 어느 스레드에서, 몇 개씩 불리나 | T-01 · T-01b · T-02 |
| 02 | [phase 와 timeout-per-shutdown-phase](02-phase-and-timeout.md) | 30초는 "앱 종료 30초" 가 아니라 "phase 묶음마다 최대 30초" | T-03 |
| 03 | [ThreadPoolTaskExecutor 의 종료 방식](03-executor-modes.md) | 같은 풀이 설정 하나로 ② 에서 기다리기도, ③ 에서 기다리기도 한다 | T-04 ~ T-06 |
| 04 | [자원은 각자 다른 단계에서 닫힌다](04-resources.md) | Redis 만 실패하는 이유는 클래스가 무엇을 구현했느냐에 있다 | T-07 · T-09 |
| 05 | [비동기 체인과 drain 설계](05-chain-and-drain.md) | 접수를 먼저 닫으면 "다음 작업" 이 조용히 사라진다 | T-08 |

## 기준 버전

Spring Framework 6.2.19 · Spring Data Redis 3.5.12 · Lettuce 6.6 (Spring Boot 3.5.x 조합).
**Spring Boot 3.2 이전(Framework 6.0 · Data Redis 3.1)은 결과가 다르다.** [04](04-resources.md#버전에-따라-정답이-바뀌었다) 참고.
