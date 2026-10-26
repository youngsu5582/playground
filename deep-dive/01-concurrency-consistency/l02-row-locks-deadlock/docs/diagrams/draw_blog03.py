#!/usr/bin/env python3
"""01.02 블로그판 03 그림. 실행: python3 -I docs/diagrams/draw_blog03.py (레슨 폴더에서)"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[4] / "tools"))
from diagram import Diagram, P, finish, timeline as _timeline  # noqa: E402

OUT = pathlib.Path(__file__).parent


def timeline(*a, **k):
    return _timeline(*a, out=OUT, **k)


def intro():
    timeline("blog03-intro", "도입: 기다림에는 기본 상한이 없다",
             "작업 행 9번을 두고 두 세션이 만난다",
             [("A", "1  UPDATE jobs SET status = 'running' WHERE id = 9", "커밋하지 않고 다른 일을 한다", None),
              ("B", "2  UPDATE jobs SET status = 'running' WHERE id = 9", "같은 행 — 기다린다", "bad"),
              ("A", "3  (아직 COMMIT 하지 않았다)", "1초 · 1분 · 1시간이 지나도 B 는 그대로", None)],
             [(0, 1, "A 의 행 락이\nB 를 세운다")],
             "데드락이 아니라면 락 대기는 무한정이다 (문서 13.3.4). lock_timeout 의 기본값도 0 = 꺼짐이다.\n"
             "한 세션의 지연이 풀 전체의 마비로 번질 수 있으니, 기다림에 상한을 두거나 아예 기다리지 않는 길이 필요하다.",
             "엔진은 알아서 포기시키지 않는다")


def three_ways():
    d = Diagram("blog03-three-ways", 1400, 520, "기다리고 싶지 않을 때의 선택지 셋",
                "못 잡았을 때 무엇이 달라지나", out=OUT)
    cols = [("NOWAIT", "즉시 에러", "\"지금 안 되면 안 한다\"\n사용자 요청 경로에서 즉시 응답", "SELECT … FOR UPDATE NOWAIT", P["bad_bg"], P["red"]),
            ("lock_timeout", "상한만큼 기다리다 에러", "안전망\n세션 · 트랜잭션에 거는 상한", "SET lock_timeout = '1s'", P["todo_bg"], P["orange"]),
            ("SKIP LOCKED", "에러 없음, 그 행을 결과에서 뺀다", "\"아무 행이나 하나면 된다\"\n큐 소비자", "SELECT … FOR UPDATE SKIP LOCKED", P["ok_bg"], P["green"])]
    for i, (t, r, use, ex, bg, st) in enumerate(cols):
        x = 40 + i * 450
        d.card(f"c{i}", x, 110, 420, 330, t, None, bg=bg, stroke=st, title_size=20)
        d.text(x + 16, 160, "못 잡으면", 13, P["muted"])
        d.text(x + 16, 182, r, 15, P["ink"])
        d.text(x + 16, 236, "무엇을 하는 방법", 13, P["muted"])
        d.text(x + 16, 258, use, 15, P["ink"])
        d.text(x + 16, 350, ex, 13, P["ink"], mono=True)
    d.text(40, 470, "NOWAIT · SKIP LOCKED 는 행 락에만 적용된다. 필요한 ROW SHARE 테이블 락은 평소처럼 잡는다 (SELECT 문서)", 14, P["muted"])
    d.save()


def timeouts():
    d = Diagram("blog03-timeouts", 1400, 560, "lock_timeout 과 statement_timeout 은 재는 구간이 다르다",
                "한 문장이 서버에 도착해서 끝날 때까지", out=OUT)
    d.rect("w", 140, 220, 440, 70, P["todo_bg"], P["orange"])
    d.text(360, 255, "락을 기다리는 구간", 15, P["ink"], align="center", valign="middle")
    d.rect("x", 580, 220, 640, 70, P["as_bg"], P["front"])
    d.text(900, 255, "실행 구간", 15, P["ink"], align="center", valign="middle")
    d.arrow([(140, 330), (1230, 330)], P["muted"], "시간", label_at=(1190, 330))
    d.text(140, 345, "명령이 서버에 도착", 13, P["muted"])
    d.text(1220, 345, "끝", 13, P["muted"], align="right")
    d.arrow([(140, 190), (580, 190)], P["red"], "lock_timeout — 락 획득 시도마다, 대기 중에만 잰다", both=True, label_size=14)
    d.arrow([(140, 150), (1220, 150)], P["green"], "statement_timeout — 도착부터 끝까지 전부 잰다", both=True, label_size=14)
    d.card("n1", 40, 390, 640, 140, "lock_timeout (기본 0 = 꺼짐, 단위 없으면 ms)",
           "DB 객체의 락을 얻으려 기다리는 시간이 넘으면 문장을 중단한다\n명시적 락과 암묵적 락 모두에 적용된다",
           bg=P["note_bg"], stroke=P["line"], title_size=15, body_size=14)
    d.card("n2", 720, 390, 640, 140, "함께 쓸 때 (문서 20.11)",
           "statement_timeout 이 0 이 아닐 때 lock_timeout 을 같거나 큰 값으로 두면\n의미가 없다 — 문장 타임아웃이 먼저 걸린다\n둘 다 postgresql.conf 에 두는 것은 비권장 (모든 세션에 적용)",
           bg=P["note_bg"], stroke=P["line"], title_size=15, body_size=14)
    d.save()


def skip_locked():
    d = Diagram("blog03-skip-locked", 1400, 560, "SKIP LOCKED — 잡힌 행은 건너뛰고 다음 행을 집는다",
                "작업 큐 jobs (pending 행 5개), 워커 셋이 같은 쿼리를 동시에 날린다", out=OUT)
    d.text(40, 100, "SELECT id FROM jobs WHERE status = 'pending' ORDER BY id LIMIT 1 FOR UPDATE SKIP LOCKED", 15, P["ink"], mono=True)
    rows = [("31", "잠겨 있다\n(워커 1 이 집음)", P["bad_bg"], P["red"]),
            ("32", "pending", P["white"], P["line"]),
            ("33", "pending", P["white"], P["line"]),
            ("34", "pending", P["white"], P["line"]),
            ("35", "pending", P["white"], P["line"])]
    for i, (n, t, bg, st) in enumerate(rows):
        d.pill(f"r{i}", 40 + i * 260, 150, 240, 80, f"id {n}\n{t}", bg, st, size=15)
    ws = [("워커 2", "31 은 건너뛰고\n32 를 집는다", 1), ("워커 3", "31 · 32 를 건너뛰고\n33 을 집는다", 2)]
    for j, (w, t, target) in enumerate(ws):
        x = 300 + j * 520
        d.card(f"w{j}", x, 340, 400, 110, w, t, bg=P["as_bg"], stroke=P["front"], title_size=16, body_size=14)
        d.arrow([d.anchor(f"w{j}", "n"), d.anchor(f"r{target}", "s")], P["green"], "집는다", start=f"w{j}", end=f"r{target}")
    d.card("n", 40, 480, 1320, 60, "잡힌 행을 후보에서 빼므로 워커들이 서로 줄을 서지 않는다 — 대가는 문서가 경고한 \"일관되지 않은 뷰\"",
           None, bg=P["note_bg"], stroke=P["line"], title_size=15)
    d.save()


def queue_shape():
    d = Diagram("blog03-queue-shape", 1400, 560, "작업 큐의 정석 — 락은 커밋까지 간다",
                "집기(SELECT) · 표시(UPDATE) · 커밋이 한 트랜잭션이어야 한다", out=OUT)
    d.pill("b1", 40, 130, 330, 70, "BEGIN", P["note_bg"], P["line"], size=16)
    d.pill("b2", 380, 130, 330, 70, "SELECT … LIMIT 1\nFOR UPDATE SKIP LOCKED", P["todo_bg"], P["orange"], size=14)
    d.pill("b3", 720, 130, 330, 70, "UPDATE jobs\nSET status = 'running'", P["as_bg"], P["front"], size=14)
    d.pill("b4", 1060, 130, 300, 70, "COMMIT", P["note_bg"], P["line"], size=16)
    d.arrow([(380, 250), (1360, 250)], P["red"], "행 락을 쥐고 있는 구간", both=True, label_size=14)
    d.card("long", 40, 300, 640, 190, "그 안에서 외부 호출 같은 긴 일을 하면",
           "락이 그만큼 길어진다\n\n집고 → 커밋 → 처리 → 결과 기록으로 나누는 설계는\n02.03 outbox 로 이어진다",
           bg=P["bad_bg"], stroke=P["red"], title_size=16, body_size=14)
    d.card("lim", 720, 300, 640, 190, "LIMIT 과 락 (SELECT 문서)",
           "LIMIT 은 요구한 수만큼 행이 반환된 시점에 잠그기를 멈춘다\n(단 OFFSET 으로 건너뛴 행은 잠긴다)\n→ LIMIT 1 … FOR UPDATE 는 한 행만 잠근다",
           bg=P["note_bg"], stroke=P["line"], title_size=16, body_size=14)
    d.save()


def worker_dies():
    d = Diagram("blog03-worker-dies", 1400, 600, "워커가 도중에 죽으면 — 트랜잭션을 어떻게 나눴느냐에 달렸다",
                "(해석 · 설계 판단 — 되돌리는 방법은 이 레슨의 범위 밖이고 문서로 확인한 것도 없다)", out=OUT)
    d.text(40, 104, "집기 · 처리 · 완료 기록이 한 트랜잭션", 17, P["green"], weight=700)
    d.pill("a1", 40, 140, 300, 80, "집고 → 처리하다\n워커가 죽는다", P["note_bg"], P["line"], size=15)
    d.pill("a2", 400, 140, 300, 80, "트랜잭션 롤백\n락이 풀린다", P["as_bg"], P["front"], size=15)
    d.pill("a3", 760, 140, 280, 80, "작업은 pending 으로\n돌아가 다시 집힌다", P["ok_bg"], P["green"], size=15)
    d.arrow([(340, 180), (400, 180)], P["muted"])
    d.arrow([(700, 180), (760, 180)], P["muted"])
    d.text(40, 284, "집기 → 커밋 → 처리로 나눔", 17, P["red"], weight=700)
    d.pill("b1", 40, 320, 300, 80, "선점(UPDATE) 커밋 후\n처리하다 워커가 죽는다", P["note_bg"], P["line"], size=15)
    d.pill("b2", 400, 320, 300, 80, "커밋은 이미 끝났다\n롤백되지 않는다", P["as_bg"], P["front"], size=15)
    d.pill("b3", 760, 320, 280, 80, "작업이 running 으로\n남는다 — 안 집힌다", P["bad_bg"], P["red"], size=15)
    d.arrow([(340, 360), (400, 360)], P["muted"])
    d.arrow([(700, 360), (760, 360)], P["muted"])
    d.card("fix", 1080, 320, 280, 80, "재집기 설계가 따로 필요", None, bg=P["todo_bg"], stroke=P["orange"], title_size=14)
    d.card("n", 40, 450, 1320, 110, "그래서 외부 호출을 낀 처리는 트랜잭션에 넣지 않는 게 정석이다",
           "그러면 상태 표시와 재집기(lease 만료 같은 설계)가 필수가 된다. 이 레슨은 재집기를 구현하지 않는다",
           bg=P["note_bg"], stroke=P["line"], title_size=15, body_size=14)
    d.save()


def savepoint():
    timeline("blog03-savepoint", "실패한 뒤의 트랜잭션 — SAVEPOINT 로 문장 단위 복구",
             "NOWAIT 나 lock_timeout 이 실패하면 트랜잭션 블록 전체가 중단 상태가 된다. SAVEPOINT 가 있으면 거기까지 돌아갈 수 있다",
             [("B", "1  BEGIN; UPDATE jobs … WHERE id = 1", "행 1 의 락을 쥐고 열어 둔다", None),
              ("A", "2  BEGIN; SAVEPOINT s;", "문장 단위 복구 지점을 표시", None),
              ("A", "3  SELECT … WHERE id = 1 FOR UPDATE NOWAIT", "잠글 수 없다 → 에러, 트랜잭션은 중단 상태", "bad"),
              ("A", "4  ROLLBACK TO s", "트랜잭션이 다시 정상", "ok"),
              ("A", "5  SELECT id FROM jobs WHERE id = 2 FOR UPDATE", "계속 가능", "ok")],
             [(0, 2, "B 의 락 때문에\n실패한다")],
             "SAVEPOINT 가 없으면 이후 문장은 current transaction is aborted 로 거절되고 ROLLBACK 만 의미가 있다.\n"
             "세이브포인트 뒤에 얻은 락은 그 세이브포인트로 ROLLBACK 하면 즉시 풀린다 (문서 13.3.1).",
             "에러가 문장이 아니라 트랜잭션을 죽인다", vcolor="note")


if __name__ == "__main__":
    for f in (intro, three_ways, timeouts, skip_locked, queue_shape, worker_dies, savepoint):
        f()
    finish()
