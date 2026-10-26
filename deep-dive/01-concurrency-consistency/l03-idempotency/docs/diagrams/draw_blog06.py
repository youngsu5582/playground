#!/usr/bin/env python3
"""01.03 블로그판 06 그림. 실행: python3 -I docs/diagrams/draw_blog06.py (레슨 폴더에서)"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[4] / "tools"))
from diagram import Diagram, P, finish, timeline as _timeline  # noqa: E402

OUT = pathlib.Path(__file__).parent


def timeline(*a, **k):
    return _timeline(*a, out=OUT, **k)


def intro():
    d = Diagram("blog06-intro", 1400, 560, "결제 요청 하나가 지나는 길과, 키만으로는 못 막는 네 곳",
                "키 테이블에 유니크 제약만 있다고 설계가 끝나는 것이 아니다 — 상태 · 지문 · 만료 · 장애 시 인수가 들어 있어야 한다", out=OUT)
    flow = [("클라이언트", "멱등 키를 만들어\n요청을 보낸다"), ("서버", "키를 선점한다"),
            ("외부 결제사", "승인 호출\n(DB 트랜잭션 밖의 세계)"), ("DB", "결제 행 · 키 상태를\n커밋한다")]
    for i, (t, b) in enumerate(flow):
        d.card(f"f{i}", 40 + i * 340, 120, 300, 100, t, b, bg=P["as_bg"] if i != 2 else P["rs_bg"],
               stroke=P["front"] if i != 2 else P["orange"], title_size=16, body_size=14)
        if i:
            d.arrow([d.anchor(f"f{i-1}", "e"), d.anchor(f"f{i}", "w")], P["muted"], start=f"f{i-1}", end=f"f{i}")
    gaps = [("1  처리 중인데 같은 키가 또 온다", "기다릴까, 돌려보낼까", "f1"),
            ("2  같은 키인데 내용이 다르다", "키만 보고 응답을 돌려주면?", "f1"),
            ("3  승인은 나갔는데 DB 가 죽는다", "돈은 나갔고 키는 사라졌다", "f2"),
            ("4  키가 만료된 뒤 늦은 재시도가 온다", "새 요청으로 보이면 중복", "f0")]
    for i, (t, b, tgt) in enumerate(gaps):
        d.card(f"g{i}", 40 + i * 340, 340, 310, 120, t, b, bg=P["bad_bg"], stroke=P["red"], title_size=15, body_size=14)
    d.arrow([d.anchor("g0", "n", 0.7), d.anchor("f1", "s", 0.3)], P["red"], None, start="g0", end="f1")
    d.arrow([d.anchor("g1", "n", 0.3), d.anchor("f1", "s", 0.7)], P["red"], None, start="g1", end="f1")
    d.arrow([d.anchor("g2", "n", 0.5), d.anchor("f2", "s", 0.5)], P["red"], None, start="g2", end="f2")
    d.arrow([d.anchor("g3", "n", 0.5), (1195, 300), (190, 300), d.anchor("f0", "s", 0.5)], P["red"], "클라이언트의 재시도가 키 보존 기간을 넘는다", label_at=(690, 300))
    d.card("n", 40, 490, 1320, 50, "중복 결제 장애 대부분이 이 네 칸의 빈자리에서 난다", None,
           bg=P["note_bg"], stroke=P["line"], title_size=15)
    d.save()


def fingerprint():
    d = Diagram("blog06-fingerprint", 1360, 560, "요청 지문 — 같은 키, 다른 내용을 가른다",
                "키가 같아도 내용이 다르면 클라이언트의 버그나 키 재사용이다. 저장된 요청 해시와 비교한다", out=OUT)
    d.card("r1", 40, 130, 420, 110, "첫 요청", "키 K · 고객 c1 · 금액 30,000\n→ 지문 H1 을 키 행에 저장 (고객 + 금액의 SHA-256)",
           bg=P["as_bg"], stroke=P["front"], title_size=16, body_size=14)
    d.card("r2", 40, 330, 420, 110, "나중 요청 — 같은 내용", "키 K · 고객 c1 · 금액 30,000\n→ 지문 H1",
           bg=P["as_bg"], stroke=P["front"], title_size=16, body_size=14)
    d.card("r3", 40, 450, 420, 100, "나중 요청 — 다른 내용", "키 K · 고객 c1 · 금액 8,000\n→ 지문 H2",
           bg=P["bff_bg"], stroke=P["back"], title_size=16, body_size=14)
    d.card("cmp", 600, 300, 300, 140, "저장된 지문과 비교", "선점에 실패했을 때만 비교한다\n(이 레슨의 replay)",
           bg=P["note_bg"], stroke=P["muted"], title_size=16, body_size=14)
    d.card("ok", 1000, 190, 330, 110, "같다 → 저장된 응답을 재생", "같은 키 = 같은 결과",
           bg=P["ok_bg"], stroke=P["green"], title_size=15, body_size=14)
    d.card("bad", 1000, 420, 330, 130, "다르다 → 거절", "이 레슨: IdempotencyKeyConflictException\nStripe: 에러 · IETF 초안: 422 (SHOULD)",
           bg=P["bad_bg"], stroke=P["red"], title_size=15, body_size=14)
    d.arrow([d.anchor("r1", "e", 0.5), (520, 185), (520, 340), d.anchor("cmp", "w", 0.2)], P["muted"], "H1 이\n저장돼 있다", label_at=(520, 260))
    d.arrow([d.anchor("r2", "e", 0.5), d.anchor("cmp", "w", 0.5)], P["front"], "H1", start="r2", end="cmp")
    d.arrow([d.anchor("r3", "e", 0.5), (560, 500), (560, 410), d.anchor("cmp", "w", 0.85)], P["back"], "H2", label_at=(560, 470))
    d.arrow([d.anchor("cmp", "e", 0.3), d.anchor("ok", "w", 0.5)], P["green"], "H1 = H1", start="cmp", end="ok")
    d.arrow([d.anchor("cmp", "e", 0.8), d.anchor("bad", "w", 0.4)], P["red"], "H1 ≠ H2", start="cmp", end="bad")
    d.save()


def in_progress():
    d = Diagram("blog06-in-progress", 1360, 460, "처리 중인 같은 키 — 기다릴까, 409 로 돌려보낼까",
                "한 트랜잭션 설계는 기다림이 공짜로 오지만, 커넥션을 쥔 채 기다린다", out=OUT)
    specs = [("기다린다 (이 레슨)", "선점 INSERT 가 DB 에서 대기\n\n구현이 짧다. 대기 중 커넥션을 쥔다\n기본 lock_timeout 은 0 (꺼짐) 이라 무제한",
              P["todo_bg"], P["orange"]),
             ("즉시 거절", "키를 먼저 커밋 → 선점 실패 시\n상태가 IN_PROGRESS 면 409\n\n커넥션 안 쥠. 클라이언트가 나중에 재시도",
              P["ok_bg"], P["green"]),
             ("시간 제한 대기", "SET LOCAL lock_timeout = '…' 후 선점\n→ 타임아웃을 409 로\n\n한 트랜잭션 설계에서 바운드를 둔다",
              P["as_bg"], P["front"])]
    for i, (t, b, bg, st) in enumerate(specs):
        d.card(f"c{i}", 40 + i * 445, 130, 410, 170, t, b, bg=bg, stroke=st, title_size=17, body_size=14)
    d.card("n", 40, 340, 1300, 90, "표준과 서비스는 어떻게 말하나",
           "IETF 초안: 원래 요청이 아직 처리 중이면 409 로 응답하라 (SHOULD)\nStripe: 동시에 실행 중인 요청과 충돌한 경우 결과를 저장하지 않는다 (재시도 가능)",
           bg=P["note_bg"], stroke=P["line"], title_size=15, body_size=14)
    d.save()


def lock_timeout():
    timeline("blog06-lock-timeout", "lock_timeout 으로 기다림에 상한을 둔다",
             "다른 세션이 같은 키를 미커밋으로 선점한 상태에서, 300ms 만 기다리고 포기한다 (실측: psql 2026-10-13)",
             [("A", "1  BEGIN · 선점 INSERT (키 K)", "아직 커밋하지 않았다", None),
              ("B", "2  BEGIN · SET LOCAL lock_timeout = '300ms'", "이 트랜잭션에서만 쓰는 대기 상한", None),
              ("B", "3  선점 INSERT (같은 키 K)", "A 의 트랜잭션이 끝나기를 기다린다", None),
              ("B", "4  300ms 뒤 에러  (55P03 lock_not_available)", "canceling statement due to lock timeout", "bad"),
              ("B", "5  그 다음 문장", "거절된다 — 트랜잭션이 중단 상태", "bad")],
             [(0, 2, "A 의 미커밋\n선점을 기다린다", 0.5)],
             "타임아웃도 에러라서 B 의 트랜잭션은 중단 상태가 된다 (문서 05). 서버가 이 에러를 \"처리 중, 잠시 후 재시도 (409)\" 로\n"
             "매핑하고 롤백하는 것이 한 방법이다 (해석 — 설계 권고). B 는 아무것도 선점하지 못했으니 되돌릴 쓰기가 없다 (해석).",
             "기다림은 끝났지만 B 의 트랜잭션도 끝났다", level="READ COMMITTED")


def side_effect():
    d = Diagram("blog06-side-effect", 1400, 640, "DB 트랜잭션은 외부 호출을 되돌리지 못한다",
                "한 트랜잭션 설계에서 process 의 순서와, 어디서 끊어지느냐에 따른 결과", out=OUT)
    flow = [("BEGIN · claim", "키 선점\n(커밋 전)"), ("외부 결제 호출", "DB 트랜잭션 안에서 부른다"),
            ("payments INSERT", "결제 행 기록"), ("COMMIT", "키 DONE · 응답 저장")]
    for i, (t, b) in enumerate(flow):
        d.card(f"t{i}", 40 + i * 340, 120, 300, 100, t, b, bg=P["rs_bg"] if i == 1 else P["as_bg"],
               stroke=P["orange"] if i == 1 else P["front"], title_size=16, body_size=14)
        if i:
            d.arrow([d.anchor(f"t{i-1}", "e"), d.anchor(f"t{i}", "w")], P["muted"], start=f"t{i-1}", end=f"t{i}")
    fails = [("호출 전 · 중에 실패 (예외)", "돈: 안 나감\nDB: 롤백 → 키 없음\n같은 키 재시도: 새로 처리 — 정상", P["ok_bg"], P["green"]),
             ("호출 자체가 타임아웃", "돈: 모름\nDB: 롤백 → 키 없음\n같은 키 재시도: 모름 — 같은 문제가\n한 겹 아래로 이사했다", P["todo_bg"], P["orange"]),
             ("결제 성공 후 payments INSERT 실패", "돈: 나감\nDB: 롤백 → 키 없음\n같은 키 재시도: 두 번째 결제 — 중복", P["bad_bg"], P["red"]),
             ("결제 성공 후 COMMIT 실패 · 프로세스 사망", "돈: 나감\nDB: 롤백 → 키 없음\n같은 키 재시도: 두 번째 결제 — 중복", P["bad_bg"], P["red"])]
    for i, (t, b, bg, st) in enumerate(fails):
        d.card(f"f{i}", 40 + i * 340, 380, 320, 160, t, b, bg=bg, stroke=st, title_size=14, body_size=13)
    d.arrow([(200, 380), (200, 300), (420, 300), (420, 220)], P["green"], "여기서 끊기면", label_at=(310, 300))
    d.arrow([(530, 380), (530, 220)], P["orange"], "여기서 끊기면", label_at=(530, 300))
    d.arrow([(880, 380), (880, 220)], P["red"], "끊기면", label_at=(880, 300))
    d.arrow([(1220, 380), (1220, 220)], P["red"], "끊기면", label_at=(1220, 300))
    d.card("n", 40, 570, 1320, 50, "이 레슨이 풀어 주는 것은 DB 안의 중복이다. 외부 호출 쪽 틈(노랑 · 빨강)은 남는다", None,
           bg=P["note_bg"], stroke=P["line"], title_size=15)
    d.save()


def two_tx():
    d = Diagram("blog06-two-tx", 1400, 640, "키를 먼저 커밋하는 2-트랜잭션 설계",
                "외부 호출 구간에 커넥션을 쥐지 않는다. 대신 IN_PROGRESS 가 커밋된 채 남을 수 있다", out=OUT)
    d.card("t1", 40, 120, 400, 130, "tx1", "INSERT … 'IN_PROGRESS'\nON CONFLICT DO NOTHING ; COMMIT\n(선점을 먼저 커밋)",
           bg=P["as_bg"], stroke=P["front"], title_size=16, body_size=14)
    d.card("ex", 500, 120, 400, 130, "외부 호출", "트랜잭션 없음\n커넥션을 쥐지 않는다",
           bg=P["rs_bg"], stroke=P["orange"], title_size=16, body_size=14)
    d.card("t2", 960, 120, 400, 130, "tx2", "UPDATE idempotency_keys\nSET status = 'DONE', response = … ;\nINSERT payments ; COMMIT",
           bg=P["as_bg"], stroke=P["front"], title_size=16, body_size=14)
    d.arrow([d.anchor("t1", "e"), d.anchor("ex", "w")], P["muted"], start="t1", end="ex")
    d.arrow([d.anchor("ex", "e"), d.anchor("t2", "w")], P["muted"], start="ex", end="t2")
    d.card("w1", 40, 330, 420, 150, "선점에 실패한 요청은", "기존 상태를 읽는다\nDONE 이면 재생\nIN_PROGRESS 면 409\n지문이 다르면 거절",
           bg=P["ok_bg"], stroke=P["green"], title_size=15, body_size=14)
    d.card("w2", 490, 330, 420, 150, "IN_PROGRESS 가 커밋돼 있으면", "다른 요청의 선점은 기다리지 않고\n즉시 0행이 되고 SELECT 로 상태를 읽는다\n(실측: INSERT 0 0 · SELECT status → IN_PROGRESS)",
           bg=P["ok_bg"], stroke=P["green"], title_size=15, body_size=13)
    d.card("w3", 940, 330, 420, 150, "서버가 죽으면", "IN_PROGRESS 가 커밋된 채 영영 남는다\n→ 만료 시각(lease) · 인수 로직 · 정리가 필요하다",
           bg=P["bad_bg"], stroke=P["red"], title_size=15, body_size=14)
    d.arrow([d.anchor("t1", "s", 0.2), d.anchor("w1", "n", 0.5)], P["green"], "tx1 뒤", start="t1", end="w1")
    d.arrow([d.anchor("t1", "s", 0.8), d.anchor("w2", "n", 0.4)], P["green"], "커밋된 상태", start="t1", end="w2")
    d.arrow([d.anchor("ex", "s", 0.8), d.anchor("w3", "n", 0.3)], P["red"], "여기서 죽으면", start="ex", end="w3")
    d.card("n", 40, 520, 1320, 80, "한 트랜잭션 설계와의 차이",
           "커넥션 점유: 외부 호출 내내 vs 호출 구간엔 없음 · 서버가 죽으면: 키가 롤백으로 사라짐 vs 커밋된 채 남음 · 실패 상태: 저장 안 함 vs 저장할지 정해야 함",
           bg=P["note_bg"], stroke=P["line"], title_size=15, body_size=13)
    d.save()


def lease():
    d = Diagram("blog06-lease", 1400, 600, "lease — 죽은 처리를 풀어 주는 만료 시각과 원자적 인수",
                "(해석 — 이 레슨 코드가 아니라 패턴) 인수는 한 문장으로 원자적이어야 한다", out=OUT)
    d.card("a", 40, 130, 380, 120, "처리자가 죽었다", "IN_PROGRESS 가 커밋된 채 남고\n만료 시각(locked_until)이 지나간다",
           bg=P["bad_bg"], stroke=P["red"], title_size=16, body_size=14)
    d.card("b", 500, 130, 380, 120, "같은 키의 새 요청", "선점에 실패했고 상태가\nIN_PROGRESS · 만료됨을 읽었다",
           bg=P["as_bg"], stroke=P["front"], title_size=16, body_size=14)
    d.card("c", 960, 130, 400, 120, "인수 시도 (한 문장)", "UPDATE … SET locked_until = now() + 30 s\nWHERE key = ? AND status = 'IN_PROGRESS'\nAND locked_until < now()",
           bg=P["note_bg"], stroke=P["muted"], title_size=16, body_size=13)
    d.arrow([d.anchor("a", "e"), d.anchor("b", "w")], P["muted"], "시간이\n지난다", start="a", end="b")
    d.arrow([d.anchor("b", "e"), d.anchor("c", "w")], P["muted"], "인수를\n시도", start="b", end="c")
    d.card("ok", 960, 320, 400, 90, "영향 행 수 1", "내가 인수한다 — 이어서 처리", bg=P["ok_bg"], stroke=P["green"], title_size=16, body_size=14)
    d.arrow([d.anchor("c", "s", 0.5), d.anchor("ok", "n", 0.5)], P["green"], "1 행", start="c", end="ok")
    d.card("risk", 40, 320, 860, 120, "lease 가 너무 짧으면",
           "처음 처리자가 아직 살아 있는데 lease 가 먼저 만료되면 둘이 동시에 처리할 수 있다\n"
           "그래서 lease 는 처리 시간 상한보다 길어야 한다\n그래도 외부 호출 쪽 멱등성이 마지막 방어선이다 (해석)",
           bg=P["todo_bg"], stroke=P["orange"], title_size=16, body_size=14)
    d.card("n", 40, 500, 1320, 60, "같은 모양으로 ON CONFLICT DO UPDATE … WHERE 도 쓸 수 있다 (문서 04: 조건이 거짓이면 0행)", None,
           bg=P["note_bg"], stroke=P["line"], title_size=15)
    d.save()


if __name__ == "__main__":
    for f in (intro, fingerprint, in_progress, lock_timeout, side_effect, two_tx, lease):
        f()
    finish()
