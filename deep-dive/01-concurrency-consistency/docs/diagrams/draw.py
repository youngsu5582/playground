#!/usr/bin/env python3
"""01 트랙 공통 docs 그림. 실행: python3 -I docs/diagrams/draw.py (트랙 폴더 01-concurrency-consistency 에서)"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "tools"))
from diagram import Diagram, P, finish  # noqa: E402

OUT = pathlib.Path(__file__).parent


def engine_map():
    d = Diagram("engine-map", 1400, 790, "PostgreSQL 16 엔진 지도 — 프로세스 · 공유 메모리 · 디스크",
                "연결 하나 = 백엔드 프로세스 하나. 프로세스들은 공유 메모리로 만나고, 내구성은 WAL 이 진다", out=OUT)
    d.card("cli", 40, 110, 300, 130, "클라이언트",
           "앱 (HikariCP 풀)\n선택: 앞단 PgBouncer\n연결 하나가 백엔드 하나로 이어진다",
           bg=P["as_bg"], stroke=P["front"], title_size=16, body_size=14)
    d.card("pm", 40, 300, 300, 130, "postmaster (최초 프로세스)",
           "연결 요청이 오면 백엔드를 만든다\n보조 프로세스도 이것이 관리한다\n컨테이너 실측: PID 1",
           bg=P["note_bg"], stroke=P["muted"], title_size=16, body_size=14)
    d.card("be", 400, 110, 400, 130, "client backend (연결 1개 = 1개)",
           "SQL 실행 · 스냅샷 · 락 요청 · WAL 기록\n실측 ps: postgres: lab lab [local] SELECT\n여기서 보는 것: 01.01 ~ 01.05 전부",
           bg=P["bff_bg"], stroke=P["back"], title_size=16, body_size=14)
    d.card("aux", 400, 300, 400, 250, "보조 프로세스 (실측 ps · backend_type)",
           "checkpointer     체크포인트 실행\nbackground writer  더러운 페이지를 디스크로\nwalwriter           WAL 버퍼를 디스크로\nautovacuum launcher  worker 를 띄움\n(autovacuum worker 는 launcher 가 띄움)\nstartup  크래시 복구 때 WAL 재생",
           bg=P["note_bg"], stroke=P["line"], title_size=16, body_size=14)
    d.card("shm", 860, 110, 500, 250, "공유 메모리",
           "shared_buffers    데이터 페이지 캐시 (보통 128MB)\nWAL 버퍼          아직 디스크에 안 간 WAL\n락 테이블          무거운 락 (01.02 · 01.03)\npredicate 락 테이블  SIREAD 락 (01.01 문서 05)\n\n프로세스들이 같은 메모리를 보며 협력한다",
           bg=P["todo_bg"], stroke=P["orange"], title_size=16, body_size=14)
    d.card("disk", 860, 420, 500, 250, "디스크 (데이터 디렉터리)",
           "base/     테이블 · 인덱스 데이터 파일\npg_wal/   WAL 파일 (커밋의 내구성은 여기)\npg_xact/  트랜잭션 커밋 상태 (01.01 문서 02)\n\n커밋 = pg_wal 에 WAL 이 닿음\n데이터 페이지는 나중에 써도 된다",
           bg=P["ok_bg"], stroke=P["green"], title_size=16, body_size=14)
    d.card("note", 40, 590, 760, 140, "커밋이 일어나는 순서 (문서 01 · 30장)",
           "1  변경을 WAL 버퍼에 기록   2  커밋 시 WAL 을 pg_wal 로 flush (synchronous_commit = on)\n"
           "3  클라이언트에 성공 응답    4  데이터 페이지는 bgwriter · checkpointer 가 나중에\n"
           "크래시 → 마지막 체크포인트의 redo 지점부터 WAL 재생",
           bg=P["white"], stroke=P["line"], title_size=15, body_size=14)
    d.arrow([d.anchor("cli", "s"), d.anchor("pm", "n")], P["front"], "연결", start="cli", end="pm")
    d.arrow([(340, 365), (370, 365), (370, 175), (400, 175)], P["back"], "생성", start="pm", end="be")
    d.arrow([d.anchor("be", "e"), (860, 175)], P["orange"], None, start="be", end="shm")
    d.arrow([(800, 500), (860, 500)], P["green"], None, start="aux", end="disk")
    d.arrow([(800, 330), (830, 330), (830, 300), (860, 300)], P["orange"], None, start="aux", end="shm")
    d.save()


if __name__ == "__main__":
    engine_map()
    finish()
