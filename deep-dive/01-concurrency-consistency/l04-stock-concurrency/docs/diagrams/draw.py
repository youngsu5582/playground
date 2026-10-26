#!/usr/bin/env python3
"""01.04 docs 그림. 실행: python3 -I docs/diagrams/draw.py (레슨 폴더에서)"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[4] / "tools"))
from diagram import Diagram, P, finish  # noqa: E402

OUT = pathlib.Path(__file__).parent


def three_timelines():
    d = Diagram("three-timelines", 1500, 760, "구매자 B 의 길 — 세 전략 (A 가 같은 행을 먼저 잡고 있다)",
                "재고 행에 A 가 먼저 UPDATE 중일 때, 늦게 온 B 가 거치는 단계. 빨간 칸 = 기다림, 노란 칸 = 버려지고 다시 하는 일", out=OUT)
    W, H, Y0, DY = 190, 78, 130, 230

    def lane(prefix, y, title, sub, bg, stroke, steps, note):
        d.card(prefix + "t", 30, y, 220, H + 30, title, sub, bg=bg, stroke=stroke, title_size=15, body_size=13)
        x = 290
        prev = None
        for i, (txt, kind) in enumerate(steps):
            k = f"{prefix}{i}"
            if kind == "wait":
                d.pill(k, x, y + 10, W, H, txt, P["bad_bg"], P["red"], size=13)
            elif kind == "redo":
                d.pill(k, x, y + 10, W, H, txt, P["todo_bg"], P["orange"], size=13)
            else:
                d.pill(k, x, y + 10, W, H, txt, bg, stroke, size=13)
            if prev:
                d.arrow([d.anchor(prev, "e"), d.anchor(k, "w")], P["muted"], start=prev, end=k)
            prev = k
            x += W + 40
        d.text(290, y + H + (62 if prefix == 'o' else 30), note, 14, P["ink"])

    lane("a", Y0, "원자 조건부 UPDATE", "문장 1개 · 왕복 1회", P["ok_bg"], P["green"],
         [("UPDATE … qty = qty - 1\nWHERE qty >= 1", "n"), ("A 가 끝나기를\n기다림 (행 락)", "wait"),
          ("A 커밋 → 최신 행에\nWHERE 재평가", "n"), ("영향 행 1 = 성공\n0 = 품절", "n")],
         "행 락을 쥐는 시간 = UPDATE 문장 하나 + 커밋까지. 다시 하는 일 없음")
    lane("p", Y0 + DY, "비관 락 (FOR UPDATE)", "트랜잭션 · 왕복 3회", P["rs_bg"], P["orange"],
         [("BEGIN\nSELECT … FOR UPDATE", "n"), ("A 가 끝나기를\n기다림 (행 락)", "wait"),
          ("A 커밋 → 최신 qty\n를 읽는다", "n"), ("앱이 계산 →\nUPDATE", "n"), ("COMMIT\n= 락 해제", "n")],
         "행 락을 쥐는 시간 = 읽기부터 COMMIT 까지. 그 사이 앱 로직·외부 호출이 끼면 그만큼 줄이 길어진다")
    lane("o", Y0 + 2 * DY, "낙관 락 (version)", "읽을 땐 락 없음 · 충돌 시 재시도", P["as_bg"], P["front"],
         [("SELECT qty, version\n(락 없음)", "n"), ("앱 계산\n(틈)", "n"), ("UPDATE … WHERE\nversion = v", "n"),
          ("A 가 끝나기를\n기다림 (UPDATE 순간)", "wait"), ("A 커밋 → version\n바뀜 → 0행", "redo")],
         "0행이면 처음부터 다시 읽는다 (상한 MAX_ATTEMPTS). 진 횟수만큼 읽기 · 계산이 버려진다")
    d.arrow([(1290 + 0, Y0 + 2 * DY + 98), (1290, Y0 + 2 * DY + 128), (385, Y0 + 2 * DY + 128), (385, Y0 + 2 * DY + 88)],
            P["orange"], "재시도 — 읽기부터 전부 다시", dashed=True)
    d.save()


if __name__ == "__main__":
    three_timelines()
    finish()
