#!/usr/bin/env python3
"""01.03 블로그판 04 그림. 실행: python3 -I docs/diagrams/draw_blog04.py (레슨 폴더에서)"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[4] / "tools"))
from diagram import Diagram, P, finish, timeline as _timeline  # noqa: E402

OUT = pathlib.Path(__file__).parent


def timeline(*a, **k):
    return _timeline(*a, out=OUT, **k)


def clauses():
    d = Diagram("blog04-clauses", 1360, 560, "ON CONFLICT — 부딪혔을 때 하는 일을 한 문장에 적는다",
                "INSERT 를 하다 유니크 위반이 나는 대신, 미리 정해 둔 대체 동작을 한다", out=OUT)
    d.card("sql", 40, 100, 1280, 100, "INSERT INTO idempotency_keys (key, request_hash, status)",
           "VALUES ('pay-1', 'h1', 'IN_PROGRESS')\nON CONFLICT (key) DO NOTHING   |   DO UPDATE SET …",
           bg=P["note_bg"], stroke=P["line"], title_size=15, body_size=14, mono_body=True)
    d.card("dn", 40, 250, 620, 170, "DO NOTHING", "충돌했을 때: 삽입하지 않고 넘어간다\n\n용도: \"내가 선점했나\" 판정\nconflict_target 을 생략할 수 있다",
           bg=P["as_bg"], stroke=P["front"], title_size=18, body_size=15)
    d.card("du", 700, 250, 620, 170, "DO UPDATE SET …", "충돌했을 때: 충돌한 기존 행을 갱신한다\n\n용도: 카운터 올리기 · 상태 재선점 · upsert\nconflict_target 을 반드시 적어야 한다",
           bg=P["bff_bg"], stroke=P["back"], title_size=18, body_size=15)
    d.arrow([(350, 200), (350, 250)], P["muted"], start="sql", end="dn")
    d.arrow([(1010, 200), (1010, 250)], P["muted"], start="sql", end="du")
    d.card("note", 40, 450, 1280, 90, "중재자(arbiter)로 쓸 수 있는 것은 NOT DEFERRABLE 제약과 유니크 인덱스뿐이다",
           "conflict_target 에 적은 컬럼에 유니크 제약이 없으면 에러가 난다 (실측: psql 2026-10-13)",
           bg=P["todo_bg"], stroke=P["orange"], title_size=15, body_size=14)
    d.save()


def rc_semantics():
    d = Diagram("blog04-rc", 1360, 580, "READ COMMITTED 의 ON CONFLICT 는 인덱스 수준에서 충돌을 본다",
                "문장 시작 시점의 스냅샷에 안 보이는, 남이 방금 커밋한 행과 부딪혀도 충돌을 인식하고 처리한다 (문서 13.2.1)", out=OUT)
    d.card("snap", 40, 100, 620, 130, "INSERT 문장의 스냅샷", "문장이 시작될 때 보이던 것만 본다\n남이 그 뒤에 커밋한 행은 \"보이지 않는다\"",
           bg=P["note_bg"], stroke=P["muted"], title_size=16, body_size=14)
    d.card("idx", 700, 100, 620, 130, "유니크 인덱스", "같은 키의 항목이 이미 있다\n스냅샷과 무관하게 인덱스는 그것을 안다",
           bg=P["ok_bg"], stroke=P["green"], title_size=16, body_size=14)
    d.card("sel", 40, 290, 620, 130, "확인 후 INSERT (문서 02)", "SELECT 는 스냅샷만 본다\n그래서 남의 행을 못 보고 틈이 생겼다",
           bg=P["bad_bg"], stroke=P["red"], title_size=16, body_size=14, title_color=P["red"])
    d.card("oc", 700, 290, 620, 130, "ON CONFLICT", "충돌을 인덱스 수준에서 인식하고 처리한다\nDO UPDATE: 그 행에 UPDATE 를 적용한다\n"
           "DO NOTHING: 삽입이 진행되지 않을 수 있다",
           bg=P["ok_bg"], stroke=P["green"], title_size=16, body_size=14, title_color=P["green"])
    d.arrow([(350, 230), (350, 290)], P["muted"], "여기까지만 본다", label_size=12, start="snap", end="sel")
    d.arrow([(1010, 230), (1010, 290)], P["green"], "여기서 본다", label_size=12, start="idx", end="oc")
    d.card("v", 40, 450, 1280, 100, "확인 후 INSERT 가 못 보는 것을 이 문장은 인덱스 수준에서 본다",
           "이 보장은 문서 13.2.1 이 READ COMMITTED 에서의 동작으로 서술한다 — 다른 격리수준은 다음 그림",
           bg=P["note_bg"], stroke=P["line"], title_size=16, body_size=14)
    d.save()


def claim_fold():
    d = Diagram("blog04-claim", 1360, 460, "영향 행 수로 선점을 판정한다 — claim",
                "DO NOTHING + 영향 행 수. RETURNING 으로도 같은 판정이 된다 (행이 돌아오면 선점)", out=OUT)
    d.pill("q", 40, 100, 1280, 54, "INSERT … ON CONFLICT (key) DO NOTHING  →  영향 행 수는?", P["note_bg"], P["line"], size=16)
    d.card("one", 40, 220, 620, 140, "1행", "내가 키를 넣었다 = 선점 성공\n다음: 처리한다", bg=P["ok_bg"], stroke=P["green"], title_size=18, body_size=15, title_color=P["green"])
    d.card("zero", 700, 220, 620, 140, "0행", "이미 있다 = 선점 실패\n다음: 저장된 상태를 읽어 재생 · 거절 (문서 06)", bg=P["as_bg"], stroke=P["front"], title_size=18, body_size=15)
    d.arrow([(350, 154), (350, 220)], P["green"], "새 키", label_size=12, start="q", end="one")
    d.arrow([(1010, 154), (1010, 220)], P["front"], "이미 있던 키", label_size=12, start="q", end="zero")
    d.text(40, 400, "이 레슨의 claim = INSERT … ON CONFLICT DO NOTHING 의 영향 행 수가 1 인지로 판정", 14, P["muted"])
    d.save()


def isolation():
    d = Diagram("blog04-isolation", 1360, 600, "격리수준별 ON CONFLICT — 직접 돌려 본 결과",
                "세션 B 가 BEGIN ISOLATION LEVEL … ; SELECT 1; 로 스냅샷을 먼저 잡고, 그 뒤 A 가 같은 키를 커밋한 상태에서 B 가 INSERT (실측: psql 2026-10-13)", out=OUT)
    d.pill("h1", 40, 110, 260, 48, "B 의 격리수준", P["note_bg"], P["line"], size=14)
    d.pill("h2", 310, 110, 480, 48, "문장", P["note_bg"], P["line"], size=14)
    d.pill("h3", 800, 110, 520, 48, "결과", P["note_bg"], P["line"], size=14)
    rows = [("REPEATABLE READ", "ON CONFLICT DO NOTHING", "40001  could not serialize access due to concurrent update", "bad"),
            ("REPEATABLE READ", "ON CONFLICT DO UPDATE", "같은 40001", "bad"),
            ("REPEATABLE READ", "ON CONFLICT 없는 INSERT", "23505 (40001 이 아니다)", "mix"),
            ("SERIALIZABLE", "ON CONFLICT DO NOTHING", "같은 40001", "bad"),
            ("REPEATABLE READ", "스냅샷 이전에 커밋된 키에 DO NOTHING", "에러 없이 넘어간다 (영향 행 수는 Q06 칸)", "ok")]
    for i, (a, b, c, k) in enumerate(rows):
        y = 170 + i * 66
        d.pill(f"a{i}", 40, y, 260, 56, a, P["as_bg"], P["front"], size=14)
        d.pill(f"b{i}", 310, y, 480, 56, b, P["white"], P["line"], size=14)
        bg, st = {"bad": (P["bad_bg"], P["red"]), "mix": (P["todo_bg"], P["orange"]), "ok": (P["ok_bg"], P["green"])}[k]
        d.pill(f"c{i}", 800, y, 520, 56, c, bg, st, size=13)
    d.card("v", 40, 520, 1280, 56, "이 레슨의 멱등 키 선점은 READ COMMITTED 가 전제다 — RR/SERIALIZABLE 로 돌리면 재시도 루프가 필요하다 (01.01 문서 05)",
           None, bg=P["note_bg"], stroke=P["line"], title_size=14)
    d.save()


def cte_trap():
    timeline("blog04-cte-trap", "한 문장 CTE 의 함정 — 동시 요청에서 빈 결과가 나온다",
             "INSERT … ON CONFLICT DO NOTHING RETURNING 을 WITH 로 감싸고, 같은 문장 안의 SELECT 로 기존 행을 읽으려 한다",
             [("A", "1  INSERT idem(key) VALUES ('k2')", "커밋 전", None),
              ("B", "2  WITH ins AS (INSERT … DO NOTHING …) SELECT …", "문장이 시작된다 — 이 시점이 문장의 스냅샷", None),
              ("A", "3  COMMIT", "k2 가 커밋된다", None),
              ("B", "4  같은 문장의 SELECT 가 k2 를 읽는다", "문장 시작 스냅샷으로 읽는다 → 0행 반환", "bad")],
             [(2, 3, "A 의 커밋이 B 의\n스냅샷에 없다")],
             "B 는 A 의 커밋을 기다렸다가 DO NOTHING 에 걸리는데, 같은 문장 안의 SELECT 는 문장 시작 스냅샷으로 읽으므로 A 의 행을 못 본다.\n"
             "그래서 이 레슨은 INSERT 와 SELECT 를 별도 문장으로 나눈다 — 다음 문장은 새 스냅샷을 잡아 커밋된 행을 본다.",
             "CTE 는 동시 요청 아래에서 빈 결과를 돌려줄 수 있다")


def do_update_where():
    d = Diagram("blog04-reclaim", 1360, 600, "DO UPDATE … WHERE — 조건부 재선점",
                "실패 상태의 키만 다시 선점하는 예 (실측: psql)", out=OUT)
    d.card("sql", 40, 100, 1280, 150, "INSERT INTO idempotency_keys(key, request_hash, status) VALUES ('p2','h1','IN_PROGRESS')",
           "ON CONFLICT (key) DO UPDATE SET status = 'IN_PROGRESS'\nWHERE idempotency_keys.status = 'FAILED' AND idempotency_keys.request_hash = EXCLUDED.request_hash\nRETURNING status;",
           bg=P["note_bg"], stroke=P["line"], title_size=14, body_size=14, mono_body=True)
    d.card("f", 40, 320, 620, 120, "기존 행이 FAILED", "WHERE 가 참 → 갱신하고 1행을 돌려준다\n내가 재선점했다", bg=P["ok_bg"], stroke=P["green"], title_size=17, body_size=15, title_color=P["green"])
    d.card("i", 700, 320, 620, 120, "기존 행이 IN_PROGRESS", "WHERE 가 거짓 → 0행\n행이 잠기기만 하고 RETURNING 에 나오지 않는다", bg=P["todo_bg"], stroke=P["orange"], title_size=17, body_size=15)
    d.arrow([(350, 250), (350, 320)], P["green"], "FAILED", label_size=12, start="sql", end="f")
    d.arrow([(1010, 250), (1010, 320)], P["orange"], "IN_PROGRESS", label_size=12, start="sql", end="i")
    d.card("v", 40, 470, 1280, 100, "영향 행 수와 RETURNING 모두 \"내가 처리한 것이 아님\" 으로 읽는다",
           "DO UPDATE … WHERE 가 거짓일 때 행은 잠기기만 하고 갱신되지 않는다 (INSERT 문서)",
           bg=P["note_bg"], stroke=P["line"], title_size=16, body_size=14)
    d.save()


def batch_dup():
    d = Diagram("blog04-batch-dup", 1360, 540, "한 문장에서 같은 키를 두 번 넣으면",
                "DO UPDATE 는 \"결정적\" 이어서 한 명령이 같은 기존 행을 두 번 이상 건드릴 수 없다 (cardinality violation)", out=OUT)
    d.card("in", 40, 100, 1280, 90, "VALUES ('z','1'), ('z','2')", "같은 키 'z' 가 한 문장 안에 두 번 들어 있다", bg=P["note_bg"], stroke=P["line"], title_size=16, body_size=14)
    d.card("u", 40, 250, 620, 170, "… ON CONFLICT (key) DO UPDATE …",
           "에러\nON CONFLICT DO UPDATE command cannot affect row a second time\nHINT: Ensure that no rows proposed for insertion within\nthe same command have duplicate constrained values.",
           bg=P["bad_bg"], stroke=P["red"], title_size=16, body_size=13, title_color=P["red"])
    d.card("n", 700, 250, 620, 170, "… ON CONFLICT (key) DO NOTHING", "에러 없이 INSERT 0 1\n둘째 행은 건너뛴다", bg=P["ok_bg"], stroke=P["green"], title_size=16, body_size=15, title_color=P["green"])
    d.arrow([(350, 190), (350, 250)], P["red"], "DO UPDATE", label_size=12, start="in", end="u")
    d.arrow([(1010, 190), (1010, 250)], P["green"], "DO NOTHING", label_size=12, start="in", end="n")
    d.card("v", 40, 450, 1280, 60, "배치 upsert 를 짤 때 입력 키 중복을 먼저 제거해야 하는 이유", None, bg=P["todo_bg"], stroke=P["orange"], title_size=16)
    d.save()


def seq_gap():
    d = Diagram("blog04-seq-gap", 1360, 420, "DO NOTHING 으로 충돌해도 시퀀스 값은 소모된다",
                "bigserial 컬럼이 있는 테이블 (실측: psql)", out=OUT)
    steps = [("1  키 'a' 삽입", "id = 1", P["ok_bg"], P["green"]),
             ("2  키 'a' 재시도", "충돌 — 삽입되지 않는다\n그래도 시퀀스 값 하나가 소모된다", P["todo_bg"], P["orange"]),
             ("3  키 'b' 삽입", "id = 3\n(id 2 는 빈 구멍)", P["bad_bg"], P["red"])]
    for i, (t, b, bg, st) in enumerate(steps):
        x = 40 + i * 440
        d.card(f"s{i}", x, 110, 360, 130, t, b, bg=bg, stroke=st, title_size=16, body_size=15)
        if i:
            d.arrow([(x - 80, 175), (x, 175)], P["muted"], "다음", label_size=11, start=f"s{i - 1}", end=f"s{i}")
    d.card("v", 40, 290, 1280, 90, "id 가 연속이라는 가정은 이미 틀렸다 — 멱등 재시도가 많으면 구멍이 더 많아진다",
           "(해석) 기본값 평가가 충돌 검사보다 먼저라 생기는 것으로 보인다",
           bg=P["note_bg"], stroke=P["line"], title_size=16, body_size=14)
    d.save()


if __name__ == "__main__":
    for f in (clauses, rc_semantics, claim_fold, isolation, cte_trap, do_update_where, batch_dup, seq_gap):
        f()
    finish()
