# 01.06 개념 정리 — 원장과 대사 (docs)

> 이 문서들만 읽고 이해하면 "타입 → 원장 구조 → 규칙 검사 시점 → 기록(멱등 · 원자적 갱신 · 락 순서) → 대사" 꼬리질문에 답할 수 있게 쓴 개념 정리다. 근거는 PostgreSQL 16 공식 문서와 이 레슨의 테스트 · psql 실측이다. 근거를 못 찾은 주장은 빼거나 `(해석)` 으로, 회계 · 운영 일반 개념은 `(일반 개념 · 해석)` 으로 표시했다.

> **읽는 법**: 개념 글(마지막 면접 사다리 앞까지)은 블로그처럼 위에서 아래로 읽는 연재다 — 장면 하나 → 개념을 하나씩(그림과 함께) → PostgreSQL 에서는 → 한눈에 정리 → 스스로 확인. 면접 대비는 마지막 사다리 글에서 한다.

> **필수 / 심화**: 필수 글(01 · 03 · 05)만 ② 원리에서 읽는다 — ① 에서 감으로 예측한 뒤, 틀린 문항이 왜 틀렸는지 찾으며. 나머지는 심화(꼬리질문 · 깊은 지식 대비)라 레슨을 마친 뒤 · 면접 전에 읽는다. 필수 글 분량은 공백 줄 · 이미지 줄을 뺀 약 29,940자 ≈ 75분(400자/분 추정)이라 ② 시간을 75분으로 잡았다. 이 레슨은 PostgreSQL 만 다룬다 — MySQL 비교 절은 두지 않았다.

## 읽는 순서

| # | 문서 | 한 줄 | 구분 |
|---|---|---|---|
| 01 | [숫자를 어떻게 저장하나](01-numbers-float-numeric.md) | float8 의 근사 · numeric 의 반올림 · 자릿수 초과 순서 · BigDecimal · sum 의 NULL | **필수** — Q01 · Q02 · Q03 · Q09 되짚기 |
| 02 | [잔고와 원장](02-balance-and-ledger.md) | 원장 append-only · 잔고 = 원장의 합 · 두 다리 · 캐시된 잔고 · 불변식 셋 · 반대 거래 | 심화 — 구조 · 용어의 배경 (꼬리질문 대비) |
| 03 | [규칙은 언제 검사하나](03-when-rules-are-checked.md) | CHECK 즉시 · 지연 constraint trigger · SET CONSTRAINTS · append-only 와 TRUNCATE · ON CONFLICT | **필수** — Q04 ~ Q08 되짚기 |
| 04 | [원장에 기록하기](04-posting-to-the-ledger.md) | 선점(멱등) · 원자적 잔고 갱신 · 잔고 부족 롤백 · 락 순서와 데드락 · 에러 번역 | 심화 — `LedgerService#post` 구현에서 막힐 때 · 꼬리질문 대비 |
| 05 | [대사](05-reconciliation.md) | 내부 · 외부 대사 · FULL OUTER JOIN · COALESCE · 어긋남 종류 · 시차 · 찾은 뒤 | **필수** — Q10 · `Reconciler#findMismatches` 구현 |
| 06 | [면접 사다리](06-interview-ladder.md) | 30초 · 2분 · 갈래별 꼬리질문 · 장애 시나리오 | 심화 — ④ 말하기 연습 · 면접 전 |

권장: ① 에서 감으로 예측해 돌린 뒤, ② 에서는 필수 01 · 03 · 05 만 읽는다 — 01 로 Q01 · Q02 · Q03 · Q09 를, 03 으로 Q04 ~ Q08 을, 05 로 Q10 과 대사 구현을 되짚는다. 구현 `post` 에서 막히면 04 를 펼친다. 나머지는 심화 — 레슨을 마친 뒤 · 면접 전.

## 예측 답 접힘 규칙

- 문항(Qnn) 시나리오의 **결과 값**(숫자 · true/false · 성공/에러 코드)은 `<details>` 안에만 있다. 예측 전에 읽어도 답이 새지 않게 썼다. 글의 예(1.1 + 2.2 · 2.675 · 9999999999.995 · 계좌 {0, 1, 2, 6, 7})는 일부러 문항과 다른 값이다.
- 일반 원리(예: "CHECK 는 지연할 수 없다", "행 트리거는 TRUNCATE 에 불리지 않는다", "FULL OUTER JOIN 은 양쪽 짝 없는 줄을 낸다")는 본문에 있다 — 원리 자체가 ② 의 공부 대상이다. 그래도 문항 값을 먼저 직접 적는다.
- 직접 돌려 본 psql 출력도 문항 장면과 같으면 `<details>` 안이다. 열기 전에 [observe/SCRIPT.md](../observe/SCRIPT.md) 로 관찰부터 해 본다. 문항 장면을 그대로 그린 그림(03 의 COMMIT 실패 · 행 트리거 표)도 접혀 있다.
- 표기: `(실측: Qnn)` = 이 레슨 테스트(정답 상태), `(실측: psql 2026-10-13)` = PostgreSQL 16.14 컨테이너에서 직접, `(해석)` = 근거 문장에서 이은 판단, `(일반 개념 · 해석)` = 회계 · 운영의 일반 개념으로 공식 근거를 붙이지 않은 것.

## 그림

| 그림 | 어디서 | 위치 |
|---|---|---|
| 원장과 대사 (기존) | 전체 | [../diagrams/ledger-reconciliation.svg](../diagrams/ledger-reconciliation.svg) |
| 1.1 + 2.2 · 이진 근사 · 큰 금액 · numeric(12,2) 구조 · 반올림 · 저장 순서 · 앱 경로 (7장) | 01 | [diagrams/blog01-intro.svg](diagrams/blog01-intro.svg) · [binary](diagrams/blog01-binary.svg) · [float-digits](diagrams/blog01-float-digits.svg) · [numeric-layout](diagrams/blog01-numeric-layout.svg) · [rounding](diagrams/blog01-rounding.svg) · [store-flow](diagrams/blog01-store-flow.svg) · [app-path](diagrams/blog01-app-path.svg) |
| 잔고만 · 원장 줄 · 잔고 = 합 · 두 다리 · 캐시 · 불변식 · 반대 거래 · 테이블 네 개 (8장) | 02 | [blog02-intro](diagrams/blog02-intro.svg) · [ledger-rows](diagrams/blog02-ledger-rows.svg) · [balance-sum](diagrams/blog02-balance-sum.svg) · [two-legs](diagrams/blog02-two-legs.svg) · [cache](diagrams/blog02-cache.svg) · [invariants](diagrams/blog02-invariants.svg) · [reversal](diagrams/blog02-reversal.svg) · [schema](diagrams/blog02-schema.svg) |
| 두 줄 사이 합 · 즉시 vs 지연 · 도구 표 · constraint trigger · COMMIT 실패(접힘) · SET CONSTRAINTS · 지연의 대가 · 행 트리거 표(접힘) · ON CONFLICT · 규칙 다섯 (10장) | 03 | [blog03-intro](diagrams/blog03-intro.svg) · [when](diagrams/blog03-when.svg) · [tools](diagrams/blog03-tools.svg) · [constraint-trigger](diagrams/blog03-constraint-trigger.svg) · [fail-timeline](diagrams/blog03-fail-timeline.svg) · [set-constraints](diagrams/blog03-set-constraints.svg) · [deferral-cost](diagrams/blog03-deferral-cost.svg) · [append-only](diagrams/blog03-append-only.svg) · [unique-flow](diagrams/blog03-unique-flow.svg) · [summary](diagrams/blog03-summary.svg) |
| post 흐름 · check-then-act · 선점 · 갱신 손실 · 원자적 갱신 · 잔고 부족 롤백 · 데드락 · 락 순서 · 에러 번역 (9장) | 04 | [blog04-flow](diagrams/blog04-flow.svg) · [check-then-act](diagrams/blog04-check-then-act.svg) · [claim](diagrams/blog04-claim.svg) · [lost-update](diagrams/blog04-lost-update.svg) · [atomic](diagrams/blog04-atomic.svg) · [insufficient](diagrams/blog04-insufficient.svg) · [deadlock](diagrams/blog04-deadlock.svg) · [lock-order](diagrams/blog04-lock-order.svg) · [error-map](diagrams/blog04-error-map.svg) |
| 두 장부 나란히 · JOIN 비교 · 대사 결과 · NULL 함정 · 외부 대사 · − 다리 거르기 · 읽는 시점 · 시차 · 찾은 뒤 (9장) | 05 | [blog05-intro](diagrams/blog05-intro.svg) · [joins](diagrams/blog05-joins.svg) · [result](diagrams/blog05-result.svg) · [null-trap](diagrams/blog05-null-trap.svg) · [external](diagrams/blog05-external.svg) · [legs-filter](diagrams/blog05-legs-filter.svg) · [snapshot](diagrams/blog05-snapshot.svg) · [timing](diagrams/blog05-timing.svg) · [after-find](diagrams/blog05-after-find.svg) |

다시 그리기(만든 사람용 · 레슨 폴더에서): `python3 -I docs/diagrams/draw_blog01.py` … `draw_blog05.py`

## 이 레슨과 연결

- 손 작업: [예측](../src/test/java/deepdive/c01/l06/LedgerPredictTest.java) · [구현](../src/main/java/deepdive/c01/l06/LedgerService.java) · [관찰](../observe/SCRIPT.md) · [내 말로](../NOTES.md)
- 앞선 레슨: [01.01 격리수준](../../l01-isolation-mvcc/docs/README.md) (스냅샷 · 40001) · [01.02 행 락 · 데드락](../../l02-row-locks-deadlock/docs/README.md) · [01.03 멱등](../../l03-idempotency/docs/README.md) (ON CONFLICT · check-then-act) · [01.04 재고 동시 차감](../../l04-stock-concurrency/docs/README.md) (원자적 갱신)
