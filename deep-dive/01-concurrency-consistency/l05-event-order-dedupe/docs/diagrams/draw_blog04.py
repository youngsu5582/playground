#!/usr/bin/env python3
"""01.05 블로그판 04 그림. 실행: python3 -I docs/diagrams/draw_blog04.py (레슨 폴더에서)"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[4] / "tools"))
from diagram import Diagram, P, finish, timeline as _timeline  # noqa: E402

OUT = pathlib.Path(__file__).parent
KC = {"ok": (P["ok_bg"], P["green"]), "bad": (P["bad_bg"], P["red"]), "warn": (P["rs_bg"], P["orange"]),
      "a": (P["as_bg"], P["front"]), "b": (P["bff_bg"], P["back"]), "note": (P["note_bg"], P["muted"])}


def timeline(*a, **k):
    return _timeline(*a, out=OUT, **k)


def box(d, key, x, y, w, h, title, body, kind, dashed=False):
    bg, st = KC[kind]
    d.card(key, x, y, w, h, title, body, bg=bg, stroke=st, title_size=16, body_size=13, dashed=dashed)


def chain(d, prefix, y, h, items, x0=40, w=290, gap=100, labels=None):
    """items: (title, body, kind). 가로 한 줄 + 사이 화살표(라벨)."""
    for i, (t, b, k) in enumerate(items):
        box(d, f"{prefix}{i}", x0 + i * (w + gap), y, w, h, t, b, k)
    for i in range(len(items) - 1):
        xa, xb = x0 + i * (w + gap) + w, x0 + (i + 1) * (w + gap)
        lab = labels[i] if labels and i < len(labels) else None
        d.arrow([(xa, y + h / 2), (xb, y + h / 2)], P["muted"], label=lab, label_size=12,
                start=f"{prefix}{i}", end=f"{prefix}{i + 1}")



def intro():
    d = Diagram("blog04-intro", 1360, 400, "도입: messageId 는 새것인데 version 은 낡았다",
                "inbox 는 \"같은 메시지의 재전달\" 만 막는다 — 다른 메시지의 역전은 그대로 통과한다", out=OUT)
    chain(d, "i", 120, 150, [
        ("상태: version 6 · 완료", "배송이 완료 상태로 저장돼 있다", "ok"),
        ("늦은 이벤트 version 4", "messageId 는 처음 보는 것이라\ninbox 를 통과한다", "warn"),
        ("그냥 덮어쓴다", "마지막에 쓴 것이 이긴다", "bad"),
        ("상태가 과거로", "고객에게 \"배송 중\" 알림이\n다시 간다 (에러는 없다)", "bad")],
        w=270, gap=60, labels=["도착", "덮어씀", "결과"])
    d.text(40, 320, "version 이 이 역전을 거른다 — messageId 가 막는 대상과 version 이 막는 대상은 다르다", 15, P["muted"])
    d.save()


def rule():
    d = Diagram("blog04-rule", 1360, 460, "version = 순서 키 — 클 때만 반영한다",
                "이벤트에 \"이 배송 건의 n 번째 변경\" 이라는 정수를 싣고, 상태 테이블에는 마지막으로 반영한 version 을 저장한다", out=OUT)
    box(d, "e", 40, 160, 330, 120, "이벤트 version", "도착한 이벤트가 싣고 온 정수", "a")
    box(d, "s", 40, 300, 330, 120, "저장된 version", "상태 테이블이 마지막으로\n반영한 version", "b")
    box(d, "c", 470, 215, 280, 110, "이벤트 > 저장?", "한 문장 안에서 비교한다", "warn")
    d.arrow([(370, 220), (470, 255)], P["muted"])
    d.arrow([(370, 360), (470, 285)], P["muted"])
    box(d, "y", 900, 130, 420, 120, "더 크다 → 반영 (APPLIED)", "version 과 status 를 덮어쓴다", "ok")
    box(d, "n", 900, 290, 420, 140, "같거나 작다 → 무시 (STALE)", "늦게 온 과거를 걸러낸다\n에러가 아니라 정상 결과다", "bad")
    d.arrow([(750, 250), (900, 190)], P["green"], label="크다", label_size=12)
    d.arrow([(750, 290), (900, 350)], P["red"], label="같거나\n작다", label_size=12)
    d.save()


def upsert_anatomy():
    d = Diagram("blog04-upsert", 1360, 640, "조건부 upsert 한 문장 읽기",
                "PostgreSQL 16 INSERT 문서 기준 — 읽고 비교하고 쓰는 세 단계가 아니라 한 문장이라 사이에 낄 틈이 없다", out=OUT)
    d.card("sql", 40, 110, 560, 220, "SQL", "INSERT INTO shipment\n  (id, version, status, change_count)\nVALUES (?, ?, ?, 1)\nON CONFLICT (id) DO UPDATE\n   SET version = EXCLUDED.version,\n       status = EXCLUDED.status,\n       change_count = shipment.change_count + 1\n WHERE shipment.version < EXCLUDED.version;",
           bg=P["note_bg"], stroke=P["ink"], title_size=15, body_size=13, mono_body=True)
    facts = [("ON CONFLICT DO UPDATE", "conflict_target 이 필수 — 여기서는 (id) 의 PK\n원자적 INSERT 또는 UPDATE 결과를 보장한다 (UPSERT)"),
             ("WHERE", "충돌이 갱신 후보로 확인된 뒤 마지막에 평가된다\n참인 행만 갱신된다 — 단, 모든 행이 잠긴다"),
             ("EXCLUDED 와 테이블 이름", "EXCLUDED = 삽입하려던(충돌한) 행\n테이블 이름(shipment) = 기존 행"),
             ("RETURNING · 명령 태그 count", "삽입 · 갱신된 행만 돌려주고 센다\nWHERE 가 거짓이라 갱신 안 된 행은 반환 · 집계 안 됨")]
    for i, (t, b) in enumerate(facts):
        box(d, f"f{i}", 640, 110 + i * 112, 680, 100, t, b, "ok" if i != 1 else "warn")
    box(d, "n", 40, 350, 560, 110, "그래서 앱은 영향 행 수만 보면 된다", "한 문장의 결과가 APPLIED 인지 STALE 인지\n영향 행 수로 갈린다 (구체 값은 접힌 칸)", "a")
    d.text(40, 490, "read-modify-write 를 피하는 것은 01.01 의 갱신 손실과 같은 원리다", 14, P["muted"])
    d.save()


def lt_le():
    d = Diagram("blog04-lt-le", 1360, 470, "같은 version 이 또 오면 — < 와 <=",
                "같은 이벤트가 inbox 를 뚫고 와도 version 조건이 막느냐가 갈린다", out=OUT)
    box(d, "a", 40, 110, 620, 230, "WHERE shipment.version < EXCLUDED.version",
        "같은 version 은 무시한다\n같은 version 의 다른 메시지(다른 messageId)도 무시된다\n— 보통 \"version 이 같으면 같은 사건\" 계약일 때 맞다\n\n같은 이벤트의 재전달은 갱신되지 않는다", "ok")
    box(d, "b", 700, 110, 620, 230, "WHERE shipment.version <= EXCLUDED.version",
        "같은 version 도 덮어쓴다\n같은 이벤트가 inbox 를 뚫고 와도 반영이\n한 번 더 일어난다\n\n부수 효과 카운트가 올라간다", "bad")
    box(d, "n", 40, 365, 1280, 80, "(해석) version 이 \"엔티티당 단조 증가, 사건마다 유일\" 이면 < 가 맞다",
        "같은 version 에 서로 다른 내용이 오는 소스라면 소스가 version 계약을 어긴 것이다 — 순서가 아니라 데이터 계약부터 고친다", "note")
    d.save()


def concurrent():
    timeline("blog04-concurrent", "동시에 와도 — 행 락과 READ COMMITTED 의 재평가",
             "같은 배송 건(같은 행)에 두 세션이 동시에 upsert 한다 — A 는 version 8, B 는 version 6",
             [("A", "1  BEGIN; upsert (version 8)", "행 락을 잡고 아직 커밋 전", None),
              ("B", "2  upsert (version 6)", "같은 행의 락을 기다린다 (transactionid)", None),
              ("A", "3  COMMIT", "version 8 이 저장된다", None),
              ("B", "4  깨어난다 → WHERE 재평가", "갱신된 버전에서 8 < 6 은 거짓 → 갱신 안 됨", "ok")],
             [(0, 1, "A 의 행 락이\nB 를 막는다", 0.3), (2, 3, "커밋된 version 8 을\nB 가 다시 본다", 0.5)],
             "락을 기다린 쪽은 첫 갱신자가 커밋하면 갱신된 버전에 WHERE 를 다시 평가한다 (13.2 Read Committed).\n"
             "도착 · 처리 순서와 무관하게 같은 결론으로 수렴한다 — 큰 version 이 남는다.",
             "행 락이 줄을 세우고, 재평가가 결론을 낸다", vcolor="ok", level="READ COMMITTED")


def batch_21000():
    d = Diagram("blog04-batch", 1360, 440, "한 문장에 같은 키가 둘이면 (21000)",
                "INSERT … ON CONFLICT DO UPDATE 는 deterministic 문장이라 한 행을 한 번 넘게 영향 줄 수 없다 (실측: psql 2026-10-13)", out=OUT)
    chain(d, "b", 120, 150, [
        ("배치로 모아 한 문장으로", "VALUES (s1, 5, ...), (s1, 6, ...)\nON CONFLICT (id) DO UPDATE ...", "a"),
        ("같은 행을 두 번 건드린다", "한 명령 안에서 같은 행이\n두 번 영향 받는다", "bad"),
        ("ERROR 21000", "ON CONFLICT DO UPDATE command\ncannot affect row a second time", "bad")],
        w=380, gap=70, labels=["실행", "거부"])
    box(d, "n", 40, 300, 1280, 100, "해결 (해석)",
        "같은 키는 version 최댓값 하나로 먼저 줄인다 — 줄여서 버린 메시지의 inbox 기록도 모두 남긴다\n(그래야 재전달에서 중복되지 않는다)", "ok")
    d.save()


def no_version():
    d = Diagram("blog04-no-version", 1360, 560, "version 이 없는 이벤트라면 (해석 — 이 레슨에서 실측하지 않음)",
                "방법마다 한계가 있다 — 가장 근본적인 것은 소스에 순번을 달라고 하는 것", out=OUT)
    rows = [("occurredAt 시각 비교", "시계 오차 · 같은 시각. 순서 키로 쓰기 위험하다", "bad"),
            ("상태 전이표 (허용된 전이만 반영)", "정당한 후퇴(예: 반송)를 구분해야 하고,\n두 상태만으로는 건너뛴 상태를 알 수 없다", "warn"),
            ("상태 enum 의 rank 비교", "간단하지만 정당한 후퇴를 놓친다", "warn"),
            ("이벤트는 신호로만, 소스에서 최신 상태를 조회", "소스 조회 비용 · 소스가 최신을 주는 계약이 필요", "warn"),
            ("소스에 version(순번)을 달라고 요청", "가장 근본적이다", "ok")]
    for i, (t, b, k) in enumerate(rows):
        y = 110 + i * 88
        box(d, f"m{i}", 40, y, 540, 76, t, None, k)
        box(d, f"l{i}", 620, y, 700, 76, "비고" if i == 4 else "한계", b, "note")
    d.save()


if __name__ == "__main__":
    for f in (intro, rule, upsert_anatomy, lt_le, concurrent, batch_21000, no_version):
        f()
    finish()
