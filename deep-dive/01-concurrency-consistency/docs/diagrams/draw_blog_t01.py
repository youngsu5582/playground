#!/usr/bin/env python3
"""01 트랙 블로그판 01 (엔진 지도) 그림. 실행: python3 -I docs/diagrams/draw_blog_t01.py (트랙 폴더 01-concurrency-consistency 에서)"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from blog_common import Diagram, P, finish, tw, kc, vchain, hchain, sequence, matrix, new, card_h, ARROW  # noqa: E402


def journey():
    specs = [
        ("1  연결이 들어온다", "postmaster 가 요청을 받아 연결마다 백엔드 프로세스를 새로 만든다", "a"),
        ("2  백엔드가 SQL 을 실행한다", "공유 메모리의 shared_buffers 에서 데이터 페이지를 읽고, 필요한 락을 락 테이블에 요청한다", "b"),
        ("3  변경을 WAL 에 적는다", "데이터 페이지를 고치기 전에, 그 변경을 설명하는 WAL 레코드를 WAL 버퍼에 기록한다", "warn"),
        ("4  COMMIT — WAL 을 디스크로 flush", "pg_wal 에 WAL 이 닿으면 커밋이 내구성을 얻는다 (synchronous_commit = on, 기본)", "ok"),
        ("5  데이터 페이지는 나중에", "background writer · checkpointer 가 더러운 페이지를 데이터 파일에 쓴다", "note"),
        ("6  크래시가 나면", "마지막 체크포인트의 redo 지점부터 WAL 을 재생해 복구한다", "bad"),
    ]
    notes = {0: "프로세스 모델", 1: "공유 메모리 · 락의 층", 2: "WAL", 3: "WAL · synchronous_commit", 4: "체크포인트", 5: "크래시 복구"}
    d = vchain("blog-t01-journey", "연결 하나가 들어와서 커밋되기까지",
               "이 글이 따라갈 길 — 오른쪽은 그 단계를 다루는 절", specs,
               labels=("SQL", "변경", "COMMIT", "나중에", "크래시"), w=1240, cw=860, gap=44, notes=None)
    # 오른쪽 절 이름
    y = 100
    for i, (t, b, k) in enumerate(specs):
        h = card_h(t, b)
        d.text(940, y + h / 2 - 9, notes[i], 15, P["muted"])
        y += h + 44
    d.save()


def processes():
    d = new("blog-t01-processes", 1400, 640, "ps 로 본 인스턴스 — postmaster 와 그 자식들",
            "(실측: psql 2026-10-13, PostgreSQL 16.14 컨테이너) 연결 1개 = 프로세스 1개")
    d.card("pm", 40, 130, 380, 160, "postmaster  (PID 1)",
           "인스턴스의 맨 처음 프로세스\n보조 프로세스를 시작 · 관리하고\n연결 요청마다 백엔드를 만든다",
           bg=P["note_bg"], stroke=P["muted"], title_size=17, body_size=14)
    rows = [("checkpointer  (PID 62)", "체크포인트 실행", "ok"),
            ("background writer  (PID 63)", "더러운 데이터 페이지를 파일 시스템에 쓴다", "ok"),
            ("walwriter  (PID 65)", "공유 메모리의 WAL 레코드를 WAL 파일에 쓴다", "ok"),
            ("autovacuum launcher  (PID 66)", "VACUUM · ANALYZE 를 돌릴 worker 를 띄운다", "ok"),
            ("logical replication launcher  (PID 67)", "논리 복제 (이 글에서는 다루지 않음)", "note"),
            ("postgres: lab lab [local] SELECT  (PID 97)", "client backend — 연결 1개 = 프로세스 1개", "a")]
    y = 110
    for i, (t, b, k) in enumerate(rows):
        bg, st = kc(k)
        d.pill(f"r{i}", 560, y, 780, 62, f"{t}\n{b}", bg, st, size=14)
        d.arrow([(420, 210), (490, 210), (490, y + 31), (560, y + 31)], ARROW[k], None, start="pm", end=f"r{i}")
        y += 74
    bg, st = kc("w")
    d.pill("st", 560, y, 780, 52, "startup — 크래시 복구 때만 WAL 재생 (평상시에는 없다)", bg, P["line"], size=14)
    d.text(40, 330, "보조 프로세스는 pg_stat_activity 에서\nwait_event_type = Activity 로 일을 기다린다\n(CheckpointerMain · BgWriterMain ·\nWalWriterMain · AutoVacuumMain)", 14, P["muted"])
    d.text(40, 450, "운영 쿼리에 backend_type = 'client backend'\n를 붙이는 이유: 붙이지 않으면 위 보조\n프로세스가 섞여 나온다", 14, P["muted"])
    d.save()


def memory():
    d = matrix("blog-t01-memory", "공유 메모리에는 무엇이 있나",
               "프로세스들이 같은 RAM 을 보며 협력한다 — 영역마다 크기를 정하는 설정이 따로 있다 (PostgreSQL 16)",
               ["무엇을 담나", "크기를 정하는 설정", "어느 글과 이어지나"],
               [("shared_buffers", [("데이터 페이지 캐시", "a"), ("shared_buffers\n보통 128MB · 서버 시작 때만 변경", "w"),
                                    ("01.01: 튜플 버전(xmin/xmax)이\n든 힙 페이지가 여기서 읽힌다", "w")]),
                ("WAL 버퍼", [("아직 디스크에 쓰지 않은\nWAL 데이터", "a"), ("wal_buffers  기본 -1 =\nshared_buffers 의 1/32 (실측 4MB)", "w"),
                              ("3절 WAL 과 커밋 내구성", "w")]),
                ("무거운 락 테이블", [("테이블 락 · transactionid ·\nadvisory 락 (객체 단위)", "a"), ("max_locks_per_transaction\n기본 64 · 행이 아니라 객체", "w"),
                                      ("01.02 · 01.03", "w")]),
                ("predicate 락 테이블", [("SIREAD 락\n(SERIALIZABLE 의 감시)", "a"), ("max_pred_locks_per_transaction\n기본 64", "w"),
                                         ("01.01 문서 05", "w")]),
                ("커밋 상태 (pg_xact)", [("트랜잭션 커밋 상태 데이터\n(디스크의 pg_xact)", "a"), ("메모리 캐시 구조는 이 문서에서\n확인하지 못했다", "warn"),
                                         ("01.01 문서 02 · 03: 가시성 판정", "w")])],
               w=1400, first_w=250, row_h=78, size=14)
    d.save()


def wal_commit():
    d = sequence("blog-t01-wal-commit", "커밋은 WAL 이 디스크에 닿는 것이다",
                 "synchronous_commit = on (기본) — 데이터 페이지는 나중에 써도 된다",
                 [("클라이언트", "a"), ("백엔드", "b"), ("WAL 버퍼 (공유 메모리)", "warn"), ("pg_wal (디스크)", "ok"), ("데이터 파일 (디스크)", "note")],
                 [("note", 0, "UPDATE ...; COMMIT;", "a"),
                  ("msg", 1, 2, "1  변경을 WAL 레코드로 기록", "warn"),
                  ("msg", 1, 3, "2  COMMIT 시 WAL flush", "ok"),
                  ("msg", 1, 0, "3  성공 응답", "a"),
                  ("note", 4, "4  더러운 페이지는 나중에\nbgwriter · checkpointer 가\n디스크에 쓴다", "note")],
                 w=1400, pitch=78,
                 bottom_note=("크래시가 나면", "마지막 체크포인트의 redo 지점부터 pg_wal 의 WAL 을 재생한다 — 데이터 파일에 안 간 변경도 WAL 로 복구된다", "bad"))
    d.save()


def checkpoint():
    d = new("blog-t01-checkpoint", 1400, 560, "체크포인트와 크래시 복구",
            "체크포인트 = 모든 더러운 페이지를 디스크로 flush 하고 특별한 체크포인트 레코드를 WAL 에 기록한다")
    d.arrow([(40, 190), (1360, 190)], P["muted"], "WAL 이 쌓이는 방향", label_at=(1200, 168))
    d.rect("seg1", 40, 215, 560, 80, P["ok_bg"], P["green"])
    d.text(320, 255, "redo 지점 이전\n데이터 파일 변경은 이미 디스크에 있다고 보장", 15, P["ink"], align="center", valign="middle")
    d.rect("seg2", 600, 215, 560, 80, P["todo_bg"], P["orange"])
    d.text(880, 255, "redo 지점부터 끝까지\n데이터 페이지에 반영 안 된 변경이 있을 수 있다 → REDO", 15, P["ink"], align="center", valign="middle")
    d.pill("crash", 1180, 215, 180, 80, "크래시", P["bad_bg"], P["red"], size=17)
    d.pill("cp", 450, 110, 300, 50, "체크포인트 레코드 → redo 지점을 알려 준다", P["as_bg"], P["front"], size=14)
    d.arrow([(600, 160), (600, 215)], P["front"], None)
    d.arrow([(1270, 295), (1270, 340), (600, 340), (600, 297)], P["red"], "크래시 뒤: 여기서부터 WAL 재생", label_at=(930, 340))
    d.card("when", 40, 380, 640, 150, "체크포인트는 언제 시작하나",
           "checkpoint_timeout (기본 5분) 마다\n또는 max_wal_size (기본 1GB) 가 곧 넘을 때 — 빠른 쪽\n그 사이 WAL 이 안 쓰였으면 건너뛴다\nSQL CHECKPOINT 로 강제할 수 있다",
           bg=P["note_bg"], stroke=P["line"], title_size=16, body_size=14)
    d.card("meas", 720, 380, 640, 150, "실측 (psql 2026-10-13) — CHECKPOINT 뒤 서버 로그",
           "checkpoint starting: immediate force wait\ncheckpoint complete: wrote 124 buffers (0.8%) …\n                    redo lsn=0/19C6DE0\nlog_checkpoints 는 16 에서 기본 on",
           bg=P["white"], stroke=P["line"], title_size=15, body_size=14, mono_body=True)
    d.save()


def sync_commit():
    d = new("blog-t01-sync-commit", 1400, 560, "synchronous_commit — 성공 응답과 \"안 사라짐\" 사이의 틈",
            "문서 30.4 · 20.5 — WAL writer 가 wal_writer_delay 마다 flush 한다. 위험은 데이터 손실이지 손상이 아니다. fsync = off 는 손상이다")
    # on
    d.pill("onl", 40, 120, 190, 60, "on  (기본)", P["ok_bg"], P["green"], size=16)
    d.pill("on1", 260, 120, 190, 60, "COMMIT", P["as_bg"], P["front"], size=15)
    d.pill("on2", 520, 120, 270, 60, "WAL flush 가 끝날 때까지 대기", P["ok_bg"], P["green"], size=14)
    d.pill("on3", 860, 120, 230, 60, "성공 응답", P["as_bg"], P["front"], size=15)
    d.arrow([(450, 150), (520, 150)], P["muted"], None)
    d.arrow([(790, 150), (860, 150)], P["muted"], None)
    d.text(1120, 138, "응답 시점에 WAL 이 이미 디스크에 있다", 14, P["green"])
    # off
    d.pill("offl", 40, 230, 190, 60, "off", P["bad_bg"], P["red"], size=16)
    d.pill("of1", 260, 230, 190, 60, "COMMIT", P["as_bg"], P["front"], size=15)
    d.pill("of2", 520, 230, 170, 60, "성공 응답", P["as_bg"], P["front"], size=15)
    d.pill("of3", 760, 230, 330, 60, "WAL flush 는 뒤에 (walwriter)", P["rs_bg"], P["orange"], size=14)
    d.arrow([(450, 260), (520, 260)], P["muted"], None)
    d.arrow([(690, 260), (760, 260)], P["muted"], None)
    d.rect("win", 520, 300, 570, 14, P["bad_bg"], P["red"], rounded=False)
    d.text(805, 322, "위험 창 — 최대 wal_writer_delay (기본 200ms) 의 3배", 14, P["red"], align="center")
    d.text(1120, 248, "이 창에서 크래시가 나면 최근 커밋이 사라진다\nDB 는 일관 상태로 복구된다 (커밋 순서대로 재생)", 14, P["ink"])
    d.card("cmp", 40, 380, 640, 150, "synchronous_commit = off",
           "위험의 종류: 최근 커밋 몇 개의 손실 (손상 아님)\n트랜잭션마다 고를 수 있다 (동기 · 비동기가 동시에 돈다)\nDROP TABLE 같은 유틸리티 명령과 2PC 는\n설정과 무관하게 동기 커밋",
           bg=P["note_bg"], stroke=P["line"], title_size=16, body_size=14)
    d.card("fs", 720, 380, 640, 150, "fsync = off  (기본 on)",
           "위험의 종류: 정전 · 크래시 때 복구할 수 없는 손상\nfsync = on 이어도 디스크 쓰기 캐시가 비휘발성이 아니면\n하드웨어가 거짓말해 내구성이 없을 수 있다\n(많은 SSD 는 기본으로 flush 명령을 지키지 않는다고 문서가 경고)",
           bg=P["bad_bg"], stroke=P["red"], title_size=16, body_size=14)
    d.save()


def lock_layers():
    d = matrix("blog-t01-lock-layers", "락의 네 층 (lmgr README)",
               "위에서 아래로 갈수록 사용자가 가까이 보는 락이 된다 — 데드락 검출은 일반 락에만 있다",
               ["성격", "데드락 검출 · 해제", "사용자가 보는 곳"],
               [("스핀락 (spinlock)", [("아주 짧은 시간용\n기다리는 쪽이 바쁘게 돈다", "w"), ("검출 없음\n에러 때 자동 해제 없음", "bad"), ("직접 안 보인다\n(엔진 내부)", "note")]),
                ("LWLock (lightweight)", [("공유 메모리 자료구조 접근을\n맞춘다 · 배타 / 공유 모드", "w"), ("검출 없음\n에러 복구 때 자동 해제", "bad"),
                                          ("wait_event_type = LWLock\n(예: ProcArray)", "a")]),
                ("일반(무거운) 락", [("다중 모드 · 충돌 규칙 표\n사용자 요청 락은 이걸 쓴다", "w"), ("검출 있음\n트랜잭션 끝에 자동 해제", "ok"),
                                     ("pg_locks: relation ·\ntransactionid · tuple · advisory", "a")]),
                ("SIReadLock (predicate)", [("README 는 README-SSI 로 넘긴다", "w"), ("블로킹하지 않아\n데드락에 참여하지 않는다", "ok"),
                                            ("pg_locks.mode = SIReadLock", "a")])],
               w=1400, first_w=250, row_h=84, size=14)
    d.save()


def row_lock_where():
    d = new("blog-t01-row-lock-where", 1400, 540, "락은 어디에 저장되나 — 객체 락 vs 행 락",
            "행 락이 수백만 개여도 락 테이블이 안 터지는 이유")
    d.card("lt", 40, 110, 620, 190, "공유 메모리의 락 테이블",
           "테이블 락 · transactionid 락 · advisory 락\n한도: 서버 프로세스당 max_locks_per_transaction 개 객체 (기본 64)\n그 한도는 행이 아니라 객체다\nadvisory 락도 같은 풀 — 다 쓰면 서버가 어떤 락도\n줄 수 없게 된다 (문서 13.3)",
           bg=P["todo_bg"], stroke=P["orange"], title_size=17, body_size=14)
    d.card("tp", 740, 110, 620, 190, "튜플 자체 (디스크의 힙 페이지)",
           "행 락은 수정된 행에 표시를 남긴다\n메모리에 기억하지 않으므로 잠글 수 있는 행 수에 제한이 없다\n대신 SELECT FOR UPDATE 는 행을 수정해 잠금 표시를 하므로\n디스크 쓰기가 생긴다",
           bg=P["ok_bg"], stroke=P["green"], title_size=17, body_size=14)
    d.card("pl", 40, 360, 1320, 140, "pg_locks 에서는 이렇게 보인다",
           "행 락 정보는 디스크에 있어 보통 이 뷰에 나타나지 않는다\n행 락을 기다리는 프로세스는 그 행 락을 쥔 현재 트랜잭션의 영구 트랜잭션 ID 를 기다리는 모습으로 보인다 (locktype = transactionid)\n모든 트랜잭션은 자기 가상 ID 에 배타 락을 쥐고, 다른 트랜잭션의 끝을 기다릴 때는 그 ID 에 공유 락을 요청한다",
           bg=P["white"], stroke=P["line"], title_size=16, body_size=14)
    d.arrow([(350, 300), (350, 360)], P["orange"], None)
    d.arrow([(1050, 300), (1050, 360)], P["green"], "대기자는 ID 로", label_at=(1160, 330))
    d.save()


def pool():
    d = new("blog-t01-pool", 1400, 640, "연결 비용과 풀 — 연결 수 = 백엔드 프로세스 수",
            "앱 풀이 연결을 미리 열어 두고 빌려 준다. PgBouncer 는 많은 클라이언트 연결을 적은 서버 연결로 모은다")
    d.card("app", 40, 120, 340, 150, "앱 (JVM)", "HikariCP 풀 — 연결을\n미리 열어 두고 빌려 준다\n(일반 개념)", bg=P["as_bg"], stroke=P["front"])
    d.card("pb", 500, 120, 340, 150, "PgBouncer (선택)", "별도 프로세스\ndefault_pool_size 20 (사용자/DB 쌍당)\nmax_client_conn 100", bg=P["bff_bg"], stroke=P["back"])
    d.card("pg", 960, 120, 400, 150, "PostgreSQL", "연결 1개 = 백엔드 프로세스 1개\nmax_connections 100 (기본, 시작 때만 변경)\nsuperuser_reserved_connections 3", bg=P["ok_bg"], stroke=P["green"])
    d.arrow([(380, 195), (500, 195)], P["front"], "클라이언트\n연결", start="app", end="pb")
    d.arrow([(840, 195), (960, 195)], P["back"], "서버\n연결", start="pb", end="pg")
    d.text(40, 306, "풀 모드 — 서버 연결을 클라이언트에 배정하는 기간 (PgBouncer, pool_mode)", 16, P["muted"], weight=700)
    modes = [("session  (기본값)", "클라이언트가 연결해 있는 동안 내내", "ok"),
             ("transaction", "트랜잭션 동안만\n지원 안 되는 기능이 생긴다", "warn"),
             ("statement", "가장 공격적 · transaction 과 같되\n여러 문장 트랜잭션을 금지", "bad")]
    for i, (t, b, k) in enumerate(modes):
        bg, st = kc(k)
        d.card(f"m{i}", 40 + i * 450, 340, 420, 100, t, b, bg=bg, stroke=st, title_size=16, body_size=14)
    d.card("tx", 40, 470, 1320, 130, "transaction 모드에서 지원되지 않는 기능 (PgBouncer 문서의 목록)",
           "SET / RESET · LISTEN · WITH HOLD CURSOR · SQL 레벨 PREPARE / DEALLOCATE\nPRESERVE / DELETE ROWS 임시 테이블 · LOAD · 세션 수준 advisory 락\n프로토콜 수준의 이름 있는 prepared statement 는 max_prepared_statements (기본 200) 로 PgBouncer 가 추적한다\n한 트랜잭션이 끝나면 서버 연결이 다른 클라이언트에게 가므로 세션 상태에 기대는 코드가 깨진다",
           bg=P["note_bg"], stroke=P["line"], title_size=16, body_size=14)
    d.save()


if __name__ == "__main__":
    for f in (journey, processes, memory, wal_commit, checkpoint, sync_commit, lock_layers, row_lock_where, pool):
        f()
    finish()
