#!/usr/bin/env python3
"""01.03 멱등성 그림. 실행: python3 -I diagrams/draw.py (레슨 폴더에서)"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "tools"))
from diagram import Diagram, P, finish  # noqa: E402

OUT = pathlib.Path(__file__).parent


def idempotency():
    d = Diagram("idempotency", 1440, 900, "멱등성 — 같은 요청이 두 번 와도 한 번만",
                "확인과 선점을 한 문장으로 합치면, 기다림 · 재생 · 재시도가 DB 에서 공짜로 온다", out=OUT)

    # ── 왼쪽: 왜 깨지고 무엇이 막나 ──
    d.rect("pa", 40, 110, 660, 740, P["white"], P["line"], dashed=True)
    d.text(60, 124, "확인하고 넣기는 깨진다 (Q01 · Q02)", 17, P["ink"], weight=700)
    d.card("a1", 60, 170, 300, 100, "A   SELECT … WHERE key", "-> 0행   (없네, 내가 넣자)",
           bg=P["white"], stroke=P["front"], body_size=14)
    d.card("b1", 380, 170, 300, 100, "B   SELECT … WHERE key", "-> 0행   (없네, 내가 넣자)",
           bg=P["white"], stroke=P["back"], body_size=14)
    d.card("both", 60, 330, 620, 120, "둘 다 INSERT 한다 -> 같은 키 2행, 결제도 2번",
           "SELECT 와 INSERT 사이의 틈에서 서로를 못 본다 (제약이 없을 때)\n"
           "유니크 제약이 있으면 둘째는 에러 23505 — 중복은 막히지만 에러로 샌다",
           bg=P["bad_bg"], stroke=P["red"], title_size=15, body_size=13)
    d.arrow([d.anchor("a1", "s"), d.anchor("both", "n", 0.25)], P["front"], start="a1", end="both")
    d.arrow([d.anchor("b1", "s"), d.anchor("both", "n", 0.75)], P["back"], start="b1", end="both")

    d.text(60, 484, "한 문장으로 선점한다 — INSERT … ON CONFLICT DO NOTHING (Q03 ~ Q07)", 16, P["ink"], weight=700)
    rows = [
        ("처음 보는 키", "1행 = 선점 성공 -> 내가 처리한다", P["ok_bg"], P["green"]),
        ("이미 커밋된 키", "0행 = 선점 실패 -> 저장된 응답을 돌려준다", P["as_bg"], P["front"]),
        ("남이 처리 중 (미커밋)", "기다린다 ... 끝나면 0행 -> 응답 재생 (Q03 Q07)", P["todo_bg"], P["orange"]),
        ("남이 처리하다 롤백", "기다리다 1행 -> 내가 처리한다 (Q05)", P["todo_bg"], P["orange"]),
    ]
    for i, (label, result, bg, st) in enumerate(rows):
        y = 520 + i * 76
        d.pill(f"l{i}", 60, y, 220, 62, label, P["white"], P["ink"], size=14)
        d.pill(f"r{i}", 296, y, 384, 62, result, bg, st, size=14)
    d.text(60, 826, "DO NOTHING 이어도 '기다림' 은 있다. 영향 행 수 0 / 1 이 곧 선점 여부", 13, P["muted"])

    # ── 오른쪽: pay() 흐름 ──
    d.rect("pb", 730, 110, 670, 740, P["white"], P["line"], dashed=True)
    d.text(750, 124, "PaymentService#pay — 한 호출 = 한 트랜잭션", 17, P["ink"], weight=700)
    d.pill("begin", 965, 170, 200, 44, "BEGIN", P["note_bg"], P["muted"], size=15)
    d.card("claim", 915, 244, 300, 112, "claim   (빈칸 1)", "INSERT … ON CONFLICT\nDO NOTHING -> 영향 행 수",
           bg=P["todo_bg"], stroke=P["orange"], body_size=14, align="center")
    d.arrow([d.anchor("begin", "s"), d.anchor("claim", "n")], P["muted"], start="begin", end="claim")
    d.card("proc", 750, 420, 290, 130, "process   (제공)", "외부 결제 호출\npayments INSERT\n키를 DONE 으로",
           bg=P["ok_bg"], stroke=P["green"], body_size=14, align="center")
    d.card("rep", 1090, 420, 290, 130, "replay   (빈칸 2)", "저장된 request_hash 와 비교\n다르면 Conflict 예외\n같으면 저장된 응답",
           bg=P["todo_bg"], stroke=P["orange"], body_size=14, align="center")
    d.arrow([d.anchor("claim", "s", 0.2), d.anchor("proc", "n", 0.5)], P["green"], "1행", start="claim", end="proc")
    d.arrow([d.anchor("claim", "s", 0.8), d.anchor("rep", "n", 0.5)], P["front"], "0행", start="claim", end="rep")
    d.pill("commit", 940, 600, 250, 44, "COMMIT", P["note_bg"], P["muted"], size=15)
    d.arrow([d.anchor("proc", "s"), (895, 622), d.anchor("commit", "w")], P["muted"])
    d.arrow([d.anchor("rep", "s"), (1235, 622), d.anchor("commit", "e")], P["muted"])

    d.card("fail", 750, 682, 630, 150, "예외가 나면 ROLLBACK — 키 행도 같이 사라진다",
           "외부 결제가 실패하면 같은 키로 다시 시도할 수 있다\n"
           "에러 23505 를 맞은 트랜잭션은 이후 문장이 전부 25P02 (Q09)\n"
           "-> ON CONFLICT 로 에러 자체를 피하거나, SAVEPOINT 로 감싼다 (Q10)\n"
           "키를 먼저 커밋하는 설계는 죽은 처리를 풀 lease 가 필요하다",
           bg=P["bad_bg"], stroke=P["red"], title_size=15, body_size=13)
    d.save()


if __name__ == "__main__":
    idempotency()
    finish()
