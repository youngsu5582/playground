# 01.01 개념 정리 — 격리수준 · MVCC (docs)

> 이 문서들만 읽고 이해하면 "원리 → 엔진 내부 → 운영 · 장애 → 설계 선택" 꼬리질문에 답할 수 있게 쓴 개념 정리다. 근거는 PostgreSQL 16 공식 문서 · 소스 README · MySQL 8.0 · Spring 공식 문서와 이 레슨의 테스트 · psql 실측이다. 근거를 못 찾은 주장은 빼거나 `(해석)` 으로 표시했다.

> **읽는 법**: 개념 글(마지막 면접 사다리 앞까지)은 블로그처럼 위에서 아래로 읽는 연재다 — 장면 하나 → 개념을 하나씩(그림과 함께) → PostgreSQL 에서는 → 한눈에 정리 → 스스로 확인. 면접 대비는 마지막 사다리 글에서 한다.

> **필수 / 심화**: 필수 글(03 · 05)만 ② 원리에서 읽는다 — ① 에서 감으로 예측한 뒤, 틀린 문항이 왜 틀렸는지 찾으며. 나머지는 심화(꼬리질문 · 깊은 지식 대비)라 레슨을 마친 뒤 · 면접 전에 읽는다. 필수 글 분량은 공백 줄 · 이미지 줄을 뺀 약 28,260자 ≈ 71분(400자/분 추정)이라 ② 시간을 75분으로 잡았다. MySQL 비교 절은 필수 글 안에서도 "(심화)" 다 — 회사 서비스가 PostgreSQL 이라 MySQL 은 비교 참고다.

## 읽는 순서

| # | 문서 | 한 줄 | 구분 |
|---|---|---|---|
| 01 | [트랜잭션 이상 현상과 격리수준](01-anomalies-and-isolation-levels.md) | 이상 현상 정의 · 표 13.1 · PostgreSQL 이 실제로 막는 것 · MySQL 비교 | 심화 — 이상 현상 정의 · 표 13.1 (Q01 ~ Q04 배경, 틀렸을 때 보충) |
| 02 | [MVCC 저장 구조](02-mvcc-tuple-storage.md) | 튜플 헤더(xmin/xmax/ctid) · UPDATE = 새 버전 · 커밋 상태 · HOT | 심화 — Q10 · 장면 2 의 배경 (xmin · xmax) |
| 03 | [스냅샷과 가시성](03-snapshot-visibility.md) | `xmin:xmax:xip` · 문장마다 vs 첫 문장 · 읽기는 쓰기를 막지 않는다 | **필수** — Q01 ~ Q04 · Q10 되짚기 |
| 04 | [같은 행을 쓰는 경쟁](04-write-conflicts.md) | 행 락 · READ COMMITTED 재확인 · REPEATABLE READ 의 40001 · 갱신 손실 | 심화 — Q05 ~ Q07 에서 막힐 때 (행 락 · 40001 · 갱신 손실) |
| 05 | [SERIALIZABLE 과 SSI · 재시도 설계](05-serializable-ssi-retry.md) | write skew · SIREAD · 위험한 구조 · `Tx.serializable` · Spring | **필수** — Q08 · Q09 · 구현 (`Tx.serializable`) |
| 06 | [운영 — VACUUM · horizon · wraparound](06-operations-vacuum-horizon.md) | 죽은 튜플 · idle in transaction · freeze · 감시 쿼리 | 심화 — 운영 · 장애 대응 (꼬리질문 대비) |
| 07 | [면접 사다리](07-interview-ladder.md) | 30초 · 2분 · 갈래별 꼬리질문 · 장애 시나리오 | 심화 — ④ 말하기 연습 · 면접 전 |

권장: ① 에서 감으로 예측해 돌린 뒤, ② 에서는 필수 03 · 05 만 읽는다 — 03 으로 Q01 ~ Q04 · Q10 을, 05 로 Q08 · Q09 와 구현을 되짚는다. Q05 ~ Q07 에서 막히면 04 를 펼친다. 나머지는 심화 — 레슨을 마친 뒤 · 면접 전.

## 예측 답 접힘 규칙

- 문항(Qnn) 시나리오의 **결과 값**(숫자 · true/false · 성공/에러 코드)은 `<details>` 안에만 있다. 예측 전에 읽어도 답이 새지 않게 썼다.
- 일반 원리(예: "READ COMMITTED 는 문장마다 스냅샷", "SERIALIZABLE 은 실패시킨다")는 본문에 있다 — 원리 자체가 ② 의 공부 대상이다. 그래도 문항 값을 먼저 직접 적는다.
- 직접 돌려 본 psql 출력도 문항 장면과 같으면 `<details>` 안이다. 열기 전에 [observe/SCRIPT.md](../observe/SCRIPT.md) 로 관찰부터 해 본다.
- 표기: `(실측: Qnn)` = 이 레슨 테스트(정답 상태), `(실측: psql 2026-10-13)` = PostgreSQL 16.14 컨테이너에서 직접, `(해석)` = 근거 문장에서 이은 판단.

## 그림

| 그림 | 어디서 | 위치 |
|---|---|---|
| 격리수준 · MVCC (기존) | 01 | [../diagrams/mvcc-isolation.svg](../diagrams/mvcc-isolation.svg) |
| 행 버전(튜플)과 스냅샷 판정 | 02 · 03 | [diagrams/tuple-visibility.svg](diagrams/tuple-visibility.svg) |
| write skew 와 rw-의존성 고리 | 05 | [diagrams/ssi-rw-cycle.svg](diagrams/ssi-rw-cycle.svg) |

다시 그리기(만든 사람용 · 레슨 폴더에서): `python3 -I docs/diagrams/draw.py`

## 이 레슨과 연결

- 손 작업: [예측](../src/test/java/deepdive/c01/l01/IsolationPredictTest.java) · [구현](../src/main/java/deepdive/c01/l01/Tx.java) · [관찰](../observe/SCRIPT.md) · [내 말로](../NOTES.md)
- 이어지는 레슨: 01.02 행 락 · 데드락 · 01.04 재고 · 잔고 동시 차감 · 02.03 outbox
