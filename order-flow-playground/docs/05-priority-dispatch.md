# 05 — 우선순위: 정렬 기준은 비즈니스 규칙이다

> "정렬 한 줄" 로 보이지만, 정렬 기준을 바꾸면 SLA 위반 건수가 바뀐다.

**대상 코드**: `stage5/TaskDispatcher.java`
**완료 기준**: `./gradlew s5` 초록 + 완전 동률에서도 순서가 결정론적

---

## 1. 문제

창고에 처리해야 할 작업이 1,000건 쌓여 있다. 작업자는 20명. **무엇부터 시키나?**

- 먼저 들어온 것부터? → 마감 임박한 주문이 뒤에서 굶는다
- 급한 것부터? → 급하지 않은 주문이 영원히 밀린다(starvation)
- 마감 순? → 대개 이게 기본. 하지만 등급·거리·묶음 처리도 고려해야 한다

**정렬 기준을 정하는 것 = 어떤 주문을 희생할지 정하는 것**이다. 기술 결정이 아니라 비즈니스 결정이고, 그래서 코드에 명시적으로 드러나야 한다.

---

## 2. 다단 정렬 조립

```java
Comparator.comparing(PickingTask::dueAt)          // 1. 마감 이른 순
    .thenComparingInt(PickingTask::priority)      // 2. 급한 등급 먼저
    .thenComparing(PickingTask::createdAt)        // 3. FIFO
    .thenComparing(PickingTask::taskId);          // 4. 결정론 보장
```

### 마지막 tie-breaker 를 반드시 넣는다

모든 기준이 같은 작업이 여러 개면, 순서가 **실행마다 달라진다.** 그러면:

- 테스트가 간헐적으로 깨진다 (flaky) — 그리고 "가끔 실패하니까 재실행" 이 습관이 되면 진짜 버그도 놓친다
- 같은 입력에 같은 출력이 안 나와 재현이 불가능해진다

`taskId` 같은 유일 값으로 마무리하면 **전순서(total order)** 가 된다.

> ⚠️ **함정**: 손으로 `int` 를 리턴하는 비교 함수를 짜면 두 가지가 터진다.
> ```java
> return (int)(a.dueAt().toEpochMilli() - b.dueAt().toEpochMilli());  // ❌ 오버플로
> ```
> long 차이를 int 로 캐스팅하면 값이 뒤집힌다. 그리고 비대칭(`compare(a,b)` 와 `compare(b,a)` 의 부호가 안 맞음)이 생기면 `TimSort` 가 `IllegalArgumentException: Comparison method violates its general contract` 를 던진다 — **데이터가 많아졌을 때만** 터지는 종류의 버그다.
>
> `Comparator.comparing` 체인을 쓰면 이 둘 다 안 생긴다.

---

## 3. PriorityQueue 의 함정

**힙은 부분 순서만 유지한다.** 루트가 최소값인 것만 보장하고, 나머지 배열은 정렬돼 있지 않다.

```java
PriorityQueue<PickingTask> q = new PriorityQueue<>(byUrgency());
// ...
new ArrayList<>(q);        // ❌ 정렬 순서 아님 — 힙 내부 배열 순서
q.stream().toList();       // ❌ 같음
q.toString();              // ❌ 같음
for (var t : q) { ... }    // ❌ 같음

while (!q.isEmpty()) q.poll();  // ✅ 이것만 정렬 순서
```

원소가 3~4개일 때는 우연히 맞아떨어져서 **테스트가 통과한다.** 6~7개부터 어긋나기 시작한다.
`peekTop()` 테스트를 일부러 틀리게 짜서 이 장면을 한 번 보고 가라.

> 📖 근거: [`PriorityQueue` javadoc](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/PriorityQueue.html) — *"The Iterator provided in method iterator() and the Spliterator are not guaranteed to traverse the elements of the priority queue in any particular order."*

### 자료구조 선택

| 요구 | 자료구조 | 복잡도 |
|---|---|---|
| 최우선 1건만 반복해서 꺼냄 | `PriorityQueue` (힙) | 삽입/삭제 O(log n) |
| 상위 N건을 정렬해서 보여줌 | `TreeSet` / 정렬된 복사본 | 순회 O(n) |
| 매번 전체 정렬 | `List.sort` | **O(n log n) × 호출 횟수** ← 함정 |

`submit` 마다 전체 정렬하면 n건 처리에 O(n² log n). 힙은 O(n log n). **이 비교를 말할 수 있는 게 이 스테이지의 알고리즘 파트다.**

---

## 4. 확장 질문

### Q1. 낮은 우선순위 작업이 영원히 안 나오면(starvation)?

<details><summary>답</summary>

마감 순으로만 뽑으면, 마감이 먼 작업은 계속 뒤로 밀린다. 급한 게 계속 유입되면 영원히.

**해법: 대기 시간에 따른 우선순위 승급(aging).**
```
유효 우선순위 = 기본 우선순위 - (대기 시간 / 승급 간격)
```
30분 대기할 때마다 한 단계씩 올린다. 언젠가는 반드시 처리된다.

구현 주의: 유효 우선순위가 시간에 따라 변하면 **힙의 정렬 키가 변한다.** 힙은 삽입 후 키가 바뀌는 걸 감당하지 못한다(원소가 잘못된 위치에 갇힌다).
- 주기적으로 큐를 재구성하거나
- 정렬 키에 시간을 직접 넣지 말고, **꺼낼 때 후보 몇 개를 보고 판단**하는 방식으로 우회
</details>

### Q2. 작업자 20명이 동시에 poll 하면?

<details><summary>답</summary>

`PriorityQueue` 는 **thread-safe 하지 않다.** 동시에 `poll` 하면 같은 작업이 두 명에게 나가거나 힙이 깨진다.

| 선택 | 특징 |
|---|---|
| `PriorityBlockingQueue` | 단일 JVM 에서 간단하게 해결 |
| DB 큐 + `SELECT ... FOR UPDATE SKIP LOCKED` | 다중 인스턴스에서 표준적인 방법. 락 걸린 행을 건너뛰고 다음 걸 집는다 |
| 전용 브로커 | 규모가 커지면 |

**`SKIP LOCKED` 가 핵심 키워드**다. 이게 없으면 워커들이 같은 행을 두고 줄을 서서 병렬성이 사라진다.

> 📖 [PostgreSQL — SELECT FOR UPDATE SKIP LOCKED](https://www.postgresql.org/docs/current/sql-select.html#SQL-FOR-UPDATE-SHARE)
</details>

### Q3. 작업을 가져간 작업자가 응답이 없으면?

<details><summary>답</summary>

큐에서 꺼내는 순간 사라지면, 처리하던 워커가 죽었을 때 **그 작업은 영영 없어진다.**

**해법: 소유권 + 임대(lease).**
```
task: id, status(WAITING/PROCESSING/DONE), owner, leased_until
```
- 가져갈 때 `PROCESSING` + `leased_until = now + 10min`
- 완료 시 `DONE`
- 배치가 `PROCESSING AND leased_until < now` 를 찾아 `WAITING` 으로 되돌린다
- 장시간 작업은 주기적으로 lease 를 연장(heartbeat)

부작용: 되돌린 작업이 실제로는 처리되고 있었다면 **중복 처리**가 된다. 그래서 작업 처리 자체가 멱등해야 한다 — **stage2 가 여기서 다시 나온다.**
</details>

### Q4. "묶음 처리가 효율적" 같은 규칙은 어떻게 넣나?

<details><summary>답</summary>

같은 상품이 포함된 주문끼리 묶으면 이동 거리가 준다. 하지만 이건 **정렬로 표현되지 않는다** — 개별 작업의 순위가 아니라 조합의 문제(집합 최적화)라서 그렇다.

접근:
- 1단계로 정렬해서 후보 K개를 뽑고, 2단계로 그 안에서 묶는다 (탐욕적 배치)
- 마감이 임박한 건은 묶음에서 빼서 즉시 처리 (제약 조건)

여기서 중요한 태도: **최적해를 찾으려 들지 않는다.** 이런 문제는 대개 NP-hard 고, 실무에서 필요한 건 "휴리스틱 + 측정" 이다. 개선 전후로 무엇을 측정할지(평균 이동 거리, 시간당 처리 건수, SLA 위반율)를 먼저 정하는 게 알고리즘보다 앞선다.

> 💡 "최적화를 어떻게 하겠냐" 는 질문에 알고리즘 이름부터 꺼내는 것보다, **측정 지표를 먼저 말하는 쪽**이 신뢰를 얻는다.
</details>

### Q5. 큐 길이가 계속 늘어나면?

<details><summary>답</summary>

`size()` 가 단조 증가 = **처리량 < 유입량.** 큐 길이(backlog)는 가장 값싸고 정직한 부하 지표다.

봐야 할 것:
- **backlog 추세** — 절대값이 아니라 기울기
- **가장 오래된 작업의 대기 시간** (age of oldest) — 평균 대기 시간보다 이쪽이 SLA 와 직결된다
- **마감 초과 건수** — 이미 실패한 것

> ✗→✓ **오해**: "평균 처리 시간이 정상이니 문제없다" → **정정**: 평균은 굶고 있는 소수를 가린다. **tail(p99, max)과 최고령 작업**을 본다.
</details>

---

## 5. 자가 점검

- [ ] `Comparator.comparing` 체인으로 조립했다 (손으로 int 리턴 안 함)
- [ ] 마지막 tie-breaker 로 결정론을 보장한다
- [ ] `PriorityQueue` 순회 순서 함정을 **직접 봤다**
- [ ] 힙 O(n log n) vs 매번 정렬 O(n² log n) 을 말할 수 있다
- [ ] starvation 과 aging 을 설명할 수 있다
- [ ] `SKIP LOCKED` 를 안다
- [ ] lease/heartbeat 로 유실을 막는 구조를 안다
- [ ] backlog·최고령 대기 시간을 지표로 말할 수 있다

---

**이전** ← [04 — 이벤트 순서와 중복](04-event-ordering.md) · **다음** → [10 — 60분 드릴 운영법](10-timeboxed-drill.md)
