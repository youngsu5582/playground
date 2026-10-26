#!/usr/bin/env python3
"""01.04 재고 동시 차감 그림. 실행: python3 -I diagrams/draw.py (레슨 폴더에서)"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "tools"))
from diagram import Diagram, P, finish  # noqa: E402

OUT = pathlib.Path(__file__).parent


def stock_concurrency():
    d = Diagram("stock-concurrency", 1440, 940, "재고 동시 차감 — 틈을 닫는 세 가지",
                "문제는 '읽고 - 확인하고 - 쓰기' 사이의 틈이다. 세 전략은 그 틈을 각자 다른 곳에서 닫는다", out=OUT)

    # ── 왼쪽: 틈 ──
    d.rect("pa", 40, 110, 500, 790, P["white"], P["line"], dashed=True)
    d.text(60, 124, "틈 — 재고 1, 구매자 A · B (Q01)", 17, P["ink"], weight=700)
    d.pill("la", 80, 175, 180, 40, "A", P["as_bg"], P["front"], size=15)
    d.pill("lb", 320, 175, 180, 40, "B", P["rs_bg"], P["orange"], size=15)
    d.card("a1", 80, 235, 180, 70, "읽기", "qty = 1", bg=P["white"], stroke=P["front"], body_size=14)
    d.card("b1", 320, 235, 180, 70, "읽기", "qty = 1", bg=P["white"], stroke=P["orange"], body_size=14)
    d.card("a2", 80, 345, 180, 70, "쓰기", "qty = 1 - 1 = 0", bg=P["white"], stroke=P["front"], body_size=14)
    d.card("b2", 320, 345, 180, 70, "쓰기", "qty = 1 - 1 = 0", bg=P["bad_bg"], stroke=P["red"], body_size=14)
    d.arrow([d.anchor("a1", "s"), d.anchor("a2", "n")], P["front"], start="a1", end="a2")
    d.arrow([d.anchor("b1", "s"), d.anchor("b2", "n")], P["orange"], start="b1", end="b2")
    d.card("gap", 80, 445, 420, 90, "틈",
           "A 의 쓰기 전에 B 가 읽었다 → 둘 다 '재고 있네'\n재고 숫자는 0 (멀쩡해 보임) · 판 약속은 2개 — 갱신 손실",
           bg=P["todo_bg"], stroke=P["orange"], title_size=15, body_size=14)
    d.card("fix", 80, 570, 420, 150, "닫는 길은 둘",
           "1. 확인과 쓰기를 한 문장으로 붙인다 → 틈이 없다\n   (원자 UPDATE)\n"
           "2. 틈은 두되, 틈에서 끼어들면 알아챈다 / 못 끼어든다\n   (낙관 락 · 비관 락)",
           bg=P["ok_bg"], stroke=P["green"], title_size=15, body_size=14)
    d.card("link", 80, 750, 420, 120, "01.01 과 이어진다",
           "Q05  앱에서 읽고 계산해 쓰면 갱신 손실 = 이 그림\nQ06  UPDATE SET x = x - n 은 기다렸다가 최신 값으로 재평가\n"
           "→ 원자 UPDATE 가 안전한 이유가 Q06 이다",
           bg=P["note_bg"], stroke=P["line"], title_size=15, body_size=14)

    # ── 오른쪽: 세 전략 ──
    d.rect("pb", 580, 110, 820, 790, P["white"], P["line"], dashed=True)
    d.text(600, 124, "세 전략 — 무엇으로 막고, 언제 고르나", 17, P["ink"], weight=700)

    d.card("s1", 600, 170, 780, 190, "원자 조건부 UPDATE   (Q02 · Q03 · Q08)",
           "UPDATE stock SET qty = qty - 1 WHERE sku = ? AND qty >= 1\n"
           "막는 것  행 락이 줄 세우고, 기다린 쪽은 커밋된 최신 값으로 조건을 다시 본다\n"
           "결과    영향 행 1 = 성공 · 0 = 품절.  A 가 롤백하면 B 는 1행 (Q03)\n"
           "고를 때  단순 증감. 왕복 1회, 락을 직접 다루지 않는다 — 기본값",
           bg=P["ok_bg"], stroke=P["green"], title_size=17, body_size=16, mono_body=False)
    d.card("s2", 600, 380, 780, 190, "낙관 락 (version)   (Q04 · Q05)",
           "UPDATE … SET qty = ?, version = version + 1 WHERE sku = ? AND version = ?\n"
           "막는 것  읽은 뒤 남이 고쳤으면 0행 → 앱이 처음부터 다시 읽고 시도\n"
           "주의    UPDATE 순간엔 행 락 대기가 있다 (Q04) · RR 이면 엔진이 40001 로 먼저 막는다 (Q05)\n"
           "고를 때  충돌이 드물고 읽고-계산-쓰기 사이가 긴 일 (사람이 화면에서 편집 등)",
           bg=P["as_bg"], stroke=P["front"], title_size=17, body_size=16)
    d.card("s3", 600, 590, 780, 190, "비관 락 (FOR UPDATE)   (Q06 · Q07)",
           "BEGIN; SELECT qty FROM stock WHERE sku = ? FOR UPDATE; … UPDATE …; COMMIT\n"
           "막는 것  읽는 순간 행을 잠근다. 두 번째는 기다렸다가 앞사람이 커밋한 최신 값을 읽는다\n"
           "주의    평범한 SELECT 는 안 기다린다 (Q07 · MVCC). 락은 커밋까지 — 안에서 외부 API 금지\n"
           "고를 때  읽고 복잡하게 계산한 뒤 쓰는 일, 경합이 높을 때",
           bg=P["rs_bg"], stroke=P["orange"], title_size=17, body_size=16)
    d.card("hot", 600, 800, 780, 84, "경합이 심하면 낙관 락이 불리하다",
           "진 쪽은 읽기부터 전부 다시 + 상한을 넘으면 실패.  50명이 한 행에 몰리면 재시도가 몰린다 — 관찰 표에서 직접 본다",
           bg=P["todo_bg"], stroke=P["orange"], title_size=15, body_size=14)
    d.save()


if __name__ == "__main__":
    stock_concurrency()
    finish()
