#!/usr/bin/env python3
"""01.03 블로그판 03 그림. 실행: python3 -I docs/diagrams/draw_blog03.py (레슨 폴더에서)"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[4] / "tools"))
from diagram import Diagram, P, finish, timeline as _timeline  # noqa: E402

OUT = pathlib.Path(__file__).parent


def timeline(*a, **k):
    return _timeline(*a, out=OUT, **k)


def scene():
    timeline("blog03-scene", "같은 키가 동시에 INSERT 되면",
             "유니크 인덱스가 있는 테이블 — A 가 INSERT 하고 아직 커밋하지 않았다",
             [("A", "1  INSERT key = 'k5'", "아직 COMMIT 도 ROLLBACK 도 하지 않았다", None),
              ("B", "2  INSERT key = 'k5'", "같은 키 — 엔진은 무엇을 할까?", None),
              ("A", "3  COMMIT 또는 ROLLBACK", "A 는 둘 중 하나로 끝난다", None)],
             [(0, 1, "A 의 미커밋 행과\n같은 키")],
             "상대가 커밋할지 롤백할지 모르는 채로는, 위반인지 아닌지 판정할 수 없다.\n"
             "엔진이 이때 무엇을 하는지가 Q03 ~ Q05 의 주제다 — 규칙은 아래 접힌 칸에 있다.",
             "B 의 INSERT 는 어떻게 되나", vcolor="note")


def invariant():
    d = Diagram("blog03-invariant", 1360, 480, "유니크 인덱스가 지키는 것",
                "어떤 MVCC 스냅샷에도 같은 키를 가진 행이 둘 보이면 안 된다 (문서 64.5)", out=OUT)
    d.card("snap", 40, 100, 620, 150, "스냅샷 S1 · S2 · S3 …", "어느 스냅샷에서 봐도\n같은 키 'k5' 를 가진 행이 둘 보이면 안 된다",
           bg=P["ok_bg"], stroke=P["green"], title_size=17, body_size=15, title_color=P["green"])
    d.card("hard", 700, 100, 620, 150, "어려운 경우", "상대가 아직 커밋하지 않았다\n커밋할지 롤백할지 모르는 채로는 위반인지 판정할 수 없다",
           bg=P["todo_bg"], stroke=P["orange"], title_size=17, body_size=15)
    d.arrow([(660, 175), (700, 175)], P["muted"], "문제", label_size=11, start="snap", end="hard")
    d.card("q", 40, 300, 1280, 150, "그럼 엔진은 이때 무엇을 하나",
           "Q03 ~ Q05 의 주제다. 규칙은 이 글의 접힌 칸에 있다 — 예측을 적은 뒤 펼친다.",
           bg=P["note_bg"], stroke=P["line"], title_size=17, body_size=15)
    d.save()


def rules():
    d = Diagram("blog03-rules", 1360, 500, "문서 64.5 — 유니크 검사가 INSERT 때 확인하는 네 경우 (요약)",
                "예측을 끝낸 뒤 펼치는 그림이다 (Q03 · Q04 · Q05 의 답이 들어 있다)", out=OUT)
    cases = [("1  내 트랜잭션이 이미 지운 행", "충돌하는 유효한 행을 현재 트랜잭션이 지웠다면 괜찮다\n(UPDATE 가 키를 안 바꾸는 경우가 여기에 걸린다)", P["ok_bg"], P["green"]),
             ("2  아직 커밋 안 된 다른 트랜잭션이 넣은 행", "넣으려는 쪽은 그 트랜잭션이 끝나기를 기다린다\n롤백하면 충돌 없음 · 커밋하면(그 행을 다시 지우지 않았다면) 유니크 위반\n실제로는 끝나기를 기다린 뒤 가시성 검사를 통째로 다시 한다", P["todo_bg"], P["orange"]),
             ("3  지워지는 중인 유효한 행", "그 트랜잭션이 커밋 또는 중단될 때까지 기다린 뒤\n검사를 반복한다", P["todo_bg"], P["orange"]),
             ("4  위반을 보고하기 직전", "방금 넣은 행이 이미 \"커밋된 채 죽었는지\" 를 다시 확인한다\n(일반적으로는 안 일어나고 CREATE UNIQUE INDEX CONCURRENTLY 중에 생길 수 있다)", P["note_bg"], P["line"])]
    for i, (t, b, bg, st) in enumerate(cases):
        x, y = 40 + (i % 2) * 670, 100 + (i // 2) * 190
        d.card(f"c{i}", x, y, 640, 170, t, b, bg=bg, stroke=st, title_size=16, body_size=14)
    d.save()


def txid():
    d = Diagram("blog03-txid", 1400, 640, "기다림의 정체 — 행이 아니라 트랜잭션이 끝나기를 기다린다",
                "실측: psql 2026-10-13, PostgreSQL 16.14. 예측을 끝낸 뒤 펼치는 그림이다", out=OUT)
    d.card("a", 40, 110, 560, 130, "세션 A", "idem 에 'k2' INSERT, 커밋 전\npg_stat_activity: Timeout / PgSleep (커밋 전에 멈춰 있다)\n"
           "자기 트랜잭션 ID 에 ExclusiveLock (granted = t)", bg=P["as_bg"], stroke=P["front"], title_size=16, body_size=13)
    d.card("b", 800, 110, 560, 130, "세션 B", "같은 키 INSERT\npg_stat_activity: wait_event_type = Lock\nwait_event = transactionid",
           bg=P["todo_bg"], stroke=P["orange"], title_size=16, body_size=13)
    d.card("ta", 40, 330, 560, 100, "A 의 트랜잭션 ID", "ExclusiveLock — A 가 쥔다 (t)", bg=P["white"], stroke=P["front"], title_size=15)
    d.card("tb", 800, 330, 560, 100, "B 의 트랜잭션 ID", "ExclusiveLock — B 가 쥔다 (t)", bg=P["white"], stroke=P["back"], title_size=15)
    d.arrow([(320, 240), (320, 330)], P["front"], "A 가 자기 ID 에 건다", label_size=12, start="a", end="ta")
    d.arrow([(1080, 240), (1080, 330)], P["back"], "B 가 자기 ID 에 건다", label_size=12, start="b", end="tb")
    d.arrow([(1000, 240), (1000, 290), (480, 290), (480, 330)], P["red"], "ShareLock 요청 (granted = f)\nA 가 끝나기를 기다린다", label_at=(740, 290), label_size=12)
    d.card("v", 40, 470, 1320, 140, "모든 트랜잭션은 자기 트랜잭션 ID 에 ExclusiveLock 을 쥔다",
           "상대가 끝나기를 기다리는 쪽은 그 ID 에 ShareLock 을 요청하고, 상대가 끝나면 풀린다.\n"
           "locktype = transactionid — 행이 아니라 트랜잭션이 끝나기를 기다린다는 뜻이다.\n"
           "(락 모델은 소스 README src/backend/storage/lmgr/README 와 01.01 문서 04 의 행 락 대기와 같은 모양)",
           bg=P["note_bg"], stroke=P["line"], title_size=16, body_size=13)
    d.save()


def pool():
    d = Diagram("blog03-pool", 1400, 640, "같은 키의 재시도가 커넥션 풀을 고갈시키는 경로",
                "이 기다림은 커넥션을 쥔 채로 한다", out=OUT)
    d.card("first", 40, 100, 1320, 100, "선점한 트랜잭션 — 느린 외부 호출(결제 API) 동안 열려 있다",
           "커넥션 1개를 쥐고 있고, 아직 커밋하지 않았다", bg=P["as_bg"], stroke=P["front"], title_size=16, body_size=14)
    for i in range(4):
        d.pill(f"w{i}", 40 + i * 330, 260, 300, 60, f"같은 키의 재시도 {i + 1} — 커넥션 1개 쥔 채 대기", P["todo_bg"], P["orange"], size=13)
        d.arrow([(190 + i * 330, 200), (190 + i * 330, 260)], P["orange"], "같은 트랜잭션을\n기다린다", label_size=11)
    d.pill("pool", 40, 380, 1320, 56, "풀이 고갈된다 — 같은 키와 관계없는 요청까지 커넥션을 못 얻어 막힌다", P["bad_bg"], P["red"], size=16)
    d.arrow([(700, 320), (700, 380)], P["red"], "쌓인다", label_size=11)
    d.card("def", 40, 470, 1320, 140, "방어",
           "lock_timeout (기본값 0 = 꺼짐 — PostgreSQL 16 문서 20.11.1. 락 대기에는 기본 시간 상한이 없다)\n"
           "재시도 간격 · 상한\n키를 먼저 커밋하고 충돌 시 즉시 409 (문서 06)",
           bg=P["ok_bg"], stroke=P["green"], title_size=16, body_size=14, title_color=P["green"])
    d.save()


def mysql():
    d = Diagram("blog03-mysql", 1400, 500, "MySQL InnoDB 는 다르게 한다 — 공유 락과 교착",
                "MySQL 8.0 · 17.7.3 Locks Set by Different SQL Statements 의 세 세션 예", out=OUT)
    steps = [("1  INSERT", "삽입한 행에 배타 레코드 락을 건다", P["as_bg"], P["front"]),
             ("2  같은 행을 INSERT 한 세션들", "중복 키 에러가 나면\n중복된 인덱스 레코드에 공유 락을 건다", P["todo_bg"], P["orange"]),
             ("3  앞선 세션이 롤백하면", "대기 중이던 세션들이 공유 락을\n동시에 얻는다", P["todo_bg"], P["orange"]),
             ("4  서로 배타 락을 못 얻는다", "교착이 날 수 있다", P["bad_bg"], P["red"])]
    for i, (t, b, bg, st) in enumerate(steps):
        x = 40 + i * 335
        d.card(f"s{i}", x, 110, 300, 130, t, b, bg=bg, stroke=st, title_size=15, body_size=13, sw=3 if i == 3 else 2)
        if i:
            d.arrow([(x - 35, 175), (x, 175)], P["muted"], start=f"s{i - 1}", end=f"s{i}")
    d.card("pg", 40, 290, 1320, 110, "PostgreSQL 은 이 모양이 아니다",
           "PostgreSQL 의 방식은 접힌 칸(문서 64.5)이고 이 모양과 다르다\n"
           "(해석 — PostgreSQL 쪽에서 같은 상황의 교착이 안 나는지는 직접 돌려 보지 않았다)",
           bg=P["note_bg"], stroke=P["line"], title_size=16, body_size=14)
    d.save()


if __name__ == "__main__":
    for f in (scene, invariant, rules, txid, pool, mysql):
        f()
    finish()
