#!/usr/bin/env python3
"""01.02 블로그판 02 그림. 실행: python3 -I docs/diagrams/draw_blog02.py (레슨 폴더에서)"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[4] / "tools"))
from diagram import Diagram, P, finish, timeline as _timeline  # noqa: E402

OUT = pathlib.Path(__file__).parent


def timeline(*a, **k):
    return _timeline(*a, out=OUT, **k)


def intro():
    timeline("blog02-intro", "도입: UPDATE 한 줄이 안 끝난다",
             "주문 42번을 두고 두 세션이 만난다. 한쪽은 아직 커밋하지 않았다",
             [("A", "1  UPDATE orders SET status = 'PAID' WHERE id = 42", "BEGIN 뒤, 행 락을 쥔 채 결제 API 를 호출한다", None),
              ("B", "2  UPDATE orders SET memo = '확인' WHERE id = 42", "같은 행 — 쿼리가 끝나지 않는다", "bad"),
              ("A", "3  (API 응답을 기다리는 중)", "DB 에서는 idle in transaction — 실행 중 쿼리 없음", None)],
             [(0, 1, "A 의 행 락이\nB 를 멈춘다")],
             "B 의 쿼리만 보면 \"UPDATE 한 줄이 안 끝난다\" 로 보인다. 진짜 원인은 아무것도 안 하면서 락을 쥐고 있는 A 다.\n"
             "그래서 \"쿼리가 안 끝난다\" 와 \"락을 기다린다\" 를 구분하는 일, 그리고 막는 쪽을 찾는 일이 장애 대응의 시작이다.",
             "막힌 쪽을 봐서는 원인이 안 보인다")


def xid_lock():
    d = Diagram("blog02-xid-lock", 1400, 520, "행 락 대기의 정체 — 상대 트랜잭션 ID 를 기다린다",
                "행 락 충돌에서 기다리는 쪽은 그 행의 현재 xmax 트랜잭션이 끝나기를 기다린다 (pg_locks 문서)", out=OUT)
    d.card("a", 40, 130, 520, 190, "트랜잭션 A — 행을 쥔 쪽",
           "모든 트랜잭션은 자기 ID 에 ExclusiveLock 을 쥐고 있다\n(영구 트랜잭션 ID 가 배정된 뒤)\n\n행 락 자체는 튜플 xmax 에 적혀 있다",
           bg=P["ok_bg"], stroke=P["green"], title_size=16, body_size=14)
    d.card("b", 840, 130, 520, 190, "트랜잭션 B — 같은 행을 쓰려는 쪽",
           "행의 현재 보유자(A)의 트랜잭션 ID 에\nShareLock 을 요청한다 → 충돌 → 기다린다\n\npg_stat_activity: Lock / transactionid",
           bg=P["todo_bg"], stroke=P["orange"], title_size=16, body_size=14)
    d.arrow([d.anchor("b", "w"), d.anchor("a", "e")], P["orange"], "A 의 트랜잭션 ID 에\nShareLock 요청", start="b", end="a", label_size=13)
    d.card("end", 40, 350, 1320, 130, "A 가 커밋 · 롤백하면",
           "A 의 ExclusiveLock 이 풀리고 → B 의 ShareLock 요청이 통과해 대기가 깨어난다\n"
           "락의 주인은 \"행\" 이 아니라 \"트랜잭션\" 이다 — 행 하나가 아니라 A 가 쥔 모든 락이 한꺼번에 풀리는 이유",
           bg=P["as_bg"], stroke=P["front"], title_size=16, body_size=14)
    d.save()


def hard_soft():
    d = Diagram("blog02-hard-soft", 1400, 570, "pg_blocking_pids() 가 가리키는 두 가지 \"막는 쪽\"",
                "막는 프로세스 PID 배열을 돌려준다 — 막는 방식이 둘이다 (문서 9.27)", out=OUT)
    d.text(40, 104, "hard block — 충돌하는 락을 쥐고 있다", 17, P["red"], weight=700)
    d.card("h1", 40, 140, 360, 100, "세션 X", "충돌하는 락을 보유 (granted)", bg=P["ok_bg"], stroke=P["green"], title_size=15, body_size=14)
    d.card("h2", 560, 140, 400, 100, "세션 Y", "같은 대상의 락을 요청 — 기다린다", bg=P["todo_bg"], stroke=P["orange"], title_size=15, body_size=14)
    d.arrow([d.anchor("h2", "w"), d.anchor("h1", "e")], P["red"], "Y 는 X 에게 막힌다", start="h2", end="h1")
    d.text(1010, 180, "pg_blocking_pids(Y) = {X}", 15, P["ink"], mono=True)
    d.text(40, 284, "soft block — 충돌할 락을 기다리면서, 대기 큐에서 나보다 앞에 있다", 17, P["red"], weight=700)
    d.card("s1", 40, 320, 300, 110, "세션 X", "락을 보유 (granted)", bg=P["ok_bg"], stroke=P["green"], title_size=15, body_size=14)
    d.card("s2", 460, 320, 300, 110, "세션 Y — 큐의 앞", "충돌하는 락을 요청 — 기다린다", bg=P["todo_bg"], stroke=P["orange"], title_size=15, body_size=14)
    d.card("s3", 880, 320, 400, 110, "세션 Z — 큐의 뒤", "Y 가 요청한 락과 충돌할 락을 요청", bg=P["bad_bg"], stroke=P["red"], title_size=15, body_size=14)
    d.arrow([d.anchor("s2", "w"), d.anchor("s1", "e")], P["red"], "hard", start="s2", end="s1")
    d.arrow([d.anchor("s3", "w"), d.anchor("s2", "e")], P["red"], "soft", start="s3", end="s2")
    d.text(460, 440, "pg_blocking_pids(Z) 에는 Y 가 soft block 으로 들어간다 — Y 가 아직 락을 얻지 못했는데도", 14, P["ink"])
    d.card("note", 40, 480, 1320, 70, "알아 둘 것 (문서 9.27)",
           "병렬 쿼리에서는 클라이언트가 보는 PID 로 나와 중복이 있을 수 있다 · 준비된(prepared) 트랜잭션이 쥔 락은 PID 0 · 자주 부르면 성능에 영향(락 매니저 상태에 잠깐 배타 접근)",
           bg=P["note_bg"], stroke=P["line"], title_size=15, body_size=14)
    d.save()


def ddl_queue():
    d = Diagram("blog02-ddl-queue", 1400, 600, "읽기만 하던 쿼리가 ALTER 뒤에 선다",
                "세 세션, 같은 테이블 jobs (실측: psql 2026-10-13). 화살표는 \"기다린다\"", out=OUT)
    d.card("s1", 40, 130, 360, 200, "세션 1 — 먼저 왔다",
           "BEGIN; SELECT count(*) FROM jobs;\n후 열어 둠 (idle in transaction)\nACCESS SHARE 를 쥐고 있다\nblocked_by = {}",
           bg=P["ok_bg"], stroke=P["green"], title_size=16, body_size=14)
    d.card("s2", 520, 130, 360, 200, "세션 2 — ALTER TABLE",
           "ALTER TABLE jobs ADD COLUMN …\nACCESS EXCLUSIVE 를 요청\nwait_event = relation  (granted = f)\nblocked_by = {세션 1}",
           bg=P["todo_bg"], stroke=P["orange"], title_size=16, body_size=14)
    d.card("s3", 1000, 130, 360, 200, "세션 3 — 평범한 SELECT",
           "SELECT count(*) FROM jobs\nACCESS SHARE 를 요청\nwait_event = relation  (granted = f)\nblocked_by = {세션 2}",
           bg=P["bad_bg"], stroke=P["red"], title_size=16, body_size=14)
    d.arrow([d.anchor("s2", "w"), d.anchor("s1", "e")], P["orange"], "기다린다", start="s2", end="s1")
    d.arrow([d.anchor("s3", "w"), d.anchor("s2", "e")], P["red"], "기다린다", start="s3", end="s2")
    d.card("why", 40, 370, 1320, 90, "왜 읽기가 막히나",
           "세션 1 의 ACCESS SHARE 와 세션 3 의 ACCESS SHARE 는 충돌하지 않는데도, ALTER 가 큐에 서 있다는 이유만으로 세션 3 이 막힌다 (soft block)",
           bg=P["note_bg"], stroke=P["line"], title_size=15, body_size=14)
    d.card("lesson", 40, 480, 1320, 90, "교훈",
           "긴 트랜잭션이 열려 있는 테이블에 DDL 을 던지면 DDL 자신이 아니라 그 뒤에 오는 모든 쿼리가 멈춘다\n"
           "DDL 에 lock_timeout 을 짧게 걸어 큐에 오래 서 있지 않게 한다 (해석 — 운영 판단, 문서가 권한 것은 아님)",
           bg=P["as_bg"], stroke=P["front"], title_size=15, body_size=14)
    d.save()


def monitor():
    d = Diagram("blog02-monitor", 1400, 540, "원인 세션을 찾는 두 걸음",
                "먼저 막힌 쪽을 나열하고, 사슬의 루트(남을 막지만 자신은 안 막힌 쪽)를 찾는다", out=OUT)
    d.card("q1", 40, 120, 560, 220, "1. 막힌 쪽 목록",
           "pg_stat_activity 에서\ncardinality(pg_blocking_pids(pid)) > 0 인 행\n\n보이는 것: pid · state · wait_event_type · wait_event ·\nblocked_by · 얼마나 기다렸나 · 쿼리 앞부분\n\n이쪽은 \"피해자\" 다",
           bg=P["bad_bg"], stroke=P["red"], title_size=16, body_size=14)
    d.card("q2", 800, 120, 560, 220, "2. 루트 원인",
           "다른 세션의 blocked_by 에 등장하지만\n자신의 pg_blocking_pids 는 비어 있는 세션\n\n보이는 것: pid · state · xact_age · 마지막 쿼리\n\n대개 state = idle in transaction",
           bg=P["ok_bg"], stroke=P["green"], title_size=16, body_size=14)
    d.arrow([d.anchor("q1", "e"), d.anchor("q2", "w")], P["muted"], "사슬을 따라 간다", start="q1", end="q2")
    d.card("last", 40, 370, 1320, 130, "루트가 idle in transaction 이면",
           "마지막 쿼리(last_query)가 그 트랜잭션이 마지막으로 한 일이다 — 락을 쥔 문장이 거기 있다\n"
           "wait_event = ClientRead 는 \"클라이언트가 다음 명령을 보내기를 기다린다\" 는 뜻이지 락 대기가 아니다",
           bg=P["as_bg"], stroke=P["front"], title_size=16, body_size=14)
    d.save()


if __name__ == "__main__":
    for f in (intro, xid_lock, hard_soft, ddl_queue, monitor):
        f()
    finish()
