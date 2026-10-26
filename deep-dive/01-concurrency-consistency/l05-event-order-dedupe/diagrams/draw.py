#!/usr/bin/env python3
"""01.05 이벤트 중복 · 순서 그림. 실행: python3 -I diagrams/draw.py (레슨 폴더에서)"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "tools"))
from diagram import Diagram, P, finish  # noqa: E402

OUT = pathlib.Path(__file__).parent


def event_dedupe():
    d = Diagram("event-dedupe", 1440, 900, "이벤트 중복 · 순서 — DB 에 도착한 순간",
                "at-least-once 라서 같은 메시지가 또 오고, 늦은 과거가 온다. messageId 로 중복을, version 으로 역전을 거른다", out=OUT)

    # ── 왼쪽: 도착한 이벤트가 지나는 길 ──
    d.rect("pa", 40, 110, 820, 740, P["white"], P["line"], dashed=True)
    d.text(60, 124, "이벤트가 지나는 길 — 전부 한 트랜잭션 (Q05 · Q06)", 17, P["ink"], weight=700)

    d.card("ev", 70, 180, 250, 110, "이벤트 도착", "messageId = m-7\nshipment s1 · version 3\nstatus = DELIVERED",
           bg=P["note_bg"], stroke=P["muted"], body_size=13, mono_body=True)
    d.card("why", 70, 330, 250, 250, "왜 축이 둘인가",
           "messageId\n같은 메시지의 재전달을 거른다\n→ 부수 효과(알림 · 적립)가\n    두 번 나가지 않는다 (Q01)\n\n"
           "version\n다른 메시지의 역전을 거른다\n→ 최신 상태가 과거로\n    되돌아가지 않는다 (Q02)\n\n"
           "하나만 두면 다른 쪽이 샌다",
           bg=P["todo_bg"], stroke=P["orange"], title_size=15, body_size=13)

    d.rect("tx", 360, 160, 470, 480, P["rs_bg"], P["orange"], dashed=True)
    d.text(376, 170, "BEGIN … COMMIT  (실패하면 둘 다 ROLLBACK)", 14, P["orange"], weight=700)
    d.card("s1", 385, 215, 420, 150, "1  inbox 선점",
           "INSERT INTO inbox (message_id) VALUES (?)\nON CONFLICT DO NOTHING\n\n영향 0행 = 이미 처리한 메시지 → DUPLICATE (끝)  Q04",
           bg=P["white"], stroke=P["front"], title_size=16, body_size=13)
    d.card("s2", 385, 425, 420, 190, "2  version 조건부 반영",
           "INSERT INTO shipment … ON CONFLICT (id)\nDO UPDATE SET …\nWHERE shipment.version < 이벤트 version\n\n영향 1행 = 반영 → APPLIED\n영향 0행 = 늦게 온 과거 → STALE  Q03",
           bg=P["white"], stroke=P["front"], title_size=16, body_size=13)
    d.arrow([d.anchor("ev", "e"), (340, d.anchor("ev", "e")[1]), (340, 290), (385, 290)], P["front"], start="ev")
    d.arrow([d.anchor("s1", "s"), d.anchor("s2", "n")], P["front"], "새 메시지 (1행)", start="s1", end="s2")

    d.pill("o1", 360, 670, 150, 46, "DUPLICATE", P["note_bg"], P["muted"])
    d.pill("o2", 535, 670, 130, 46, "STALE", P["note_bg"], P["muted"])
    d.pill("o3", 690, 670, 140, 46, "APPLIED", P["ok_bg"], P["green"])
    d.arrow([d.anchor("tx", "s", 0.17), d.anchor("o1", "n")], P["muted"], start=None, end="o1")
    d.arrow([d.anchor("tx", "s", 0.5), d.anchor("o2", "n")], P["muted"], start=None, end="o2")
    d.arrow([d.anchor("tx", "s", 0.85), d.anchor("o3", "n")], P["green"], start=None, end="o3")

    d.card("race", 70, 740, 760, 92, "동시에 같은 키 (Q07 · Q08 · Q09)",
           "WHERE version < v 는 행 락을 기다린 뒤 최신 값으로 다시 평가된다 → v2 · v3 어느 순서로 와도 최종 version 3\n"
           "같은 messageId 의 두 번째 INSERT 도 첫째의 커밋/롤백을 기다린다 → 커밋이면 0행, 롤백이면 1행",
           bg=P["note_bg"], stroke=P["line"], title_size=14, body_size=12)

    # ── 오른쪽: 기록과 반영이 갈라지면 ──
    d.rect("pb", 900, 110, 500, 740, P["white"], P["line"], dashed=True)
    d.text(920, 124, "inbox 기록과 반영이 갈라지면", 17, P["ink"], weight=700)
    d.card("bad", 925, 180, 450, 200, "따로 커밋 (Q05) — 처리됨인데 상태는 그대로",
           "1  INSERT inbox → COMMIT\n2  UPDATE shipment → 실패 (장애)\n3  재전달: INSERT inbox → 0행\n    → DUPLICATE 로 건너뜀\n\n결과  status = READY\n이 이벤트는 영영 반영되지 않는다",
           bg=P["bad_bg"], stroke=P["red"], title_size=14, body_size=14)
    d.card("good", 925, 440, 450, 200, "한 트랜잭션 (Q06) — 실패하면 기록도 사라진다",
           "1  INSERT inbox\n2  UPDATE shipment → 실패 → ROLLBACK\n3  재전달: INSERT inbox → 1행\n    → 정상 반영\n\n결과  status = DELIVERED\n재전달이 곧 재시도가 된다",
           bg=P["ok_bg"], stroke=P["green"], title_size=14, body_size=14)
    d.arrow([d.anchor("bad", "s"), d.anchor("good", "n")], P["muted"], "같은 장애, 다른 결말", start="bad", end="good")
    d.card("next", 925, 700, 450, 66, "다음 레슨", "Kafka 의 offset 커밋과 이 inbox 를 잇는 이야기는 02.03", bg=P["note_bg"],
           stroke=P["line"], title_size=14, body_size=13)
    d.save()


if __name__ == "__main__":
    event_dedupe()
    finish()
