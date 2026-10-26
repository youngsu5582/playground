#!/usr/bin/env python3
"""01.02 행 락 · 데드락 그림. 실행: python3 -I diagrams/draw.py (레슨 폴더에서)"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "tools"))
from diagram import Diagram, P, finish  # noqa: E402

OUT = pathlib.Path(__file__).parent


def row_locks():
    d = Diagram("row-locks-deadlock", 1440, 900, "행 락 · 데드락 — PostgreSQL 16",
                "같은 행을 노리는 쓰기는 줄을 선다. 읽기는 서지 않는다. 줄을 안 서는 법과, 줄이 원이 될 때(데드락)", out=OUT)

    # ── 왼쪽: 행 락 충돌표 ──
    d.rect("pa", 40, 110, 660, 740, P["white"], P["line"], dashed=True)
    d.text(60, 124, "행 락 4종 — 누가 누구를 막나 (Q01 · Q02 · Q07 · Q08)", 17, P["ink"], weight=700)
    modes = ["FOR KEY\nSHARE", "FOR\nSHARE", "FOR NO KEY\nUPDATE", "FOR\nUPDATE"]
    X0, CW, Y0, RH = 290, 100, 170, 70
    d.text(60, Y0 - 4, "잡혀 있는 락 →", 13, P["muted"])
    d.text(60, Y0 + 30, "내가 요청하는 락 ↓", 13, P["muted"])
    for i, m in enumerate(modes):
        d.pill(f"h{i}", X0 + i * CW + 4, Y0, CW - 8, 52, m, P["note_bg"], P["ink"], size=12)
    conflict = [
        [0, 0, 0, 1],
        [0, 0, 1, 1],
        [0, 1, 1, 1],
        [1, 1, 1, 1],
    ]
    for r, m in enumerate(modes):
        y = Y0 + 64 + r * RH
        d.pill(f"l{r}", 60, y, 220, RH - 10, m.replace("\n", " "), P["note_bg"], P["ink"], size=13)
        for i, c in enumerate(conflict[r]):
            d.pill(f"c{r}{i}", X0 + i * CW + 4, y, CW - 8, RH - 10, "기다림" if c else "함께", P["bad_bg"] if c else P["ok_bg"],
                   P["red"] if c else P["green"], size=13)
    d.card("who", 60, 530, 620, 110, "누가 어떤 락을 잡나",
           "FOR UPDATE  —  DELETE · 키 열을 바꾸는 UPDATE · SELECT … FOR UPDATE\n"
           "FOR NO KEY UPDATE  —  그 밖의 UPDATE\n"
           "FOR KEY SHARE  —  자식 INSERT 가 부모 행에 건다 (Q08, 실측)\n"
           "평범한 SELECT  —  행 락을 잡지도, 락에 막히지도 않는다 (Q02)",
           bg=P["note_bg"], stroke=P["line"], title_size=14, body_size=13)
    d.card("wait", 60, 670, 620, 120, "줄을 서지 않으려면 (Q03 · Q04 · Q05)",
           "기본  —  잡힌 행 앞에서 끝날 때까지 기다린다\n"
           "NOWAIT  —  바로 55P03. 그 트랜잭션의 이후 문장은 25P02\n"
           "lock_timeout  —  기다리다 시간이 되면 55P03\n"
           "SKIP LOCKED  —  잡힌 행은 없는 셈 치고 다음 행. 작업 큐 (구현 1)",
           bg=P["todo_bg"], stroke=P["orange"], title_size=14, body_size=13)

    # ── 오른쪽: 데드락 ──
    d.rect("pb", 740, 110, 660, 740, P["white"], P["line"], dashed=True)
    d.text(760, 124, "데드락 — 서로의 행을 기다리는 원 (Q10)", 17, P["ink"], weight=700)
    d.pill("ta", 780, 170, 200, 44, "A  (1 → 2 순서)", P["as_bg"], P["front"], size=14)
    d.pill("tb", 1130, 170, 200, 44, "B  (2 → 1 순서)", P["bff_bg"], P["back"], size=14)
    d.card("r1", 780, 260, 200, 90, "행 1", "A 가 UPDATE 로 잡음", bg=P["ok_bg"], stroke=P["green"], title_size=15, body_size=13)
    d.card("r2", 1130, 260, 200, 90, "행 2", "B 가 UPDATE 로 잡음", bg=P["ok_bg"], stroke=P["green"], title_size=15, body_size=13)
    d.arrow([d.anchor("ta", "s"), d.anchor("r1", "n")], P["green"], "잡았다", start="ta", end="r1")
    d.arrow([d.anchor("tb", "s"), d.anchor("r2", "n")], P["green"], "잡았다", start="tb", end="r2")
    d.arrow([(980, 285), (1130, 285)], P["red"], "A 는 2 를 원한다", start="r1", end="r2")
    d.arrow([(1130, 325), (980, 325)], P["red"], "B 는 1 을 원한다", start="r2", end="r1")

    d.card("det", 780, 400, 550, 120, "엔진이 끊는다",
           "기다림이 deadlock_timeout(기본 1s)을 넘으면 순환을 검사\n"
           "순환이면 한쪽을 40P01 로 abort → 다른 쪽은 계속 진행\n"
           "누가 끊기나는 보장이 아니다 (공식 문서). 이 랩에서는\n"
           "먼저 기다린 쪽의 타이머가 먼저 울린다 (NOTES)",
           bg=P["bad_bg"], stroke=P["red"], title_size=14, body_size=12)
    d.card("pre", 780, 560, 550, 110, "예방 — 잠그는 순서를 하나로 (구현 2)",
           "방향이 아니라 행을 기준으로: 항상 작은 id 먼저\n"
           "1→2 이체도 2→1 이체도 1번 → 2번 순서 → 원이 생길 수 없다\n"
           "순서가 같으면 뒤에 온 쪽은 그냥 줄을 선다",
           bg=P["ok_bg"], stroke=P["green"], title_size=14, body_size=12)
    d.card("obs", 780, 710, 550, 80, "누가 누구를 기다리나 (Q09)",
           "pg_blocking_pids(pid) · pg_stat_activity.wait_event\n"
           "pg_locks (granted = false)  — observe/SCRIPT.md",
           bg=P["note_bg"], stroke=P["line"], title_size=14, body_size=12)
    d.save()


if __name__ == "__main__":
    row_locks()
    finish()
