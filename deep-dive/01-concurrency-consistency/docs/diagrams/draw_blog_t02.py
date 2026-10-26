#!/usr/bin/env python3
"""01 트랙 블로그판 02 (장애 대응 쿼리) 그림. 실행: python3 -I docs/diagrams/draw_blog_t02.py (트랙 폴더에서)"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from blog_common import Diagram, P, finish, tw, kc, vchain, hchain, sequence, matrix, new, card_h, ARROW  # noqa: E402


def order():
    d = hchain("blog-t02-order", "DB 가 느려졌다 — 먼저 보는 순서 (해석: 일반 운영 절차)",
               "증상은 대개 \"앱 응답 지연 + 커넥션 풀 고갈\" 이다. 원인이 락 · 오래 열린 트랜잭션 · 데드락 · 느린 쿼리 중 무엇인지 3분 안에 가른다",
               [("1  연결", "수 · 상태 분포\n쿼리 5", "a"),
                ("2  막힘", "막힌 세션 → 루트\n쿼리 1 · 2", "bad"),
                ("3  느린 쿼리", "오래 도는 active\n누적 느린 쿼리\n쿼리 8 · 9", "warn"),
                ("4  오래 열린 것", "트랜잭션 · 죽은 튜플\n쿼리 4 · 7", "b"),
                ("5  디스크", "쿼리 10", "ok")],
               labels=("", "막힘\n없으면", "점진적\n이면", ""), gap=70, h=130, top=120, bs=14)
    d.save()


def lock_chain():
    d = new("blog-t02-lock-chain", 1400, 520, "blocked_by 는 사슬로 나온다 — 루트를 찾아라",
            "(실측: psql 2026-10-13) 세션 A 가 UPDATE 후 커밋 안 함, B · C 가 같은 행 UPDATE")
    d.card("A", 40, 130, 350, 190, "A  pid 158  (루트)",
           "state = idle in transaction\nupdate obs set v=1 where id=1;\n자기는 안 막혔고 남을 막는다\n(blocking_count = 1)",
           bg=P["bad_bg"], stroke=P["red"], title_size=16, body_size=14)
    d.card("B", 510, 130, 350, 190, "B  pid 165",
           "state = active\nwait_event_type = Lock\nwait_event = transactionid\nblocked_by = {158}\nupdate obs set v=2 where id=1;",
           bg=P["todo_bg"], stroke=P["orange"], title_size=16, body_size=14)
    d.card("C", 980, 130, 350, 190, "C  pid 172",
           "state = active\nwait_event_type = Lock\nwait_event = tuple\nblocked_by = {165}\nupdate obs set v=3 where id=1;",
           bg=P["todo_bg"], stroke=P["orange"], title_size=16, body_size=14)
    d.arrow([(510, 225), (390, 225)], P["orange"], "A 의 ID 를\n기다린다", start="B", end="A", label_at=(450, 195))
    d.arrow([(980, 225), (860, 225)], P["orange"], "B 에게 막혀\ntuple 락 대기", start="C", end="B", label_at=(920, 195))
    d.card("rd", 40, 360, 1300, 130, "읽는 법",
           "C 는 A 가 아니라 B 에게 막혀 있다 — 같은 행 UPDATE 대기일 때 blocked_by 는 C → B → A 의 사슬이고 맨 끝이 루트다\n(같은 키 유니크 INSERT 대기는 전부 삽입자 하나를 가리킨다 — 실측: psql 2026-10-13, 01.03 문서 08)\n막힌 쪽(B · C)을 죽이면 줄만 바뀐다 — 루트(A)를 찾는다 (쿼리 2)",
           bg=P["note_bg"], stroke=P["line"], title_size=16, body_size=14)
    d.save()


def idle_in_tx():
    d = new("blog-t02-idle-in-tx", 1400, 560, "idle in transaction 이 쥐고 있는 것",
            "쿼리는 안 도는데 트랜잭션은 열려 있다 — 앱이 외부 호출 · 사용자 대기 중이거나 커밋을 빼먹은 상태")
    d.card("c", 40, 190, 380, 160, "idle in transaction 세션",
           "xact_age 가 크다\nstate = idle in transaction\n(aborted) 는 에러 뒤 롤백을\n안 한 앱 버그의 전형",
           bg=P["bad_bg"], stroke=P["red"], title_size=16, body_size=14)
    items = [("락", "남의 UPDATE 를 줄 세운다\n(쿼리 1 · 2 의 루트 후보)", "warn", 120),
             ("연결 슬롯", "풀 · max_connections 를 차지한다\n(쿼리 5 의 idle_in_tx)", "a", 270),
             ("VACUUM horizon", "backend_xmin 이 오래되면 죽은 튜플을\n치우는 기준선을 붙잡는다 (쿼리 4 · 7)", "b", 420)]
    for i, (t, b, k, _y) in enumerate(items):
        bg, st = kc(k)
        d.card(f"i{i}", 560, items[i][3] - 20, 780, 110, t, b, bg=bg, stroke=st, title_size=16, body_size=14)
        d.arrow([(420, 270), (490, 270), (490, items[i][3] + 35), (560, items[i][3] + 35)], ARROW[k], None, start="c", end=f"i{i}")
    d.text(560, 540 - 24, "(실측) 쿼리 하나가 도는 중인 세션(274)도 backend_xmin 을 갖는다 — 읽기 전용이어도 스냅샷이 열려 있는 동안 horizon 을 붙잡는다", 14, P["muted"])
    d.save()


def cancel_terminate():
    d = matrix("blog-t02-cancel-terminate", "취소와 종료 — 실측한 세 장면",
               "(실측: psql 2026-10-13) A = idle in transaction 루트, B = A 를 기다리는 UPDATE, C = B 를 기다리는 UPDATE",
               ["무슨 일이 일어났나", "그 세션의 상태", "기다리던 쪽은"],
               [("pg_cancel_backend(A)", [("true 를 돌려줬다", "w"), ("A 는 그대로\nidle in transaction", "bad"), ("도는 쿼리가 없어서\n취소할 것이 없다", "note")]),
                ("pg_cancel_backend(B)\nB 는 락 대기 중", [("B 의 UPDATE 가 ERROR:\ncanceling statement due to user request", "w"),
                                                         ("B 는 idle in transaction\n(aborted) — 연결은 살아 있다", "warn"),
                                                         ("C 는 한 칸 앞으로\n(여전히 A 를 기다림)", "note")]),
                ("pg_terminate_backend(A)", [("FATAL: terminating connection\ndue to administrator command", "w"),
                                             ("A 가 사라지고\n그 트랜잭션은 롤백", "ok"),
                                             ("기다리던 C 가\n바로 락을 얻었다", "ok")])],
               w=1400, first_w=260, row_h=96, size=14,
               notes="고르는 기준 (해석): 쿼리가 도는 중이면 취소로 충분하다. 트랜잭션만 열어 두고 놀고 있으면 종료밖에 없다.")
    d.save()


def deadlock():
    d = new("blog-t02-deadlock", 1400, 520, "데드락 — 서로의 트랜잭션 ID 를 기다린다",
            "(실측: psql 2026-10-13 — 반대 순서 UPDATE 두 세션) 서버 로그의 deadlock detected DETAIL")
    d.card("p1", 40, 130, 520, 150, "Process 207",
           "update obs set v=20 where id=1;\n기다리는 것: ShareLock on transaction 752\n막은 쪽: process 208",
           bg=P["as_bg"], stroke=P["front"], title_size=16, body_size=14)
    d.card("p2", 840, 130, 520, 150, "Process 208",
           "update obs set v=10 where id=2;\n기다리는 것: ShareLock on transaction 751\n막은 쪽: process 207",
           bg=P["bff_bg"], stroke=P["back"], title_size=16, body_size=14)
    d.arrow([(560, 170), (840, 170)], P["red"], "207 은 208 에게 막혔다", start="p1", end="p2", label_at=(700, 150))
    d.arrow([(840, 245), (560, 245)], P["red"], "208 은 207 에게 막혔다", start="p2", end="p1", label_at=(700, 268))
    d.card("how", 40, 330, 1320, 150, "읽는 법",
           "pg_stat_database.deadlocks 는 누적 값 — 두 시점의 차이로 읽는다 (이 실측: deadlocks = 1)\n카운터는 \"몇 번\" 만 알려 준다. 어떤 쿼리 두 개였는지는 서버 로그의 deadlock detected 에 나온다\n어느 쪽이 희생되는지는 예측해서 기대면 안 된다 (문서 13.3) · 앱이 받는 SQLSTATE 는 40P01\n조치: 락을 잡는 순서 통일(예방) + 재시도",
           bg=P["note_bg"], stroke=P["line"], title_size=16, body_size=14)
    d.save()


def dead_tuples():
    d = new("blog-t02-dead-tuples", 1400, 600, "n_dead_tup 이 크다 — autovacuum 은 돌고 있나",
            "(쿼리 7 의 해석 순서) 비율만 보지 말고 절대량과 임계를 같이 본다 (해석)")
    d.card("q", 40, 120, 440, 110, "n_dead_tup 이 크다", "last_autovacuum 을 본다", bg=P["as_bg"], stroke=P["front"], title_size=17, body_size=14)
    d.card("r", 620, 120, 740, 150, "1  last_autovacuum 이 최근이다",
           "autovacuum 은 돌지만 못 치우고 있다\n= horizon 을 붙잡는 트랜잭션이 있다\n→ 쿼리 4 의 backend_xmin 을 본다", bg=P["bad_bg"], stroke=P["red"], title_size=16, body_size=14)
    d.card("o", 620, 320, 740, 150, "2  last_autovacuum 이 오래됐다",
           "임계가 너무 크거나(큰 테이블) 못 따라가는 중\nautovacuum 은 threshold(50) + scale_factor(0.2) × 튜플 수 를 넘어야 돈다 (01.01 문서 06)\n확인 · 조치: 01.01 문서 06 (VACUUM (VERBOSE) · age(datfrozenxid))", bg=P["todo_bg"], stroke=P["orange"], title_size=16, body_size=14)
    d.arrow([(480, 175), (620, 175)], P["red"], "최근", start="q", end="r")
    d.arrow([(260, 230), (260, 395), (620, 395)], P["orange"], "오래됨", start="q", end="o", label_at=(330, 395))
    d.card("m", 40, 510, 1320, 70, "실측 예: obs — n_live_tup 6 · n_dead_tup 17 · dead_pct 73.9 · last_autovacuum 비어 있음 · autovacuum_count 0",
           "비율은 높지만 임계(50 + 0.2 × 튜플 수) 아래라 아직 안 돌았다", bg=P["note_bg"], stroke=P["line"], title_size=14, body_size=14)
    d.save()


def disk():
    d = new("blog-t02-disk", 1400, 560, "디스크가 찬다 — 무엇이 큰가 (쿼리 10)",
            "원인별 읽기는 해석이고, 문서 근거는 표시한 것만")
    d.card("root", 40, 200, 280, 100, "디스크가 찬다", "쿼리 10 의 네 쿼리", bg=P["as_bg"], stroke=P["front"], title_size=17, body_size=14)
    cases = [("테이블 · 인덱스가 크다", "bloat 인지 정상 성장인지 쿼리 7 · 4 (horizon 을 붙잡는 트랜잭션)\n일반 VACUUM 은 공간을 OS 에 돌려주지 않는다 (01.01 문서 06)", "warn", 110),
             ("WAL 이 크다", "슬롯의 active = false · wal_status = extended 이면 슬롯이 WAL 을 붙잡고 있다\nmax_wal_size 는 소프트 한도 (부하 · 실패하는 archive_command · 큰 wal_keep_size 때 넘을 수 있음)", "bad", 260),
             ("그 밖 (로그 · 임시 파일 등)", "이 문서에서 확인하지 못했다", "note", 410)]
    for i, (t, b, k, _y) in enumerate(cases):
        bg, st = kc(k)
        d.card(f"k{i}", 440, cases[i][3], 920, 120, t, b, bg=bg, stroke=st, title_size=16, body_size=14)
        d.arrow([(320, 250), (380, 250), (380, cases[i][3] + 60), (440, cases[i][3] + 60)], ARROW[k], None, start="root", end=f"k{i}", dashed=(k == "note"))
    d.save()


def statements():
    d = hchain("blog-t02-statements", "pg_stat_statements 는 확장이다 — 세 단계가 모두 필요하다",
               "(실측: psql 2026-10-13) preload 없이 CREATE EXTENSION 만 하면 조회 때 에러가 난다",
               [("1  postgresql.conf", "shared_preload_libraries =\n'pg_stat_statements'", "a"),
                ("2  서버 재시작", "추가 공유 메모리가\n필요하므로", "warn"),
                ("3  CREATE EXTENSION", "쓸 DB 에서\nCREATE EXTENSION\npg_stat_statements;", "ok")],
               labels=("", ""), w=1400, gap=80, h=140, top=120, extra=110)
    d.card("err", 40, 290, 1320, 100, "preload 없이 조회하면 (01.01 컨테이너 실측)",
           "ERROR: pg_stat_statements must be loaded via shared_preload_libraries\n확장은 pg_available_extensions 에 1.10 으로 있었다 — 설치 가능하지만 preload 가 별개다",
           bg=P["bad_bg"], stroke=P["red"], title_size=15, body_size=14)
    d.save()


if __name__ == "__main__":
    for f in (order, lock_chain, idle_in_tx, cancel_terminate, deadlock, dead_tuples, disk, statements):
        f()
    finish()
