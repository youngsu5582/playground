#!/usr/bin/env python3
"""01.01 블로그판 05 그림. 실행: python3 -I docs/diagrams/draw_blog05.py (레슨 폴더에서)"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[4] / "tools"))
from diagram import Diagram, P, finish, timeline as _timeline  # noqa: E402

OUT = pathlib.Path(__file__).parent


def timeline(*a, **k):
    return _timeline(*a, out=OUT, **k)


def intro():
    timeline("blog05-intro", "도입: 당직 규칙 \"2명 이상\" 이 깨지는 장면",
             "당직 3명(alice · bob · carol). 규칙은 \"당직은 2명 이상\". A 는 bob 을, B 는 alice 를 당직에서 뺀다",
             [("A", "1  SELECT count(*) WHERE on_call", "본 값: 3  → 한 명 빼도 2명이다", None),
              ("B", "2  SELECT count(*) WHERE on_call", "본 값: 3  → 한 명 빼도 2명이다", None),
              ("A", "3  UPDATE bob → off  ·  COMMIT", "성공 (다른 행 — 기다릴 일이 없다)", None),
              ("B", "4  UPDATE alice → off  ·  COMMIT", "성공 — 남은 당직 1명, 규칙이 깨졌다", "bad")],
             [(0, 3, "A 가 읽은 근거를\nB 가 바꾼다", 0.83), (1, 2, "B 가 읽은 근거를\nA 가 바꾼다", 0.5)],
             "둘 다 자기 스냅샷에서 3명을 봤고, 고친 행이 서로 달라서 행 락도 \"스냅샷 이후 바뀐 행\" 에러(04)도 없다.\n"
             "어느 순서로 직렬로 돌려도 이 결과는 안 나온다 — 01 에서 이름 붙인 쓰기 왜곡(write skew)이 실제 업무 규칙을 깬 모양이다.",
             "각자는 옳은데 합치면 규칙이 깨진다", level="REPEATABLE READ")


def three_ways():
    d = Diagram("blog05-three-ways", 1400, 560, "write skew 를 막는 방법 세 가지",
                "방법마다 막는 원리와 치르는 값이 다르다", out=OUT)
    cs = [("SERIALIZABLE", "원리: 엔진이 읽기-쓰기 의존성을 추적해\n위험하면 실패시킨다", "단점: 앱에 재시도 필요 · 오탐 · 오버헤드", P["bff_bg"], P["back"]),
          ("판단 근거를 SELECT ... FOR UPDATE", "원리: 읽은 행을 잠가 상대가 기다리게 한다", "단점: 존재하는 행만 잠근다 — 조건에\n새로 들어올 행(팬텀)은 못 막는다", P["as_bg"], P["front"]),
          ("충돌 구체화 (materialize)", "원리: \"당직 인원\" 행을 하나 두고 모두가 그 행을\nUPDATE -> 같은 행이라 행 락이 줄 세운다", "단점: 설계 변경 · 한 행이 병목", P["ok_bg"], P["green"])]
    for i, (t, a, b, bg, st) in enumerate(cs):
        d.card(f"c{i}", 40 + i * 450, 110, 420, 250, t, a + "\n\n" + b, bg=bg, stroke=st, title_size=16, body_size=14)
    d.card("n", 40, 400, 1320, 120, "FOR UPDATE 의 한계는 \"잠기는 행은 쿼리가 반환하는 행 그대로\" 라서 나온다 (SELECT 문서의 락 절, 논리적 귀결 — 해석)",
           "이 방법들은 이 레슨의 NOTES 꼬리질문 2번이 다루는 것과 같다. 아래 실측으로 FOR UPDATE 의 동작은 확인했다",
           bg=P["note_bg"], stroke=P["line"], title_size=15, body_size=14)
    d.save()


def forupdate():
    d = Diagram("blog05-forupdate", 1400, 520, "판단 근거에 FOR UPDATE 를 걸면 — 수준마다 다르다",
                "두 세션이 SELECT doctor FROM on_call WHERE on_call FOR UPDATE 후 같은 판단을 한다 (실측: psql 2026-10-13)", out=OUT)
    d.card("rc", 40, 110, 640, 220, "READ COMMITTED",
           "늦은 세션은 FOR UPDATE 자리에서 기다린다\n상대가 커밋하면 이어서 진행한다\n"
           "count(*) 가 1 로 보였다\n-> 앱이 \"빠지면 안 된다\" 로 거절할 수 있다",
           bg=P["ok_bg"], stroke=P["green"], title_size=17, body_size=15)
    d.card("rr", 720, 110, 640, 220, "REPEATABLE READ",
           "늦은 세션은 FOR UPDATE 자리에서\nERROR: could not serialize access due to concurrent update\n\n"
           "문서 13.3.2: RR · SERIALIZABLE 에서는 잠그려는 행이\n트랜잭션 시작 이후 바뀌었으면 에러",
           bg=P["bad_bg"], stroke=P["red"], title_size=17, body_size=14)
    d.card("n", 40, 370, 1320, 100, "결과의 차이는 04 에서 본 \"기다린 뒤의 행동\" 과 같은 규칙이다",
           "RC 는 최신 버전을 받아들여 계속하고, RR 은 스냅샷 이후 바뀐 행을 거부한다. 이 방법의 한계(팬텀)는 잠길 행이 아직 없는 경우다",
           bg=P["note_bg"], stroke=P["line"], title_size=15, body_size=14)
    d.save()


def siread():
    d = Diagram("blog05-siread", 1400, 640, "SIREAD 락(predicate lock) — 락이라기보다 깃발",
                "읽은 범위를 기록해 두었다가, 나중에 \"이 읽기 결과에 영향을 줬을 쓰기\" 를 알아낸다", out=OUT)
    d.card("a", 40, 110, 640, 150, "블로킹하지 않는다",
           "다른 트랜잭션을 기다리게 하지 않는다\n-> 데드락에 참여하지 않는다\npg_locks 에 mode = SIReadLock 으로 보인다",
           bg=P["ok_bg"], stroke=P["green"], title_size=16, body_size=14)
    d.card("b", 720, 110, 640, 150, "커밋 뒤에도 남을 수 있다",
           "겹친 읽기-쓰기 트랜잭션이 끝날 때까지\n남을 수 있다 (문서 13.2.3)",
           bg=P["note_bg"], stroke=P["muted"], title_size=16, body_size=14)
    d.text(40, 295, "granularity — 메모리를 아끼려고 합쳐질 수 있다", 17, P["ink"], weight=700)
    d.pill("t", 40, 340, 360, 80, "튜플 락\n(읽은 행 하나)", P["as_bg"], P["front"], size=15)
    d.pill("p", 520, 340, 360, 80, "페이지 락\n(그 행이 있는 페이지)", P["todo_bg"], P["orange"], size=15)
    d.pill("r", 1000, 340, 360, 80, "릴레이션 락\n(테이블 · 인덱스 전체)", P["bad_bg"], P["red"], size=15)
    d.arrow([d.anchor("t", "e"), d.anchor("p", "w")], P["muted"], "합쳐질 수 있다", start="t", end="p")
    d.arrow([d.anchor("p", "e"), d.anchor("r", "w")], P["muted"], "합쳐질 수 있다", start="p", end="r")
    d.card("seq", 40, 470, 1320, 90, "시퀀셜 스캔은 항상 릴레이션 수준 predicate 락을 필요로 한다 (문서 13.2.3 의 성능 팁)",
           "그래서 읽은 행이 겹치지 않아도 충돌로 보일 수 있다 — 아래 오탐 절", bg=P["bad_bg"], stroke=P["red"], title_size=15, body_size=14)
    d.save()


def dangerous():
    d = Diagram("blog05-dangerous", 1400, 600, "위험한 구조 (dangerous structure)",
                "스냅샷 격리의 모든 이상은 가운데(pivot) 트랜잭션에 두 개의 인접한 rw-화살표가 있는 고리를 포함한다 (README-SSI)", out=OUT)
    d.pill("tin", 40, 130, 260, 80, "Tin", P["as_bg"], P["front"], size=20)
    d.pill("tp", 570, 130, 260, 80, "Tpivot", P["todo_bg"], P["orange"], size=20)
    d.pill("tout", 1100, 130, 260, 80, "Tout", P["ok_bg"], P["green"], size=20)
    d.arrow([d.anchor("tin", "e"), d.anchor("tp", "w")], P["red"], "rw: Tin 이 읽으려던 것을\nTpivot 이 썼다", start="tin", end="tp")
    d.arrow([d.anchor("tp", "e"), d.anchor("tout", "w")], P["red"], "rw: Tpivot 이 읽으려던 것을\nTout 이 썼다", start="tp", end="tout")
    d.card("when", 40, 260, 640, 130, "취소하는 때 — Tout 이 가장 먼저 커밋할 때만",
           "Tin -rw-> Tpivot -rw-> Tout 이고 Tout 이 Tpivot · Tin 보다 먼저 커밋\n(\"We only roll back a transaction if Tout commits before Tpivot and Tin\")",
           bg=P["bad_bg"], stroke=P["red"], title_size=15, body_size=14)
    d.card("rw", 720, 260, 640, 130, "rw-의존성(rw-conflict)이란",
           "한 트랜잭션이 읽으려는 데이터를 동시 트랜잭션이 썼거나 쓸 예정이라\n볼 수 없을 때 생긴다. 읽은 쪽 -> 쓴 쪽 방향의 화살표\n\"읽은 쪽은 쓴 쪽보다 먼저 일어난 것처럼 보여야 한다\"",
           bg=P["note_bg"], stroke=P["line"], title_size=15, body_size=14)
    d.card("one", 40, 420, 420, 140, "한 방향만 있다면", "T1 -> T2 는 직렬 순서 \"T1 먼저\" 로\n설명된다 — 문제가 없다",
           bg=P["ok_bg"], stroke=P["green"], title_size=15, body_size=14)
    d.card("victim", 490, 420, 420, 140, "희생자 선택", "즉시 재시도해도 정확히 같은 트랜잭션들과\n다시 충돌하지 않도록 고르려 한다\n-> 그래서 재시도가 의미를 갖는다",
           bg=P["as_bg"], stroke=P["front"], title_size=15, body_size=14)
    d.card("fp", 940, 420, 420, 140, "오탐(false positive)", "모양만 맞아도 취소될 수 있다\n실제로는 직렬화 이상이 아닌데도\n(\"low in practice\" 라고도 쓴다)",
           bg=P["todo_bg"], stroke=P["orange"], title_size=15, body_size=14)
    d.save()


def error_timing():
    d = Diagram("blog05-error-timing", 1400, 560, "SERIALIZABLE 의 40001 은 두 자리에서 난다",
                "같은 당직 시나리오를 SERIALIZABLE 로 두 번 돌렸다 (실측: psql 2026-10-13)", out=OUT)
    d.card("c", 40, 110, 640, 220, "1  커밋 시점",
           "A 먼저 UPDATE -> B UPDATE -> A 커밋 -> B 커밋 시도\n\nERROR: could not serialize access due to\nread/write dependencies among transactions\n"
           "Reason code: Canceled on identification as a\npivot, during commit attempt.",
           bg=P["bad_bg"], stroke=P["red"], title_size=17, body_size=14)
    d.card("w", 720, 110, 640, 220, "2  UPDATE 자리 (쓰는 중)",
           "타이밍을 바꿔 B 가 먼저 커밋하고 A 가 나중에 UPDATE\n\n실패가 UPDATE 에서 났다\n"
           "Reason code: Canceled on identification as a\npivot, during write.",
           bg=P["todo_bg"], stroke=P["orange"], title_size=17, body_size=14)
    d.card("n", 40, 360, 1320, 150, "그래서 호출 코드는 commit() 까지 같은 try 안에 둬야 한다",
           "1 번 출력의 HINT: The transaction might succeed if retried.\n"
           "즉 40001 은 UPDATE 에서도, COMMIT 에서도 날 수 있다\n"
           "(WriteSkewImplementTest 의 \"commit 시점 40001\" 테스트)",
           bg=P["note_bg"], stroke=P["line"], title_size=16, body_size=14)
    d.save()


def false_positive():
    d = Diagram("blog05-false-positive", 1400, 640, "오탐 — 행이 겹치지 않는데도 실패하는 경우",
                "fp(id PK, v) 1000행. 두 SERIALIZABLE 트랜잭션이 자기 행만 읽고(count(*) WHERE id = X) 같은 X 의 v 를 UPDATE 한다 (실측: psql 2026-10-13)", out=OUT)
    cs = [("X = 1 / 2   인덱스 스캔", "ctid: id 1 · 2 = (0,1) · (0,2) 같은 페이지\n인덱스 leaf 도 같은 page 1\n"
           "SIReadLock: 힙 fp page 0 · 인덱스 fp_pkey page 1\n각 2개 (A · B 가 같은 페이지를 잡음)", "A 가 40001 (commit attempt)", P["bad_bg"], P["red"]),
          ("X = 1 / 999   인덱스 스캔", "ctid: id 999 = (4,95), 인덱스 leaf page 4\n힙 page 0 · 4, 인덱스 page 1 · 4 로 갈라져\n각 1개씩",
           "둘 다 커밋", P["ok_bg"], P["green"]),
          ("X = 1 / 999   시퀀셜 스캔", "인덱스 · 비트맵 스캔을 끈 시퀀셜 스캔\nSIReadLock 은 relation 락",
           "A 가 40001 (commit attempt)", P["bad_bg"], P["red"])]
    for i, (t, b, r, bg, st) in enumerate(cs):
        d.card(f"c{i}", 40 + i * 450, 110, 420, 230, t, b + "\n\n결과: " + r, bg=bg, stroke=st, title_size=15, body_size=13)
    d.card("why", 40, 370, 1320, 100, "해석: SIREAD 락이 페이지 · 릴레이션 단위로 커졌기 때문으로 보인다",
           "시퀀셜 스캔은 릴레이션 락이라는 문서 13.2.3 의 설명과 맞고, 1 과 2 가 같은 페이지라 실패한 것도 페이지 락으로 확인된다\n"
           "왜 튜플 락이 아니라 페이지 락으로 보였는지의 세부는 확인하지 않았다",
           bg=P["note_bg"], stroke=P["line"], title_size=15, body_size=14)
    d.card("fix", 40, 500, 1320, 100, "문서가 권하는 완화 (문서 13.2.3)",
           "인덱스 스캔이 되게 (random_page_cost 낮추기 · cpu_tuple_cost 올리기)\n"
           "락 메모리 파라미터 증가: max_pred_locks_per_transaction · max_pred_locks_per_relation · max_pred_locks_per_page",
           bg=P["todo_bg"], stroke=P["orange"], title_size=15, body_size=14)
    d.save()


def deferrable():
    d = Diagram("blog05-deferrable", 1400, 430, "SERIALIZABLE READ ONLY DEFERRABLE",
                "긴 리포트 · 백업에 적합하다 — 대가는 시작 지연이다", out=OUT)
    d.pill("p1", 40, 130, 380, 90, "BEGIN ISOLATION LEVEL SERIALIZABLE\nREAD ONLY DEFERRABLE", P["bff_bg"], P["back"], size=14, mono=True)
    d.pill("p2", 510, 130, 380, 90, "안전한 스냅샷을 얻을 때까지\n시작 시점에 블록될 수 있다", P["todo_bg"], P["orange"], size=15)
    d.pill("p3", 980, 130, 380, 90, "이후: 일반 SERIALIZABLE 의 오버헤드 없이\n실패에 기여하지도 취소되지도 않는다", P["ok_bg"], P["green"], size=14)
    d.arrow([d.anchor("p1", "e"), d.anchor("p2", "w")], P["muted"], start="p1", end="p2")
    d.arrow([d.anchor("p2", "e"), d.anchor("p3", "w")], P["muted"], start="p2", end="p3")
    d.card("n", 40, 260, 1320, 130, "\"Serializable 은 블록되는데 Repeatable Read 는 안 되는 유일한 경우\" (문서 13.2.3)",
           "READ ONLY 선언만으로도 SSI 가 더 효율적이다 (문서 13.2.3 성능 팁, README-SSI)\n"
           "SERIALIZABLE 에서 읽은 데이터는 커밋에 성공하기 전까지는 유효하다고 여기면 안 된다 — 읽기 전용이어도 (단 DEFERRABLE 읽기 전용은 읽는 즉시 유효)",
           bg=P["note_bg"], stroke=P["line"], title_size=15, body_size=14)
    d.save()


def retry_loop():
    d = Diagram("blog05-retry-loop", 1400, 700, "재시도 설계 — Tx.serializable 한 시도의 흐름",
                "재시도의 단위는 work 전체다. 앞서 읽은 값이 이미 틀렸기 때문이다", out=OUT)
    d.card("s", 40, 110, 420, 120, "시도 시작", "새 커넥션 · setAutoCommit(false) ·\nTRANSACTION_SERIALIZABLE\n(실패한 트랜잭션은 중단 상태 25P02 라 재사용 불가)",
           bg=P["as_bg"], stroke=P["front"], title_size=16, body_size=13)
    d.card("w", 520, 110, 420, 120, "같은 try 안에서", "work.run(...)  그리고  commit()\n(40001 은 커밋 시점에도 난다)",
           bg=P["as_bg"], stroke=P["front"], title_size=16, body_size=13)
    d.card("ok", 1000, 110, 360, 120, "성공", "끝", bg=P["ok_bg"], stroke=P["green"], title_size=16, body_size=14)
    d.arrow([d.anchor("s", "e"), d.anchor("w", "w")], P["muted"], start="s", end="w")
    d.arrow([d.anchor("w", "e"), d.anchor("ok", "w")], P["green"], "예외 없음", start="w", end="ok")
    d.arrow([(730, 230), (730, 300)], P["red"], "예외")
    d.card("rb", 520, 300, 420, 80, "rollback()  후 SQLState 확인", None, bg=P["bad_bg"], stroke=P["red"], title_size=16)
    d.card("y", 40, 440, 600, 150, "SQLState == \"40001\"  -> work 전체를 다시",
           "상한 MAX_ATTEMPTS = 5 에서 포기하고 예외\n재시도 사이 5~25ms 무작위 대기 (같은 박자로 다시 부딪히지 않게)\n"
           "(두 값은 이 레슨의 선택이지 PostgreSQL 규정이 아니다 — 해석)",
           bg=P["todo_bg"], stroke=P["orange"], title_size=15, body_size=13)
    d.card("n", 720, 440, 640, 150, "40001 이 아니면 재시도하지 않는다 (예: 23505)",
           "다시 해도 똑같다 -> 예외를 그대로 올린다",
           bg=P["bad_bg"], stroke=P["red"], title_size=15, body_size=13)
    d.card("side", 40, 610, 1320, 70, "부수효과: 재시도는 work 를 다시 실행한다 — 그 안의 외부 API 호출 · 메시지 발행은 시도마다 중복된다", None,
           bg=P["note_bg"], stroke=P["line"], title_size=15)
    d.arrow([(450, 380), (340, 440)], P["red"], "40001")
    d.arrow([(820, 380), (960, 440)], P["red"], "그 외")
    d.save()


def spring_retry():
    d = Diagram("blog05-spring-retry", 1400, 560, "Spring 에서 재시도는 @Transactional 경계의 바깥에 둔다 (해석)",
                "트랜잭션은 프록시 경계에서 시작 · 종료된다. Spring 문서 자체는 재시도 위치를 규정하지 않는다", out=OUT)
    d.card("bad", 40, 110, 640, 250, "안쪽에서 catch 해 다시 시도",
           "@Transactional 메서드 안에서\ntry { ... } catch (40001) { 다시 }\n\n"
           "같은 중단된 트랜잭션 안에서 재실행하게 된다\n-> 25P02 (이후 문장 거절)",
           bg=P["bad_bg"], stroke=P["red"], title_size=17, body_size=14)
    d.card("good", 720, 110, 640, 250, "바깥에서 통째로 다시 호출",
           "호출하는 쪽(파사드 · 상위 서비스 · 별도 AOP)에서\n트랜잭션 메서드를 통째로 다시 호출\n\n"
           "-> 새 트랜잭션이 열린다",
           bg=P["ok_bg"], stroke=P["green"], title_size=17, body_size=14)
    d.card("self", 40, 390, 640, 130, "같은 클래스 안의 this.method() 호출",
           "프록시를 안 거쳐 트랜잭션이 안 열린다 (self-invocation 경고)\n-> 재시도 래퍼와 트랜잭션 메서드는 다른 빈에 둔다",
           bg=P["todo_bg"], stroke=P["orange"], title_size=15, body_size=14)
    d.card("rule", 720, 390, 640, 130, "롤백 규칙",
           "기본: RuntimeException · Error 는 롤백, 검사 예외는 롤백하지 않는다\n재시도 대상이 검사 예외로 감싸져 올라오면 롤백이 안 될 수 있다 -> rollbackFor 점검",
           bg=P["note_bg"], stroke=P["line"], title_size=15, body_size=13)
    d.save()


if __name__ == "__main__":
    for f in (intro, three_ways, forupdate, siread, dangerous, error_timing, false_positive, deferrable, retry_loop, spring_retry):
        f()
    finish()
