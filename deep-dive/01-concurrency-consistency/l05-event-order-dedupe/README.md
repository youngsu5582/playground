# 01.05 이벤트 중복 · 순서

> **완료 기준**: 예측 9문항을 먼저 적고 돌려 전부 초록 · 구현 테스트 초록 · NOTES 를 채우고 꼬리질문 5개를 해설 보기 전에 답한다 · "같은 이벤트가 두 번 오고 늦은 과거가 올 때, messageId 와 version 이 각각 무엇을 막고, inbox 기록과 상태 갱신을 왜 한 트랜잭션에 묶어야 하나"를 그림 없이 3분 안에 설명한다.

공고 연결 — "유실 없는 데이터 정합성 · 이벤트 기반 연동". 결제 · 배송 · 권한 이벤트는 전부 at-least-once 로 오고, 순서도 보장되지 않는다.
(참고) 이 레슨은 이전 실험장 `order-flow-playground` docs/04-event-ordering.md · stage4 (배송 이벤트), `comic-entitlement-playground` PROBLEM.md Stage 2 (messageId · version 두 축, Kotlin)를 옮긴 것이다. 여기서는 **이벤트가 DB 에 도착한 순간**만 진짜 PostgreSQL 위에서 판정한다. Kafka 는 없다 — 브로커와 inbox 를 잇는 이야기는 02.03(outbox · 멱등 소비).

---

## ① 질문 · 첫 예측 — 20분

1. at-least-once 라서 같은 이벤트가 두 번 오면 무슨 일이 생기나? 상태가 같은 값으로 덮이니 문제없지 않나?
2. 늦게 도착한 과거 이벤트(v2)가 최신(v3) 뒤에 오면 최종 상태는? 무엇으로 막나?
3. messageId 와 version 은 왜 **둘 다** 필요한가? 하나만 있으면 각각 무엇이 샌다?
4. "처리했다" 는 inbox 기록과 상태 갱신이 다른 트랜잭션이면, 그 사이에 실패했을 때 재전달에서 무엇이 깨지나?
5. 두 컨슈머가 같은 키(같은 배송 건, 같은 messageId)를 동시에 처리하면 DB 는 어떻게 줄을 세우나?

> **이어서 첫 예측**: 질문에 종이로 답해 NOTES §0 에 옮긴 뒤, `DedupePredictTest.java` 의 예측 칸 `"?"` 를 **감으로** 채워 `./gradlew 01.05-predict` 를 돌린다. 틀려도 된다 — 틀린 문항이 ② 를 읽는 이유가 된다. PROGRESS 의 "예측 적중"은 이 첫 예측으로 센다.

## ② 원리 — 70분

![이벤트 중복 · 순서](diagrams/event-dedupe.svg)

<sub>편집: [diagrams/event-dedupe.excalidraw](diagrams/event-dedupe.excalidraw) · 다시 그리기(만든 사람용 · 레슨 폴더에서): `python3 -I diagrams/draw.py`</sub>

1차 자료 (블로그 요약 말고 이것부터):

공식 문서에서 아래 "찾을 것" 문장을 직접 찾아 표시하고, 한 줄로 번역해 NOTES 나 여백에 적어 둔다.

| 자료 | 읽으면서 찾을 것 |
|---|---|
| [개념 정리 docs/](docs/README.md) | **필수 02 · 03 · 04** 를 읽으며 ① 에서 틀린 문항이 왜 틀렸는지 찾는다 (나머지 글은 심화 — 레슨을 마친 뒤 · 면접 전). 공식 문서 행은 docs 가 링크하는 곳에서 같이 연다 · 예측 답은 접힌 칸에만 |
| [PostgreSQL 16 · INSERT](https://www.postgresql.org/docs/16/sql-insert.html) | ON CONFLICT DO NOTHING 의 정의 · 명령 태그 count = "삽입 또는 갱신된 행 수" (Q04) · DO UPDATE 의 WHERE 는 "충돌이 후보로 확인된 뒤 마지막에" 평가된다 · "원자적 INSERT 또는 UPDATE 결과" 보장 |
| [PostgreSQL 16 · 13.2 Transaction Isolation](https://www.postgresql.org/docs/16/transaction-iso.html) | Read Committed 에서 같은 행을 고치려는 두 번째 UPDATE 는 첫째의 커밋/롤백을 기다리고, 커밋되면 **갱신된 버전에 WHERE 를 다시 평가**한다 (Q07 · Q08) |
| [Kafka 문서 · Design (message delivery semantics)](https://kafka.apache.org/documentation/#semantics) | Message Delivery Semantics 절을 직접 읽고 아래 질문의 답이 되는 문장을 찾는다 — ① at-least-once 는 어떤 상황에서 같은 메시지를 두 번 받게 되나? ② idempotent producer 가 막아 주는 중복의 범위는 어디까지인가(프로듀서 재시도에 한정되는가, 컨슈머 쪽 재전달도 막는가)? |
| 『데이터 중심 애플리케이션 설계』 11장 | 정확히 한 번(exactly-once)은 "at-least-once + 멱등 처리" 로 만든다는 관점 · 멱등성 키 |

## ③ 재현 — 30분 · 세 가지 손 작업

파일 경로는 이 레슨 폴더(`01-concurrency-consistency/l05-event-order-dedupe/`) 기준이다. 명령은 두 곳에서 친다.

```bash
# deep-dive 폴더에서 — ./gradlew 는 전부 여기서
./gradlew 01.05-predict
./gradlew 01.05-implement
```

```bash
# deep-dive 폴더에서 레슨 폴더로 들어간 뒤 — observe 스크립트는 여기서
cd 01-concurrency-consistency/l05-event-order-dedupe
observe/up.sh
```

IntelliJ 로 한다면: deep-dive 폴더를 Gradle 프로젝트로 열고(코드를 바꾼 뒤 Gradle 창에서 Reload), 테스트 메서드 옆 ▶ 로 한 문항씩 돌려도 된다. 자세히는 [GUIDE.md](../../GUIDE.md).

| 작업 | 실행 | 무엇을 |
|---|---|---|
| **예측** (되짚기) | `./gradlew 01.05-predict` | `src/test/java/deepdive/c01/l05/DedupePredictTest.java` 의 Q01~Q09(9문항 · 예측 칸 18곳)을 ① 에서 감으로 적었다. 틀린 문항을 ② 를 읽은 뒤 되짚어 다시 적고 초록으로 만든다 (NOTES §1 에 한 줄). 한 문항씩 돌리는 법: [GUIDE](../../GUIDE.md) §2-3. 출력의 A/B 타임라인은 예측을 적은 문항만 보인다 |
| **구현** (코드) | `./gradlew 01.05-implement` | 구현 대상 `src/main/java/deepdive/c01/l05/EventApplier.java` 의 `TODO(구현)` — inbox 선점 + version 조건부 반영을 한 트랜잭션으로. 실패 메시지가 "정합성 깨짐: 같은 메시지가 5번 반영됐다" 부터 알려 준다. 검사는 `src/test/java/deepdive/c01/l05/EventApplierImplementTest.java` |
| **관찰** (진짜 엔진) | `observe/up.sh` → [observe/SCRIPT.md](observe/SCRIPT.md) | psql 두 개로 inbox 중복 · 역전 · 따로 커밋 vs 한 트랜잭션 |

테스트는 진짜 PostgreSQL 16 컨테이너(Testcontainers)에서 돈다. Docker 가 떠 있어야 한다.

한 문항만 (deep-dive 폴더에서): `./gradlew :01-concurrency-consistency:l05-event-order-dedupe:predict --tests '*Q05*'`

구현 테스트는 7개다. **결과 검사** 5개: 같은 messageId 5개 동시 · 순서를 섞은 version 1..10 순차 · version 1..10 동시 · stale 재전달 · 같은 version 의 다른 메시지. **가드** 2개: 정상 순서 · 반영 중 예외 후 재전달.
빈칸 상태(inbox · version 없이 그대로 덮어쓰기)에서 **빨간 5개**: 같은 messageId 5개 동시 · version 섞어 순차 · version 동시 · stale 재전달 · 같은 version 의 다른 메시지.
**초록 2개(가드)**: 정상 순서, 그리고 "예외 후 재전달" — 후자는 한 문장짜리 구현에서는 롤백할 inbox 기록이 없어서다. inbox 를 도입한 뒤 **따로 커밋**하면 이 테스트가 빨개진다.

## ④ 내 말로 — 20분

1. [NOTES.md](NOTES.md) — 틀린 예측 · 3분 설명 · 꼬리질문 5개(답을 먼저 쓰고 해설과 비교) · §6 내 실무와 연결(권장 — 내가 일하는 서비스를 떠올려 한 줄씩)
2. `/kata:discuss 이벤트 중복과 순서 역전, inbox 멱등 처리` — 면접관 역할의 꼬리질문
3. 버텼으면 [../../PROGRESS.md](../../PROGRESS.md) 에 테스트 ✅ · 내 말로 ✅

---

💡 **실무**: 중복 거르기의 핵심은 "처리했다는 기록" 과 "처리 결과" 가 **같이 커밋되거나 같이 사라지는 것**이다.
기록만 남고 결과가 없으면 재전달이 영영 건너뛰고, 결과만 있고 기록이 없으면 중복이 반영된다.
그리고 inbox 는 무한히 자란다 — 보관 기간(예: 브로커 재전달이 가능한 기간보다 길게)을 정하고 지우는 배치가 따로 필요하다. 처리 자체를 멱등하게(`WHERE version < :v`) 만들어 두면 inbox 가 뚫려도 최종 상태는 안전하다.

정답 patch: [../../solutions/01.05.patch](../../solutions/01.05.patch) — 구현 정답과 **예측 답**이 들어 있다. 예측 · 구현을 끝낸 뒤 연다 (deep-dive 폴더에서 `less solutions/01.05.patch`). 내 코드와 비교한다.
