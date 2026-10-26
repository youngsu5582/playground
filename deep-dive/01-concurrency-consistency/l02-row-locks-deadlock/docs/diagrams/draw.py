#!/usr/bin/env python3
"""01.02 docs 그림. 실행: python3 -I docs/diagrams/draw.py (레슨 폴더에서)"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[4] / "tools"))
from diagram import Diagram, P, finish  # noqa: E402

OUT = pathlib.Path(__file__).parent


def wait_queue():
    d = Diagram("wait-queue", 1400, 700, "줄 서기의 실제 모양 — pg_stat_activity 에 찍힌 것",
                "행 락 줄(위)과 테이블 락 줄(아래). 숫자는 이 랩의 실측 (psql 2026-10-13)", out=OUT)
    d.rect("p1", 30, 100, 1340, 270, P["white"], P["line"], dashed=True)
    d.text(50, 112, "행 락 — 같은 행 UPDATE 세 개", 16, P["ink"], weight=700)
    d.card("a", 60, 150, 360, 190, "세션 A  (pid 162)",
           "FOR UPDATE 로 행을 잡고 열어 둠\nstate = idle in transaction\nwait_event = ClientRead\nblocked_by = {}\n자기 트랜잭션 ID 758 에 ExclusiveLock",
           bg=P["ok_bg"], stroke=P["green"], title_size=15, body_size=13)
    d.card("b", 520, 150, 400, 190, "세션 B  (pid 168)  — 줄의 맨 앞",
           "UPDATE 가 멈춤\nwait_event = Lock / transactionid\nblocked_by = {162}\nA 의 ID 758 에 ShareLock 을 기다림 (granted=f)\n행의 tuple 락은 B 가 잡음",
           bg=P["todo_bg"], stroke=P["orange"], title_size=15, body_size=13)
    d.card("c", 1010, 150, 340, 190, "세션 C  (pid 175)  — B 뒤",
           "같은 행 UPDATE 가 멈춤\nwait_event = Lock / tuple\nblocked_by = {168}  (A 가 아니라 B)\ntuple 락 ExclusiveLock 을 기다림 (granted=f)",
           bg=P["bad_bg"], stroke=P["red"], title_size=15, body_size=13)
    d.arrow([d.anchor("b", "w"), d.anchor("a", "e")], P["orange"], "기다린다", start="b", end="a")
    d.arrow([d.anchor("c", "w"), d.anchor("b", "e")], P["red"], "기다린다", start="c", end="b")

    d.rect("p2", 30, 390, 1340, 280, P["white"], P["line"], dashed=True)
    d.text(50, 402, "테이블 락 — 읽기만 하던 쿼리가 ALTER 뒤에 선다", 16, P["ink"], weight=700)
    d.card("t1", 60, 440, 360, 200, "세션 1  (pid 297)",
           "BEGIN; SELECT count(*) FROM jobs;\n후 열어 둠 (idle in transaction)\nAccessShareLock  granted = t\nblocked_by = {}",
           bg=P["ok_bg"], stroke=P["green"], title_size=15, body_size=13)
    d.card("t2", 520, 440, 400, 200, "세션 2  (pid 304)  — ALTER TABLE",
           "ALTER TABLE jobs ADD COLUMN …\nwait_event = Lock / relation\nAccessExclusiveLock  granted = f\nblocked_by = {297}",
           bg=P["todo_bg"], stroke=P["orange"], title_size=15, body_size=13)
    d.card("t3", 1010, 440, 340, 200, "세션 3  (pid 311)  — 평범한 SELECT",
           "SELECT count(*) FROM jobs\nwait_event = Lock / relation\nAccessShareLock  granted = f\nblocked_by = {304}  (ALTER 에 막힘)",
           bg=P["bad_bg"], stroke=P["red"], title_size=15, body_size=13)
    d.arrow([d.anchor("t2", "w"), d.anchor("t1", "e")], P["orange"], "기다린다", start="t2", end="t1")
    d.arrow([d.anchor("t3", "w"), d.anchor("t2", "e")], P["red"], "기다린다", start="t3", end="t2")
    d.save()


def multixact():
    d = Diagram("multixact", 1400, 520, "행 락은 튜플 헤더에 적힌다 — 둘 이상이 잡으면 MultiXact",
                "FOR KEY SHARE(A)와 FOR SHARE(B)가 같은 행을 잡았을 때 (실측: psql 2026-10-13, pageinspect)", out=OUT)
    d.card("one", 40, 110, 400, 190, "한 트랜잭션이 잡을 때",
           "t_xmax = 잠근 트랜잭션 ID\n플래그 HEAP_XMAX_LOCK_ONLY\n= \"xmax 는 삭제자가 아니라 잠금자\"\n(01.01 docs 04 실측: xmax = 761)",
           bg=P["note_bg"], stroke=P["line"], title_size=15, body_size=13)
    d.card("two", 500, 110, 420, 190, "둘 이상이 잡을 때",
           "t_xmax = 2  (MultiXact ID)\n플래그 LOCK_ONLY + IS_MULTI\n행 헤더에는 MultiXact ID 하나만 있다\n(예: 두 트랜잭션이 같은 행에 락을 건 경우)",
           bg=P["todo_bg"], stroke=P["orange"], title_size=15, body_size=13)
    d.card("mem", 980, 110, 380, 190, "pg_multixact 에 따로 저장",
           "pg_get_multixact_members(2)\n  756   keysh   (A: FOR KEY SHARE)\n  757   sh      (B: FOR SHARE)\n각 멤버가 어떤 모드로 잡았는지 함께 기록",
           bg=P["as_bg"], stroke=P["front"], title_size=15, body_size=13, mono_body=True)
    d.arrow([d.anchor("one", "e"), d.anchor("two", "w")], P["muted"], "둘째 잠금자", start="one", end="two")
    d.arrow([d.anchor("two", "e"), d.anchor("mem", "w")], P["muted"], "멤버 목록", start="two", end="mem")
    d.card("eff", 40, 340, 1320, 130, "그래서 생기는 일",
           "행 락 정보는 공유 메모리의 락 테이블이 아니라 디스크의 튜플에 있다 → 잠글 수 있는 행 수에 제한이 없다 (문서 13.3.2)\n"
           "대신 SELECT FOR UPDATE 도 페이지를 더럽힌다(디스크 쓰기). 그래서 pg_locks 에는 행 락이 한 줄씩 나오지 않는다 (문서 pg_locks)\n"
           "MultiXact 도 wraparound 를 피하려면 VACUUM 이 정리해야 한다 (문서 25.1.5.1)",
           bg=P["note_bg"], stroke=P["line"], title_size=15, body_size=13)
    d.save()


if __name__ == "__main__":
    wait_queue()
    multixact()
    finish()
