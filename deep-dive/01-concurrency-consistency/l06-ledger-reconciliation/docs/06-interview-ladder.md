# 06. 면접 사다리 — 원장과 대사

> 외우는 순서: 30초 답 → 2분 답 → 사다리. 답은 접혀 있다 — 먼저 소리 내어 답한다.
> 근거는 문서 01~05 에 있다. 이 문서의 숫자 · 동작은 거기서 확인한 것만 쓴다. 회계 일반 개념은 `(일반 개념 · 해석)` 으로 표시했다.
> **구분**: 심화 — ④ 말하기 연습 · 면접 전.

## 30초 답 (첫 질문용)

**Q. 돈처럼 맞아야 하는 숫자를 어떻게 저장하고, 틀렸을 때 어떻게 알아채나요?**

<details><summary>답</summary>

금액은 `numeric`(앱에서는 `BigDecimal`)에 담습니다. `float` 는 이진 근사값이라 같음 비교가 어긋나고 큰 금액은 센트가 사라집니다. 잔고 컬럼 하나만 두지 않고 거래 내역을 원장에 쌓기만 하는 기록으로 두며, 잔고는 그 합입니다. 이체는 원장 두 줄(−금액 · +금액, 합 0)과 두 잔고 변경을 한 트랜잭션에서 하고, 같은 거래는 거래 id 선점(`INSERT … ON CONFLICT DO NOTHING`)으로 한 번만 반영합니다. 잔고 갱신은 `balance = balance + ?` 로 DB 안에서 하고 두 계좌는 id 순서로 잡아 데드락을 피합니다. 그래도 어긋날 수 있으니 잔고와 원장 합을 `FULL OUTER JOIN` 으로 맞춰 보는 대사로 알아채고, 찾으면 원인을 본 뒤 원장을 고치지 않고 반대 거래를 쌓습니다.
</details>

## 2분 답 (화이트보드 · 그림 없이 말로)

<details><summary>답 (구조: 타입 → 구조 → 규칙 시점 → 기록 → 대사)</summary>

1. **타입**: `float8` 은 IEEE 754 이진 부동소수점이라 1.1 + 2.2 = 3.3 이 거짓이고(실측), 정밀도가 최소 15 자리라 17 자리 금액은 끝자리가 바뀝니다. `numeric(p, s)` 는 십진 정확값이지만 선언한 scale 보다 길면 조용히 반올림하고(ties 는 0 에서 먼 쪽) 그 뒤 정수부가 p − s 자리를 넘으면 에러입니다. 앱도 `double` 을 거치면 안 됩니다.
2. **구조**: 원장은 거래마다 줄을 쌓고(append-only) 잔고는 그 합입니다. 잔고 컬럼은 읽기 요약(캐시)이라 어긋날 수 있습니다. 이체 한 건은 원장 두 줄 + 잔고 두 곳이고, 불변식은 거래별 다리 합 0 · 계좌별 잔고 = 원장 합 · 전체 잔고 합 0 입니다.
3. **규칙 시점**: CHECK 는 한 행만 보고 지연이 안 되어 문장에서 즉시 검사합니다(잔고 ≥ 0). 거래의 다리 합 0 은 두 줄을 넣는 사이엔 깨져 있으니 지연 가능한 constraint trigger(`DEFERRABLE INITIALLY DEFERRED`)로 커밋 때 검사합니다. 대가는 에러가 커밋에서 난다는 것이고, `SET CONSTRAINTS … IMMEDIATE` 로 그 자리에서 검사할 수 있습니다. append-only 는 행 트리거만으로는 TRUNCATE 가 빠집니다.
4. **기록**: 한 트랜잭션에서 거래 id 선점 → 잔고 상대값 갱신(id 순서) → 원장 두 줄 → 커밋. 중복은 오류가 아니라 "이미 처리됨" 을 돌려줍니다. 잔고 부족은 CHECK 가 막고, 선점도 같이 롤백해 같은 id 로 재시도할 수 있게 합니다.
5. **대사**: 내부(잔고 vs 원장 합)와 외부(우리 + 다리 vs 외부 정산 내역). 한쪽에만 있는 줄이 대상이라 `FULL OUTER JOIN`, 합이 NULL 일 수 있어 `COALESCE`. 시차는 허용 지연으로 거르고, 찾은 뒤엔 원인을 보고 반대 거래로 정정합니다.
</details>

## 사다리 — 한 질문에서 꼬리가 이어지는 길

### 갈래 A: "금액을 float 로 저장하면 안 되나요?"

1. Q. 왜 안 되죠?
   <details><summary>답</summary>
   `float8` 은 이진 근사값이라 0.1 · 1.1 같은 십진 소수를 정확히 못 담습니다. 문서 8.1 은 "부정확(inexact)" 이라고 분류하고 같음 비교가 기대대로 안 될 수 있다고 경고하며, 금액에는 `numeric` 을 쓰라고 합니다. 실측으로 `1.1 + 2.2 = 3.3` 이 거짓이었습니다 — 합계를 `=` 로 맞춰 보는 대사가 거짓 경보를 냅니다.
   </details>
2. 꼬리 Q. 그럼 `numeric` 이면 안전한가요?
   <details><summary>답</summary>
   저장과 계산은 정확하지만 끝이 아닙니다. 선언한 scale 보다 긴 값은 조용히 반올림되고(ties 는 0 에서 먼 쪽 — `2.675` → `2.68`), 정수부가 넘치면 에러입니다. 반올림이 먼저라서 `numeric(12, 2)` 에 `9999999999.995` 를 넣으면 반올림 뒤 `10000000000.00` 이 되어 에러입니다(실측). 어디서 몇 자리로 반올림할지는 도메인이 정할 일입니다 (해석).
   </details>
3. 꼬리 Q. 앱에서는요?
   <details><summary>답</summary>
   `BigDecimal` 과 `setBigDecimal` · `getBigDecimal` 로만 주고받고 `double` 을 거치지 않습니다. `double` 은 17 자리 금액에서 센트가 사라집니다(실측: `12345678901234567.89` → `float8` 에서 `1.2345678901234568e+16`). 계산도 `balance = balance + ?` 로 DB 안에서 합니다.
   </details>
4. 꼬리 Q. 최소 단위 정수(센트)를 `bigint` 에 담는 방식과 비교하면?
   <details><summary>답</summary>
   반올림 책임을 앱이 전부 지는 대신 타입 변환 실수가 줄어듭니다. 이 레슨은 `numeric` 으로 갑니다. 어느 쪽이 낫다고 단정하지 않습니다 (일반 개념 · 해석).
   </details>

### 갈래 B: "잔고 컬럼이 있는데 왜 원장이 따로 필요하죠?"

1. Q. 잔고만 있으면 무엇을 잃나요?
   <details><summary>답</summary>
   "왜 이 잔고인가" 의 근거를 잃고, 틀렸는지 알아챌 비교 대상도 잃습니다. 원장은 거래 내역을 쌓기만 하는 기록이고 잔고는 그 합입니다.
   </details>
2. 꼬리 Q. 그럼 잔고 컬럼은 왜 두나요? 어긋나면 어느 쪽을 믿나요?
   <details><summary>답</summary>
   읽을 때 `SUM` 을 안 하려는 요약(캐시)입니다 (일반 개념 · 해석). 쓸 때 두 곳을 같이 바꿔야 해서 어긋날 수 있고, 어긋나면 쌓기만 하는 원장을 근거로 봅니다.
   </details>
3. 꼬리 Q. 이체는 원장에 어떻게 적나요? 합 0 은 누가 지키나요?
   <details><summary>답</summary>
   −금액 · +금액 두 줄입니다 (복식부기의 차변 · 대변 틀을 빌렸습니다 — 일반 개념). 합이 0 이어야 한다는 규칙은 지연 constraint trigger 가 커밋 때 검사합니다. 돈이 들어오고 나가는 상대편은 시스템 계정(id 0)이라 마이너스가 허용됩니다.
   </details>
4. 꼬리 Q. 잘못 올라간 거래는 어떻게 바로잡나요?
   <details><summary>답</summary>
   원장을 UPDATE 로 고치지 않고 반대 방향 거래를 새로 쌓습니다. 이력이 남고 반대 거래도 같은 규칙(합 0 · 멱등)을 지납니다. 이 레슨의 스키마는 원장 UPDATE · DELETE 를 트리거로 막습니다. 순서는 찾고, 원인을 보고, 정정하고, 다시 대사입니다 (일반 개념 · 해석).
   </details>
5. 꼬리 Q. 원장의 UPDATE 를 막는 트리거가 있으면 안전한가요?
   <details><summary>답</summary>
   빈틈이 둘 있습니다. 행 트리거는 `TRUNCATE` 에 불리지 않습니다(문서: TRUNCATE 는 ON DELETE 트리거를 부르지 않고, TRUNCATE 에는 문장 트리거만 만들 수 있음). 막으려면 `BEFORE TRUNCATE … FOR EACH STATEMENT` 를 따로 달아야 합니다(실측). 테이블 소유자는 `ALTER TABLE … DISABLE TRIGGER` 로 트리거를 끌 수도 있습니다(문서 · 실측). 그래서 권한 분리가 같이 필요합니다 (해석).
   </details>

### 갈래 C: "다리 합 0 은 언제 검사하나요? CHECK 로 안 되나요?"

1. Q. CHECK 로 만들 수 없는 이유는?
   <details><summary>답</summary>
   CHECK 는 새 행이나 바뀐 행 하나가 만족해야 하는 조건이고, 문서상 `NOT NULL` 과 함께 지연할 수 없어 행이 삽입될 때 즉시 검사됩니다. 이체는 두 줄을 넣는 동안 합이 0 이 아닌 순간이 있어 즉시 검사로는 정상 이체도 막힙니다.
   </details>
2. 꼬리 Q. 그럼 무엇으로 하죠? 조건은?
   <details><summary>답</summary>
   constraint trigger 입니다. 일반 테이블의 `AFTER ROW` 트리거여야 하고 `DEFERRABLE INITIALLY DEFERRED` 를 줄 수 있습니다(문서: CREATE TRIGGER). 지연 가능한 제약은 UNIQUE · PK · EXCLUDE · FK 와 이 constraint trigger 이고, 지연하면 트랜잭션 끝(커밋 직전)에 검사해 위반이면 트랜잭션이 통째로 실패합니다.
   </details>
3. 꼬리 Q. 지연의 대가는?
   <details><summary>답</summary>
   에러가 규칙을 어긴 문장이 아니라 COMMIT 에서 나서 원인 문장을 찾기 어렵고, 앱은 `commit()` 의 예외도 처리해야 합니다(실측: 두 INSERT 는 성공하고 COMMIT 에서 `P0001`, 줄은 모두 사라짐 — 롤백). 필요하면 `SET CONSTRAINTS ALL IMMEDIATE` 로 그 자리에서 검사하고, 소급 적용됩니다(문서). 이때는 두 줄을 한 문장으로 넣어야 정상 이체가 통과합니다(실측).
   </details>
4. 꼬리 Q. `SET CONSTRAINTS` 가 모든 제약에 듣나요?
   <details><summary>답</summary>
   지연 가능한 제약에만 듣습니다. CHECK 같은 지연 불가 제약에 이름을 주고 `DEFERRED` 로 바꾸려 하면 `constraint "account_check" is not deferrable` 로 거절됩니다(실측). 현재 트랜잭션에서만 유효합니다(문서).
   </details>

### 갈래 D: "같은 거래가 두 번 오거나 동시에 오면요?"

1. Q. 어떻게 한 번만 반영하나요?
   <details><summary>답</summary>
   `INSERT INTO posted_txn (txn_id) VALUES (?) ON CONFLICT DO NOTHING` 으로 확인과 선점을 한 문장으로 합니다. 삽입된 행 수가 1 이면 처음이고 0 이면 이미 처리된 거래입니다(`DUPLICATE`). SELECT 로 확인하고 넣으면 동시에 올 때 둘 다 "없다" 를 봅니다.
   </details>
2. 꼬리 Q. 동시에 같은 id 가 오면 정확히 어떻게 되죠?
   <details><summary>답</summary>
   두 번째 문장은 첫 번째 트랜잭션이 끝나기를 기다립니다. 첫 번째가 커밋하면 건너뛰고(0행), 롤백하면 삽입됩니다(1행) (실측: 약 1.3 초 대기 후 각각 `INSERT 0 0` · `INSERT 0 1`). 그래서 잔고 부족으로 거절할 때 선점도 같이 롤백해야 같은 id 로 재시도할 수 있습니다.
   </details>
3. 꼬리 Q. 호출한 쪽에는 무엇을 돌려주나요?
   <details><summary>답</summary>
   오류가 아니라 "이미 처리됨"(`DUPLICATE`)입니다. 오류로 돌려주면 호출한 쪽이 재시도마다 실패한 줄 압니다. UNIQUE `(txn_id, account_id)` 는 선점을 빠뜨린 코드를 막는 뒤의 안전망입니다.
   </details>
4. 꼬리 Q. 동시 이체에서 잔고가 틀어지지 않게 하려면?
   <details><summary>답</summary>
   읽고 → 앱에서 계산 → 덮어쓰기는 갱신 손실입니다(1000 에서 100 · 200 이체가 800 으로). `UPDATE … SET balance = balance + ?` 한 문장이면 행 락이 줄을 세우고, 기다린 쪽은 갱신된 최신 행에 다시 적용합니다(문서 13.2.1 · 실측: 잔고 85 에서 동시 −60 두 번 중 두 번째는 −35 가 되려다 CHECK 에서 거절).
   </details>
5. 꼬리 Q. 반대 방향 이체가 섞이면요?
   <details><summary>답</summary>
   각자 보내는 쪽부터 갱신하면 락을 엇갈려 잡아 데드락(`40P01`)이 납니다. 엔진이 `deadlock_timeout`(기본 1초) 뒤 순환을 찾아 한쪽을 중단시키고 누가 중단될지는 예측하면 안 됩니다(문서 13.3.4). 방어는 항상 같은 순서로 잡는 것 — 계좌 id 순서로 갱신합니다(실측: 같은 순서면 둘 다 커밋).
   </details>

### 갈래 E: "대사는 어떻게 하나요?"

1. Q. 잔고와 원장의 어긋남을 어떻게 찾죠? 왜 FULL OUTER JOIN 인가요?
   <details><summary>답</summary>
   계좌별 원장 합을 만들어 계좌와 `FULL OUTER JOIN` 한 뒤 `a.id IS NULL OR a.balance <> COALESCE(l.s, 0)` 만 남깁니다. 찾는 것은 한쪽에만 있는 줄(원장 없는 계좌 · 계좌 없는 원장)이고 INNER JOIN 은 그 줄을 못 보며, LEFT JOIN 은 계좌 없는 원장을 못 봅니다(문서 7.2.1.1).
   </details>
2. 꼬리 Q. COALESCE 가 왜 필요하죠?
   <details><summary>답</summary>
   `sum` 은 행이 없으면 NULL 이고(문서 9.21) NULL 과의 `<>` 는 UNKNOWN 이라 WHERE 가 그 줄을 거릅니다. 원장 없이 잔고만 있는 계좌가 조용히 사라지고, 빈 결과는 "이상 없음" 으로 읽힙니다(실측). 거꾸로 잔고 0 에 원장 없는 빈 계좌는 `COALESCE` 덕에 정상으로 빠집니다.
   </details>
3. 꼬리 Q. 외부 대사는요? 어떤 종류가 나오나요?
   <details><summary>답</summary>
   우리 원장의 + 다리(거래당 한 줄)와 외부 정산 내역을 거래 id 로 `FULL OUTER JOIN` 해서 `OURS_ONLY` · `THEIRS_ONLY` · `AMOUNT_DIFFERS` 를 얻습니다. − 다리를 거르지 않으면 부호가 달라 가짜 어긋남이 거래마다 나옵니다(실측).
   </details>
4. 꼬리 Q. `OURS_ONLY` 가 나오면 오류인가요?
   <details><summary>답</summary>
   시차일 수 있습니다. 외부가 아직 안 보냈거나 정산 주기가 달라서입니다. 허용 지연을 두고 시간이 지나도 남는 것만 오류로 올립니다. `AMOUNT_DIFFERS` 는 양쪽에 있는 거래의 값 차이라 시차로 설명되지 않습니다 (일반 개념 · 해석).
   </details>
5. 꼬리 Q. 대사가 못 찾는 것은요? 잔고 합이 0 이 아닌 것만으로 알 수 있는 건?
   <details><summary>답</summary>
   같은 입력으로 두 기록이 함께 틀린 경우(잘못된 금액이 원장과 잔고에 똑같이 들어감)는 못 찾습니다 — 외부 대사가 도움이 됩니다 (해석). 전체 잔고 합이 0 이 아니면 어딘가 어긋났다는 것은 알지만 어디인지는 계좌별 대사가 알려 줍니다(실측: 원장 합 0.00 · 잔고 합 9.00 인 장부).
   </details>
6. 꼬리 Q. 대사 쿼리를 둘로 쪼개 돌리면 문제가 있나요?
   <details><summary>답</summary>
   READ COMMITTED 에서 한 쿼리는 시작 순간의 스냅샷을 보지만 연속된 두 SELECT 는 사이에 커밋된 변경을 볼 수 있습니다(문서 13.2.1). 잔고를 읽은 뒤 이체가 커밋되고 원장 합을 읽으면 둘 다 맞는 값인데 어긋난 것처럼 보입니다. 잔고와 원장을 한 문장에서 읽으면 한 스냅샷을 봅니다 (해석).
   </details>

## 모를 때 — 정직하게 아는 데까지 말하는 법

- "정확한 내부 구현은 확인해 봐야 하지만, 관찰한 것은 …" — 예: constraint trigger 가 커밋 직전 어떤 자료구조로 큐잉되는지는 소스를 보지 않았습니다. 다만 `INSERT` 는 성공하고 `COMMIT` 에서 에러가 나는 것을 psql 로 봤고, 문서는 지연 트리거가 트랜잭션 끝에 실행된다고 설명합니다.
- "회계에서 그렇게 부른다고 알고 있는데 공식 근거까지는 확인하지 않았습니다" — 복식부기 · 반대 거래 같은 일반 개념은 이렇게 구분해서 말합니다.
- "그 상황은 제가 직접 재현해 보지는 않았고, 문서 기준으로는 …" — 예: Spring `@Transactional` 에서 지연 제약 위반(`commit()` 에서 나는 에러)이 어떤 예외로 올라오는지는 이 레슨에서도 이 트랙의 Spring 문서에서도 확인하지 않았습니다. 확인한 것은 재시도를 `@Transactional` 바깥 빈의 루프에 두어야 한다는 것까지입니다([트랙 05](../../docs/05-spring-jpa-mapping.md)).
- 모르는 숫자는 지어내지 않고 "기본값은 확인해 봐야 한다" 고 말합니다. 아는 값(예: `deadlock_timeout` 기본 1초, PostgreSQL 16 문서)은 버전과 함께 말합니다.

## 실무 장애 시나리오

### 시나리오 1: 대사에서 "잔고 ≠ 원장 합" 이 나왔다

- **증상**: 대사 쿼리가 `BALANCE_NOT_MATCH` 를 몇 건 돌려준다. 또는 전체 잔고 합이 0 이 아니다.
- **확인할 것**: ① 계좌별 잔고 · 원장 합 · 차이를 뽑는다 (아래 쿼리). ② 그 계좌의 최근 원장 줄과 거래 id 를 본다. ③ 수작업 UPDATE 이력 · 최근 배포 · 장애 시각과 겹치는지 본다. ④ 대사가 두 쿼리로 나뉘어 있다면 시점 차이로 인한 거짓 경보인지 한 문장으로 다시 돌려 본다.
  ```sql
  SELECT COALESCE(a.id, l.account_id) AS id, a.balance, l.s AS ledger_sum,
         a.balance - COALESCE(l.s, 0) AS diff
  FROM account a
  FULL OUTER JOIN (SELECT account_id, sum(amount) s FROM ledger GROUP BY account_id) l ON l.account_id = a.id
  WHERE a.id IS NULL OR a.balance <> COALESCE(l.s, 0)
  ORDER BY 1;
  ```
- **원인 후보**: 잔고를 읽고 계산해 덮어쓴 갱신 손실(01.04), 수작업 UPDATE, 장애 중 일부 반영(원장만 · 잔고만), 반올림 정책 불일치, 시점 차이. (해석 — 후보 목록)
- **조치**: 원인을 먼저 본다. 원장은 고치지 않고 반대 거래로 정정한다. 코드 원인이면 고친 뒤 다시 대사한다. 시차가 원인이면 허용 지연을 조정한다.

### 시나리오 2: 이체 API 에서 커밋 시 "다리 합이 0 이 아니다" 에러가 난다 · 또는 데드락이 늘었다

- **증상 A**: `COMMIT` 에서 `P0001` 에러(합 ≠ 0). 앞선 INSERT 문장들은 모두 성공했다.
- **확인할 것**: 에러 메시지의 거래 id · 합. 그 거래를 올린 코드 경로(−금액과 +금액이 같은 값인가 · 반올림이 두 줄에서 다르게 적용되나 · 다리 하나가 빠졌나). 지연 제약이라 에러가 난 문장이 원인 문장이 아니다.
- **조치 A**: 실패한 커밋은 롤백이라 줄이 남지 않는다 — 같은 입력으로 재시도해도 같은 에러다. 코드를 고친다. 원인 문장을 바로 보려면 개발 환경에서 `SET CONSTRAINTS ALL IMMEDIATE` 로 그 자리에서 검사한다.
- **증상 B**: `deadlock detected` (`40P01`) 가 로그에 늘었다.
- **확인할 것**: 반대 방향 이체가 락을 엇갈려 잡는 코드 경로. 기다림이 길면 락 대기를 본다 (문서 28.2).
  ```sql
  SELECT pid, state, wait_event_type, wait_event, left(query, 60) AS query
  FROM pg_stat_activity
  WHERE wait_event_type = 'Lock' OR state = 'idle in transaction';
  ```
  실측으로 락 대기 세션은 `state = active` · `wait_event_type = Lock` · `wait_event = transactionid` 였다. `idle in transaction` 은 락을 쥔 채 일을 안 하는 세션이다.
- **조치 B**: 여러 계좌를 갱신하는 코드는 항상 같은 순서(계좌 id 순)로 잡는다(문서 13.3.4). 엔진이 중단시킨 쪽은 롤백 후 재시도한다 — 거래 id 선점이 있어 두 번 반영되지 않는다 (해석).
