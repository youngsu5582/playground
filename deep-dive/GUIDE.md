# 따라 하기 가이드

처음 보는 사람이 01.01 을 끝까지 한 번 돌 수 있게 순서대로 적었다. 개념 설명은 [LOOP.md](LOOP.md) · 각 레슨 README 에 있고, 여기는 **명령 · 화면 · 막혔을 때**만 다룬다.
아래 출력 예시는 실제로 돌려서 가져온 것이다 (시간 · 포트 번호 · 줄 순서는 실행마다 다르다).

---

## 1. 준비 확인

```bash
# 아무 폴더에서
java -version     # 첫 줄이 21 로 시작해야 한다: openjdk version "21.…"
docker info       # "Client:" 아래에 "Server:" 가 이어지면 데몬이 떠 있는 것
```

- `java` 가 21 이 아니다 → JDK 21 을 설치한다. Gradle 이 21 toolchain 을 요구한다.
- `docker info` 가 Server 를 못 찾는다(데몬 연결 오류) → Rancher Desktop 또는 Docker Desktop 을 켜고, 준비가 끝날 때까지 기다린 뒤 다시 친다. 테스트는 Docker 가 꺼져 있으면 시작하지 못한다.
- 첫 실행은 `postgres:16-alpine` 이미지를 받느라 느릴 수 있다. 이후에는 레슨 하나가 몇 초 걸린다.

## 2. 처음 한 바퀴 따라 하기 — 01.01 (약 2시간 반)

### 2-1. 빈칸 상태 보관 · 폴더 이동

```bash
# 저장소를 받은 위치(deep-dive 의 부모 폴더)에서
cp -R deep-dive deep-dive-blank   # (권장, 1회) 손대기 전 상태 보관 — 나중에 정답을 돌려 볼 때 쓴다 (§5-4)
cd deep-dive
```

이 뒤의 `./gradlew` 는 모두 이 폴더에서 친다.

### 2-2. ① 질문 · 첫 예측 (20분) — 읽기 전에 감으로

[01.01 README](01-concurrency-consistency/l01-isolation-mvcc/README.md) ① 의 질문 5개에 **종이로** 답하고, 그 답을 [NOTES.md](01-concurrency-consistency/l01-isolation-mvcc/NOTES.md) §0 에 옮긴다. 틀려도 된다.
이어서 §2-3 처럼 예측 칸 `"?"` 를 **감으로** 채워 돌린다 — 읽기 전이니 틀리는 게 정상이고, 틀린 문항이 ② 를 읽는 이유가 된다. PROGRESS 의 "예측 적중" 은 이 첫 예측으로 센다.

### 2-3. ① 첫 예측 — 돌리기 전에 답을 적는다

> 예측을 안 적은(`"?"`) 문항은 실제 값을 **어디에도 찍지 않는다** — 실패 메시지도, A/B 타임라인도 숨긴다. 그러니 `./gradlew 01.01-predict` 를 먼저 전체로 돌려 봐도 답이 새지 않는다 (10개 모두 빨강, 정상). 예측을 적으면 맞든 틀리든 타임라인이 보인다.

1. 테스트 파일을 연다: `01-concurrency-consistency/l01-isolation-mvcc/src/test/java/deepdive/c01/l01/IsolationPredictTest.java`
2. `Q01_READ_COMMITTED_같은_SELECT_를_두_번` 메서드의 `String 예측 = "?";` 를 내 답으로 바꾼다. 질문은 바로 아래 `Predict.확인(…)` 의 첫 인자에 있다 (`A 의 두 번째 SELECT 결과는? (처음엔 100 · 답: 숫자)`).
   한 문항에 예측 칸이 둘 이상이면(예: `예측_대기` · `예측_행수`) **모두 적고** 돌린다. 앞 칸이 틀리면 그 자리에서 멈추고 타임라인을 보여 주는데, 거기에 뒤 칸의 답도 찍혀 있기 때문이다.
3. 그 문항만 돌린다.

```bash
# deep-dive 폴더에서
./gradlew :01-concurrency-consistency:l01-isolation-mvcc:predict --tests '*Q01*'
```

(`./gradlew 01.01-predict` 단축 태스크는 `--tests` 를 받지 못한다. 한 문항만 돌릴 때는 위처럼 긴 이름을 쓴다.)

**예측이 틀렸을 때** — 아래처럼 나온다. (첫 예측에서는 이게 흔하다. 바로 아래 NOTES §1 에 한 줄 남기고 다음 문항으로 간다.)

```
[예측] 01.01 격리수준 · MVCC — 10문항 > Q01_READ_COMMITTED_같은_SELECT_를_두_번() STANDARD_OUT

    ── Q01 READ COMMITTED — 사이에 남이 커밋하면 ──────────────────────────────────────
    [ +24ms] A  BEGIN ISOLATION LEVEL READ COMMITTED
    [ +27ms] A  SELECT balance FROM account WHERE id = 1                   → 100
    [ +29ms] B  UPDATE account SET balance = 50 WHERE id = 1               → 1행
    [ +30ms] A  SELECT balance FROM account WHERE id = 1                   → 50

[예측] 01.01 격리수준 · MVCC — 10문항 > Q01_READ_COMMITTED_같은_SELECT_를_두_번() FAILED
    org.opentest4j.AssertionFailedError: [
    예측이 빗나갔다 → A 의 두 번째 SELECT 결과는? (처음엔 100 · 답: 숫자)
      내 예측: 100
      왜 다른지 한 줄로 NOTES.md 에 남기자 (틀린 예측이 제일 남는다)]
    expected: "100"
     but was: "50"
```

- 타임라인 읽는 법: `[ +30ms]` 는 문항 시작 후 경과 시간, `A` · `B` 는 세션 이름, `→ 50` 은 결과다. 시간 순서대로 위에서 아래로 읽는다.
- 이 한 줄을 바로 NOTES §1 "틀린 예측" 표에 적는다 (Q · 내 예측 · 실제 — "왜 다른가" 는 ② 를 읽은 뒤 채운다). 예측을 실제 값으로 고쳐 초록으로 만드는 것은 ③ 되짚기에서 한다 (§2-4). PROGRESS 의 "예측 적중" 은 **① 에서 처음 적은 예측**이 맞은 문항 수라, 고친 문항은 적중에 안 든다.

**맞았을 때** — `… PASSED` 와 `BUILD SUCCESSFUL` 이 나온다.

**예측을 안 적고(`"?"`) 돌렸을 때** — 아래처럼 나온다. 그 문항은 빨강이고, 이게 정상이다. 타임라인은 장면 제목만 남기고 숨긴다.

```
    ── Q01 READ COMMITTED — 사이에 남이 커밋하면 ──────────────────────────────────────
      (타임라인 숨김 — 예측을 적고 다시 돌리면 보인다)

[예측] 01.01 격리수준 · MVCC — 10문항 > Q01_READ_COMMITTED_같은_SELECT_를_두_번() FAILED
    java.lang.AssertionError:
    먼저 예측을 적는다 → A 의 두 번째 SELECT 결과는? (처음엔 100 · 답: 숫자)
      테스트 코드의  String 예측 = "?";  를 내 답으로 바꾸고 다시 돌린다.
      (실제 값은 예측을 적은 뒤에야 보여 준다)
```

나머지 9문항도 같은 방식으로 하나씩 적고 돌린다. 다 끝나면 `./gradlew 01.01-predict` 로 10개를 한 번에 돌린다 (빨강이 남아 있는 게 정상이다).

### 2-4. ② 원리 → ③ 틀린 예측 되짚기

**② 원리 (필수 글 분량 · 01.01 은 75분)** — 명령이 없다. README ② 표의 첫 행 [개념 정리 docs/](01-concurrency-consistency/l01-isolation-mvcc/docs/README.md) 에서 **필수** 글(03 · 05)만 읽는다. ① 에서 틀린 문항이 왜 틀렸는지를 찾으며 읽고, 찾으면 NOTES §1 의 "왜" 칸에 한 줄 적는다. 1차 자료를 열어 그림을 그린다. 문항의 답은 docs 에서 `<details>` 로 접혀 있다. 나머지 글은 심화 — 레슨을 마친 뒤 · 면접 전에 읽는다.

**③ 틀린 예측 되짚기** — 틀린 문항의 예측을 실제 값으로 고쳐 그 문항을 초록으로 만든다. 한 문항씩 돌리는 명령은 위 §2-3 과 같다.

**예측 문항의 정답 patch 는 열지 않는다** — `solutions/01.01.patch` 에는 구현 정답과 **예측 답**이 같이 들어 있다. 예측 · 구현이 끝난 뒤에만 연다 (§5-4 참고).

### 2-5. ③ 구현 — TODO(구현)을 채운다

1. **먼저 빨간 상태를 본다** (환경 확인을 겸한다).

```bash
# deep-dive 폴더에서
./gradlew 01.01-implement
```

빈칸 상태의 기대 출력 — 6개 중 5개 실패, 1개 통과(가드)다.

```
[구현] 01.01 Tx.serializable — write skew 막기 > 직렬화_실패가_아닌_오류는_다시_시도하지_않는다() PASSED

[구현] 01.01 Tx.serializable — write skew 막기 > 당직은_동시에_빠져도_항상_1명_이상_남는다() FAILED
    java.lang.AssertionError:
    정합성 깨짐: 1회차에서 당직이 0명이 됐다 (규칙: 항상 1명 이상) — write skew.
      두 트랜잭션이 각자 '2명이니 빠져도 된다'를 보고, 서로 다른 행을 고쳐서 행 락으로는 안 막혔다.
      두 호출의 결과: [true, true]
      고칠 곳: Tx.serializable — SERIALIZABLE 로 돌리고, 40001 이면 처음부터 다시

[구현] 01.01 Tx.serializable — write skew 막기 > 방법_검사_Tx_serializable_은_이름대로_SERIALIZABLE_로_돈다() FAILED
    expected: "serializable"
     but was: "read committed"
…
6 tests completed, 5 failed
BUILD FAILED
```

2. `01-concurrency-consistency/l01-isolation-mvcc/src/main/java/deepdive/c01/l01/Tx.java` 의 `TODO(구현)` 주석을 읽고 `serializable` 메서드를 고친다. 실패 메시지의 "고칠 곳" 줄이 방향을 알려 준다.
3. 고칠 때마다 다시 돌린다 (한 번에 하나씩).
4. 끝나면 6개 모두 `PASSED` 이고 `BUILD SUCCESSFUL` 이 나온다.
5. 그제야 정답 patch 와 내 코드를 비교한다 (§5-4).

### 2-6. ③ 관찰 — psql 두 개

```bash
# 터미널 1 — deep-dive 폴더에서 시작
cd 01-concurrency-consistency/l01-isolation-mvcc
observe/up.sh                                       # "ready — 다음: SCRIPT.md" 가 나오면 준비 끝
observe/psql.sh A

# 터미널 2 — 새 터미널을 열고 deep-dive 폴더에서 시작
cd 01-concurrency-consistency/l01-isolation-mvcc
observe/psql.sh B
```

- [observe/SCRIPT.md](01-concurrency-consistency/l01-isolation-mvcc/observe/SCRIPT.md) 의 장면 표를 순서대로 따라 한다. 표의 A · B 칸 문장을 해당 터미널에 그대로 붙여 넣는다.
- 프롬프트 `A*#` 의 `*` 는 "트랜잭션 안", `!` 는 "실패한 트랜잭션 안(ROLLBACK 해야 함)" 이다.
- 테이블 구조는 `\d on_call` · 목록은 `\dt`. 접속은 컨테이너 안의 psql 이라 로컬에 psql 이 없어도 된다.
- 본 것(메시지 원문 포함)은 NOTES "관찰 메모"(§1-2)에 적는다.

```bash
# 레슨 폴더(01-concurrency-consistency/l01-isolation-mvcc)에서
observe/down.sh   # 컨테이너와 볼륨을 지운다. 다시 up 하면 seed 부터 새로 시작
```

### 2-7. ④ 내 말로 · 기록

1. NOTES §2(내 그림) · §3(3분 설명) · §4(꼬리질문 — **답을 먼저 쓰고** 해설을 연다) · §5(회차 기록)를 채우고, §6(내 실무와 연결 — 권장)에 내가 일하는 서비스(PostgreSQL)를 떠올려 한 줄씩 적는다.
2. [면접 사다리](01-concurrency-consistency/l01-isolation-mvcc/docs/07-interview-ladder.md) — 30초 답 → 2분 답 → 사다리를 소리 내어. 답은 접혀 있다 — 말한 뒤에 펼친다.
3. `/kata:discuss PostgreSQL 격리수준과 MVCC, write skew` — 없으면 아무 AI 에게 "면접관처럼 꼬리질문해 줘".
4. [PROGRESS.md](PROGRESS.md) 에 테스트 ✅ (`./gradlew 01.01` 전부 초록) · 내 말로 ✅ (NOTES 를 채우고 꼬리질문 5개를 해설 전에 답함) 를 체크한다.

## 3. IntelliJ 로 하기

1. **deep-dive 폴더**를 연다 (저장소 루트나 `01-concurrency-consistency` 가 아니라). `settings.gradle.kts` 가 있는 폴더여야 Gradle 프로젝트로 인식한다.
2. 코드를 바꾸거나 처음 열었을 때 Gradle 창(오른쪽 코끼리 아이콘) → 새로고침(Reload All Gradle Projects). JDK 21 이 Gradle JVM 으로 잡혔는지 확인한다 (Settings → Build Tools → Gradle).
3. 테스트 한 문항: `IsolationPredictTest` 에서 메서드 이름 옆 ▶ → Run. 클래스 옆 ▶ 는 10문항 전체다.
4. 출력은 아래쪽 Run 창이다. 문항을 고르면 오른쪽에 그 문항의 출력이 나온다. A · B 타임라인(`[ +24ms] A …`)과 실패 메시지(`예측이 빗나갔다 → …`)가 여기 같이 있다.
5. IntelliJ 가 단축 태스크(`01.01-predict`)가 아니라 JUnit 으로 돌려도 같은 테스트다. 60초 제한(§5-3)과 타임라인 숨김도 똑같이 걸린다.
6. `observe/*.sh` 는 IntelliJ 의 Terminal 탭에서 레슨 폴더로 이동한 뒤 친다.

## 4. 명령 모음

| 명령 | 어디서 | 무엇을 | 언제 |
|---|---|---|---|
| `./gradlew 01.01` | deep-dive | 레슨 전체(예측 + 구현) | 끝났는지 확인할 때 |
| `./gradlew 01.01-predict` | deep-dive | 예측 테스트 전체 | ① 첫 예측을 다 적은 뒤 · ③ 되짚기 뒤 |
| `./gradlew 01.01-implement` | deep-dive | 구현 테스트 전체 | 구현할 때마다 |
| `./gradlew :01-concurrency-consistency:l01-isolation-mvcc:predict --tests '*Q01*'` | deep-dive | 예측 한 문항 | 문항 하나씩 적고 돌릴 때 |
| `./gradlew :01-concurrency-consistency:l04-stock-concurrency:test --tests '*Observation*'` | deep-dive | 01.04 관찰 테스트(측정 표) | 01.04 ③ 에서 |
| `./gradlew 01` | deep-dive | 트랙 01 전체 | 트랙을 마쳤을 때 |
| `observe/up.sh` | 레슨 폴더 | 관찰용 PostgreSQL 컨테이너 시작 | ③ 관찰 시작 |
| `observe/psql.sh A` · `B` · `C` | 레슨 폴더 | 이름 붙은 psql 세션 열기 | 장면마다 터미널을 나눠서 |
| `observe/down.sh` | 레슨 폴더 | 컨테이너와 볼륨 삭제 | 관찰이 끝났을 때 |
| `less solutions/01.01.patch` | deep-dive | 정답 patch 읽기 | 예측 · 구현이 끝난 뒤 |
| `patch -p1 < solutions/01.01.patch` | 빈칸 사본 폴더 | 사본을 정답 상태로 (§5-4) | 정답을 돌려 보고 싶을 때 |

관찰용 포트: 01.01 55432 · 01.02 55433 · 01.03 55434 · 01.04 55435 · 01.05 55436 · 01.06 55437.

## 5. 막혔을 때

### 5-1. Docker 가 꺼져 있다

`docker info` 가 데몬에 연결하지 못한다고 하거나, 테스트가 시작 직후 실패한다 (Testcontainers 가 Docker 환경을 찾지 못했다는 오류가 대표적이다 — 이 문서를 쓰며 Docker 를 끄고 재현해 보지는 않았다). Docker 를 켜고 `docker info` 로 확인한 뒤 다시 돌린다.

### 5-2. 포트 충돌 (5543x)

`observe/up.sh` 가 포트가 이미 사용 중이라 실패한다 (docker 의 "port is already allocated" 류 메시지 — 직접 재현하지는 않았다). 레슨마다 포트가 달라(55432~55437) 레슨끼리는 충돌하지 않는다. 다른 프로그램(예: 로컬 PostgreSQL)이 그 포트를 쓰고 있을 가능성이 크다.

```bash
# 아무 폴더에서
docker ps --filter name=deepdive-     # 떠 있는 관찰 컨테이너 확인
lsof -i :55432                         # 해당 포트를 쓰는 프로세스 확인
```

`docker ps` 에 `deepdive-` 컨테이너가 보이면 그 레슨 폴더에서 `observe/down.sh` 를 친다. 안 보이는데 `lsof` 에 다른 프로세스가 나오면 그 프로그램이 원인이다 — 그것을 끄거나, 내가 쓰지 않는 포트인지 확인한 뒤 정리한다.

### 5-3. 테스트가 60초 뒤 실패한다

틀린 구현이 멈춘 것이다 (무한 재시도 · 풀리지 않는 락 대기). 이 저장소는 테스트 하나에 **60초** 제한을 건다(`testkit/src/main/resources/junit-platform.properties`). 실패는 타임아웃 오류로 보이고, 구현이 락을 쥔 채 기다리거나 재시도를 끝내지 않는지를 의심한다. 실패 메시지가 아니라 **구현 쪽**을 본다.

### 5-4. 정답과 비교하고 싶다 · 정답을 돌려 보고 싶다

**읽어서 비교** — 가장 간단하다. patch 의 `-` 줄이 빈칸, `+` 줄이 정답이다.

```bash
# deep-dive 폴더에서
less solutions/01.01.patch
```

**정답 상태로 돌려 보기** — patch 는 **빈칸 상태 파일**에 맞춰져 있다. 내가 이미 고친 파일에는 들어가지 않는다(`.rej` 파일이 생긴다). 그래서 빈칸 상태 사본에서 한다.

```bash
# deep-dive 폴더의 부모 폴더에서 — 레슨을 시작하기 전에 한 번만
cp -R deep-dive deep-dive-blank            # 빈칸 상태 보관 (커밋해 둬도 된다)

# 정답을 보고 싶을 때
cp -R deep-dive-blank deep-dive-answer
cd deep-dive-answer
patch -p1 < solutions/01.01.patch          # 사본에 정답 적용 — "patching file …" 줄만 나오면 성공
./gradlew 01.01                            # 전부 초록
```

- patch 에는 구현 정답과 **예측 답**이 같이 들어 있다. 예측 · 구현을 끝낸 뒤에 연다.
- 내 코드와의 차이: `diff -r deep-dive/01-concurrency-consistency/l01-isolation-mvcc/src/main deep-dive-answer/01-concurrency-consistency/l01-isolation-mvcc/src/main` (부모 폴더에서).
- 다 보면 `deep-dive-answer` 를 지운다. 원본은 건드리지 않았다.
- 빈칸 사본을 안 떠 뒀다면: 내가 고친 파일만 `.rej` 가 생기고 나머지는 들어간다. 그 파일은 `less solutions/01.01.patch` 로 읽어서 비교한다.
- `git apply solutions/01.01.patch` 도 같은 결과다. 다만 하나라도 안 맞으면 전부 거절하므로, 일부만이라도 넣으려면 `patch -p1` 이 낫다.

### 5-5. 컨테이너 정리

```bash
# 아무 폴더에서
docker ps --filter name=deepdive-      # 관찰 컨테이너 (deepdive-01.01-pg …)
docker ps                              # 테스트가 띄운 postgres:16-alpine 도 보인다. 테스트가 끝나면 자동으로 정리된다
```

관찰 컨테이너는 레슨 폴더의 `observe/down.sh` 로 지운다 (볼륨 포함). 테스트용 컨테이너는 손댈 필요가 없다.
