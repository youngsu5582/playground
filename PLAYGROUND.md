# Playground 규약

**직접 해보고 확인하며 지식을 얻는 실험장**의 공통 구조와 컨벤션.
대상은 AWS/terraform 인프라에 한정되지 않는다 — 로컬 도커로 재현하는 DB·동시성·실패경로 실험도 포함한다.
기준은 "**내가 직접 돌려보고 관찰해서 깨달을 수 있는가**" 하나다.
새 playground를 시작할 때 이 문서를 따른다. (원칙: **가볍게 + 하나씩** — 무거운 프레임워크 금지)

> 학습 철학: 하나씩만 / output 중심 / 완료기준 / 피드백 짧게.
> 레퍼런스 구현: [`order-flow-playground/`](order-flow-playground/).

---

## 0. 시작 규칙
- **완료 기준을 1문장**으로 먼저 정의 (README 상단).
- **새 기술은 1개만** (토끼굴 금지).
- **AI 분담**: 셋업(terraform/scaffold/스크립트)은 AI, **테스트 실행·관찰은 내가** 하나씩.
- 목표 달성하면 **멈춘다** — 측정 정밀화·부가 도구는 별도 과제로 분리.

## 1. 공통 디렉토리 구조
```
<name>-playground/
├── README.md          목적 / 완료기준(1줄) / 사전준비 / 실행 / 비용 / 정리(destroy)
├── TESTING.md         T-ID 테스트 매트릭스 + 결과 보는 곳 + 결과 기록 템플릿
├── terraform/         (infra test 시) 인프라 (main/variables/outputs/providers/versions + tfvars.example)
├── docker-compose.yml (local test 시) 미들웨어 1개 + 관찰용 설정
├── sql/               (DB test 시) 스키마·시드 (초기화 자동 적용 순서 = 파일명 순)
├── app/               (code test 시) 최소 앱 + gradle wrapper 등
├── scripts/           NN-*.sh (번호 = 실행 순서)
├── docs/              README(학습지도) + 원자적 학습 노트
└── .gitignore         tfvars / build 산출물
```

## 2. 타입별 애드온 (공통 코어 + 필요한 것만)
| 타입 | 추가 | 검증 |
|---|---|---|
| **infra test** | terraform 중심 | `describe-*`로 상태(ACTIVE 등) + CloudWatch 지표 |
| **local test** | docker-compose 중심 (terraform 없음) + `sql/` | 세션 2개 + 서버 로그 + 시스템 뷰(`pg_stat_activity` 등) |
| **code test** | `app/` + SDK 라우팅 | 요청 로그(엔드포인트/리전) + 응답 |
| **perf/부하 test** | 부하 하네스(warm client) | CloudWatch **권위 지표** + (필요시) 분산 poller |

## 3. 스크립트 컨벤션 (`scripts/NN-*.sh`)
- `#!/usr/bin/env bash` + `set -euo pipefail`
- **번호 접두어** = 실행 순서 (`01-`, `02-`…), 문서의 T-ID와 정렬
- **헤더 주석**: 목적 / `사용:` 예시 / 환경변수 / **[앱 필요]** 여부
- 파라미터는 **환경변수 + 기본값** (`"${VAR:-default}"`)
- macOS 기본 bash(3.2) 호환: 연관배열 금지, ms/ISO 시각은 `python3`로
- 실행권한 부여(`chmod +x`), `bash -n` 문법 체크

## 4. 문서/노트 컨벤션 (`docs/`)
- `README.md` = **학습 지도**: 3줄 요약 + 권장 읽는 순서 + 노트별 한 줄 훅
- **원자적 노트**: 개념 1개 = MD 1개. 구조는 **지식 타입마다 유연**(고정 템플릿 X)
- **callout 세트**: `📊 측정`(측정일·재현 스크립트 표기) / `⚠️ 함정` / `✗→✓ 오해` / `💡 실무` / `📖 근거`
- **하드 클레임(API/제약/수치)엔 공식문서 링크 의무** — 기억이 아니라 문서로 검증
- 다이어그램은 **Mermaid**(PNG 대신, GitHub 렌더), 링크는 GitHub 상대링크 `[x](x.md)`
- 실측값은 **직접 잰 것만** 📊로 표기 (이론/추론과 구분)

## 5. 측정 규율 (배운 교훈)
- **sub-second 측정엔 warm SDK client** — `aws` CLI는 프로세스 startup ~1s로 값 오염(실증).
- **CloudWatch = 권위 지표** (서버측). 클라 측정과 **교차검증**.
- 도구 3-way 대조(앱 warm client / CLI / CloudWatch)로 오염 여부 판별.
- 지연·지표는 **tail(p99/max)** 을 본다. 평균은 함정. **lag는 SLA 아님**.

## 6. 비용·정리 규율 (필수)
- README에 **비용 메모** + **정리(destroy)** 절차 명시.
- on-demand면 유휴 ≈ 0이지만, **끝나면 반드시 `terraform destroy`**.
- **local test 는 비용 0** — 대신 `docker compose down -v` 로 정리하고, 볼륨을 지워도 시드가 재생성되는지 확인해둔다.
- 비용 추정은 **실측(ConsumedCapacity 등) × 단가**, 정밀 달러는 리전 실단가로 보정.

## 7. 표준 흐름
```
infra up → verify(상태 ACTIVE 등) → test(하나씩, 내가 실행) → measure(warm client + CloudWatch)
  → document(docs/ 노트) → teardown(destroy)
```

---
승격 규칙: 이 규약을 2~3개 playground에서 실제로 재사용하고 마찰이 확인되면 → **템플릿 디렉토리**, 그다음에도 자주면 → **스킬(`playground:init`)** 로 점진적 자동화. 지금은 문서만.
