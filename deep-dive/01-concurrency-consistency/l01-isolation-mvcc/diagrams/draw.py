#!/usr/bin/env python3
"""01.01 격리수준 · MVCC 그림. 실행: python3 -I diagrams/draw.py (레슨 폴더에서)"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "tools"))
from diagram import Diagram, P, finish  # noqa: E402

OUT = pathlib.Path(__file__).parent


def mvcc_isolation():
    d = Diagram("mvcc-isolation", 1440, 900, "격리수준 · MVCC — PostgreSQL 16",
                "쓰기는 행을 덮어쓰지 않고 새 버전을 만든다. 각 트랜잭션은 자기 스냅샷에 보이는 버전만 읽는다", out=OUT)

    # ── 왼쪽: MVCC ──
    d.rect("pa", 40, 110, 640, 740, P["white"], P["line"], dashed=True)
    d.text(60, 124, "MVCC — 행은 버전의 사슬이다 (Q10)", 17, P["ink"], weight=700)
    d.card("v1", 60, 180, 250, 120, "버전 1   ctid (0,1)", "balance = 100\nxmin = 701  (만든 트랜잭션)\nxmax = 705  (지운 트랜잭션)",
           bg=P["note_bg"], stroke=P["muted"], body_size=13, mono_body=True)
    d.card("v2", 410, 180, 250, 120, "버전 2   ctid (0,2)", "balance = 50\nxmin = 705\nxmax = (없음 — 최신)",
           bg=P["as_bg"], stroke=P["front"], body_size=13, mono_body=True)
    d.arrow([d.anchor("v1", "e"), d.anchor("v2", "w")], P["muted"], "UPDATE\n(705)", start="v1", end="v2")

    d.card("ra", 60, 360, 250, 132, "A — REPEATABLE READ", "스냅샷: 704 시점\n705 는 '아직 안 끝난' 트랜잭션\n→ 버전 1 을 본다 (100)",
           bg=P["white"], stroke=P["back"], body_size=13)
    d.card("rc", 410, 360, 250, 132, "C — READ COMMITTED", "문장마다 새 스냅샷\n705 커밋 이후의 문장\n→ 버전 2 를 본다 (50)",
           bg=P["white"], stroke=P["back"], body_size=13)
    d.arrow([d.anchor("ra", "n"), d.anchor("v1", "s")], P["back"], "보인다", start="ra", end="v1")
    d.arrow([d.anchor("rc", "n"), d.anchor("v2", "s")], P["back"], "보인다", start="rc", end="v2")

    d.card("rule", 80, 540, 570, 150, "보이는 버전 = xmin 이 내 스냅샷 전에 커밋됐고, xmax 는 아직 아닌 것",
           "읽기는 락을 잡지 않는다 → 쓰는 중인 행을 읽어도 기다리지 않는다 (Q10)\n"
           "UPDATE 는 새 버전 → ctid 가 바뀐다. 옛 버전은 VACUUM 이 치운다\n"
           "RR 의 스냅샷은 '첫 문장'에 잡힌다 — BEGIN 이 아니라 (Q02)",
           bg=P["todo_bg"], stroke=P["orange"], title_size=14, body_size=13)
    d.card("cost", 80, 720, 570, 100, "대가", "긴 트랜잭션 = 옛 버전을 못 치움 (bloat)\n쓰기 경쟁은 MVCC 가 아니라 행 락 · 직렬화 검사가 맡는다 → 오른쪽 표",
           bg=P["note_bg"], stroke=P["line"], title_size=14, body_size=13)

    # ── 오른쪽: 격리수준 표 ──
    d.rect("pb", 720, 110, 680, 740, P["white"], P["line"], dashed=True)
    d.text(740, 124, "격리수준 × 이상 현상 — PostgreSQL 실제 동작", 17, P["ink"], weight=700)
    cols = ["READ\nUNCOMMITTED", "READ\nCOMMITTED", "REPEATABLE\nREAD", "SERIALIZABLE"]
    rows = [
        ("더티 리드", ["막힘 Q04", "막힘", "막힘", "막힘"]),
        ("반복 불가 읽기", ["생김", "생김 Q01", "막힘 Q02", "막힘"]),
        ("팬텀", ["생김", "생김", "막힘 Q03", "막힘"]),
        ("갱신 손실\n(앱에서 읽고 써서)", ["생김", "생김 Q05", "40001 Q07", "40001"]),
        ("write skew", ["생김", "생김", "생김 Q08", "40001 Q09"]),
    ]
    X0, CW, Y0, RH = 900, 120, 170, 96
    for i, c in enumerate(cols):
        d.pill(f"c{i}", X0 + i * CW + 4, Y0, CW - 8, 52, c, P["note_bg"], P["ink"], size=12)
    for r, (label, cells) in enumerate(rows):
        y = Y0 + 64 + r * RH
        d.pill(f"r{r}", 740, y, 152, RH - 12, label, P["white"], P["ink"], size=13)
        for i, cell in enumerate(cells):
            ok = cell.startswith("막힘")
            retry = cell.startswith("40001")
            bg = P["ok_bg"] if ok else (P["todo_bg"] if retry else P["bad_bg"])
            st = P["green"] if ok else (P["orange"] if retry else P["red"])
            d.pill(f"x{r}{i}", X0 + i * CW + 4, y, CW - 8, RH - 12, cell.replace(" Q", "\nQ"), bg, st, size=13)
    d.card("legend", 740, 730, 640, 100, "읽는 법",
           "초록 막힘 · 빨강 생김(데이터가 틀어진다) · 주황 40001 = 엔진이 진 쪽을 실패시킨다\n"
           "→ 40001 을 받은 쪽은 처음부터 다시 해야 한다. 재시도는 앱의 몫 — 구현: Tx.serializable\n"
           "PG 의 READ UNCOMMITTED = READ COMMITTED.  RR 은 SQL 표준보다 강하다 (팬텀도 막음)",
           bg=P["note_bg"], stroke=P["line"], title_size=14, body_size=12)
    d.save()


if __name__ == "__main__":
    mvcc_isolation()
    finish()
