#!/usr/bin/env python3
"""01.05 블로그판 05 그림. 실행: python3 -I docs/diagrams/draw_blog05.py (레슨 폴더에서)"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[4] / "tools"))
from diagram import Diagram, P, finish  # noqa: E402

OUT = pathlib.Path(__file__).parent
KC = {"ok": (P["ok_bg"], P["green"]), "bad": (P["bad_bg"], P["red"]), "warn": (P["rs_bg"], P["orange"]),
      "a": (P["as_bg"], P["front"]), "b": (P["bff_bg"], P["back"]), "note": (P["note_bg"], P["muted"])}


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



def outcomes():
    d = Diagram("blog05-outcomes", 1360, 470, "처리 한 건의 결과 — 정상 값 세 가지",
                "에러가 아니다. 구분해 두면 운영에서 \"재전달이 잘 걸러졌다\" 가 보인다", out=OUT)
    rows = [("APPLIED", "inbox: 기록   ·   상태: 갱신", "부수 효과: 한 번 일으켜도 된다", "ok"),
            ("STALE", "inbox: 기록   ·   상태: 그대로", "부수 효과: 일으키지 않는다", "warn"),
            ("DUPLICATE", "inbox: 이미 있음   ·   상태: 그대로", "부수 효과: 일으키지 않는다", "bad")]
    for i, (t, a, b, k) in enumerate(rows):
        box(d, f"o{i}", 40 + i * 440, 120, 400, 160, t, a + "\n\n" + b, k)
    box(d, "n", 40, 310, 1280, 110, "STALE 이어도 inbox 에는 기록한다 (이 레슨 구현 지침)",
        "같은 messageId 가 또 오면 DUPLICATE 로 끝나야 하기 때문이다. 기록하지 않으면 매번 상태 테이블을 다시 평가한다\n"
        "(결과는 같은 STALE 이지만 행 락을 잡는다). STALE 의 개수는 센다 — 역전이 얼마나 나는지가 소스 · 인프라 문제의 신호다 (해석)", "note")
    d.save()


def holes():
    d = Diagram("blog05-holes", 1360, 540, "messageId 와 version — 서로 다른 구멍을 막는다",
                "가진 것에 따라 막는 것과 새는 것이 다르다", out=OUT)
    box(d, "a", 40, 110, 410, 380, "messageId 만 (inbox)", "막는 것\n같은 메시지의 재전달\n\n새는 것\n처음 보는 다른 과거 메시지가\n상태를 되돌린다\n(Q02 와 같은 현상)", "warn")
    box(d, "b", 475, 110, 410, 380, "version 만", "막는 것\n늦은 과거\n\n새는 것 — 조건에 따라 다르다\n< 비교이고 부수 효과를 APPLIED 일\n때만 일으키면 재전달도 STALE 이라\n한 번이다\n새는 경우: <=, 부수 효과가 version 판정\n과 무관, delta 인데 version 이 건너뜀", "warn")
    box(d, "c", 910, 110, 410, 380, "둘 다 + 한 트랜잭션", "막는 것\n위 둘\n\n새는 것\n외부 호출\ninbox 보존 기간 밖의 재전달", "ok")
    d.save()


def version_only():
    d = Diagram("blog05-version-only", 1360, 780, "version 만으로 부수 효과를 제한할 수 있나 — 조건별로",
                "inbox 가 없을 때 (근거는 실측: psql 2026-10-13 · 해석 표시 그대로)", out=OUT)
    d.pill("h1", 40, 100, 440, 44, "상황", P["note_bg"], P["line"], size=14)
    d.pill("h2", 490, 100, 440, 44, "version 만 (inbox 없음)", P["note_bg"], P["line"], size=14)
    d.pill("h3", 940, 100, 380, 44, "근거", P["note_bg"], P["line"], size=14)
    rows = [("같은 메시지 재전달 · <\n· 부수 효과를 APPLIED 일 때만", "한 번. 두 번째는 0행이라 STALE", "v1 을 두 번 upsert →\n두 번째는 갱신 없음, change_count 1", "ok"),
            ("같은 메시지 재전달 · <=", "샌다. 두 번째도 APPLIED", "<= 로 같은 v1 두 번 → 둘 다 반영,\nchange_count 가 두 번 오른다", "bad"),
            ("inbox 를 지운 뒤의 재전달", "< 이고 APPLIED 일 때만이면\nSTALE 이라 안전", "실측: psql 2026-10-13", "ok"),
            ("부수 효과가 version 판정과 무관\n(알림 API · 판정 결과를 안 보는 카운터)", "샌다. 판정과 상관없이 나간다", "(해석)", "bad"),
            ("같은 version 의 다른 메시지", "뒤에 온 것은 STALE 로 버려진다 —\n중복이 아니라 유실. inbox 가 있어도 같다", "같은 v1 에 status 만 다른 upsert →\n갱신 없음", "warn"),
            ("delta 이벤트", "version 이 건너뛰면 STALE 로 버려진\n변경이 유실 (문서 04 오해 3)", "(해석)", "warn")]
    for i, (a, b, c, k) in enumerate(rows):
        y = 156 + i * 100
        box(d, f"r{i}a", 40, y, 440, 90, a, None, "note")
        box(d, f"r{i}b", 490, y, 440, 90, b, None, k)
        box(d, f"r{i}c", 940, y, 380, 90, c, None, "note")
    d.save()


def side_effect():
    d = Diagram("blog05-side-effect", 1360, 640, "부수 효과 — DB 안이면 한 트랜잭션, DB 밖이면 outbox 또는 멱등 키",
                "알림 · 적립 같은 부수 효과를 어디서 일으키느냐", out=OUT)
    d.text(40, 104, "DB 안 (포인트 적립 행 INSERT 등)", 16, P["ink"], weight=700)
    chain(d, "i", 134, 110, [
        ("BEGIN", "inbox INSERT\n상태 반영 + 적립 행 INSERT", "a"),
        ("COMMIT 또는 ROLLBACK", "셋이 함께 커밋되거나 함께 롤백된다", "ok"),
        ("inbox 판정 = \"한 번\"", "재전달은 DUPLICATE 로 걸러진다", "ok")], w=380, gap=70, labels=["", ""])
    d.text(40, 280, "DB 밖 (알림 API · 메일 · 다른 서비스 호출) — 롤백으로 되돌릴 수 없다", 16, P["ink"], weight=700)
    chain(d, "o", 310, 120, [
        ("커밋 전에 호출", "롤백되면 재전달에서\n또 나간다", "bad"),
        ("커밋 후에 호출", "호출 전에 죽으면\n유실이다", "bad"),
        ("outbox (해석)", "같은 트랜잭션에서 \"보낼 것\" 을 outbox\n에 INSERT, 별도 발송기가 읽어 보낸다", "ok"),
        ("멱등 키 (해석)", "상대가 지원하면 messageId 를\n키로 보내 재호출을 무해하게 한다", "ok")], w=290, gap=40)
    box(d, "n", 40, 460, 1280, 130, "inbox = 들어오는 쪽의 멱등, outbox = 나가는 쪽의 신뢰성 (해석 — 02.03 에서 확인)",
        "발송기는 at-least-once 이므로 상대 API 에 멱등 키를 준다. outbox 패턴은 02.03 에서 다룬다 — 아직 이 레슨 시점에는 없다\n"
        "@TransactionalEventListener(AFTER_COMMIT) 로 외부 호출을 빼면 커밋 후 호출 전 크래시에서 유실된다 (해석, Spring 문서로 확인하지 않음)", "note")
    d.save()


def retention():
    d = Diagram("blog05-retention", 1360, 560, "inbox 는 언제까지 보관하나",
                "inbox 는 무한히 자란다 — 지우는 배치가 필요하다. 기준은 해석이다", out=OUT)
    box(d, "a", 40, 110, 620, 210, "보관 기간 > 재전달 가능한 최대 지연", "브로커가 같은 메시지를 다시 전달할 수 있는\n최대 지연보다 길게 보관한다\n\n(해석) 재전달 가능 기간은 오프셋 보관 · 재처리(리플레이)\n정책 · DLT 재투입 주기에 달렸다 — 숫자를 외우지 않는다", "ok")
    box(d, "b", 700, 110, 620, 210, "보관 기간 < 재전달 가능한 최대 지연", "오래된 중복이 inbox 를 뚫는다\n\n그래도 상태는 version 이 지킨다 (실측: psql)\n— 지운 뒤 과거 version 을 upsert 해도 갱신 없음\n새는 것은 부수 효과를 version 판정과 무관하게\n일으키는 설계다", "warn")
    box(d, "n", 40, 350, 1280, 170, "구현 선택지 (해석)",
        "received_at 컬럼 + 주기 삭제 · 시간 파티션 테이블을 파티션 단위로 DROP\n"
        "PK 인덱스가 계속 커지므로 키를 짧게(해시 · 정수) 가져간다\n\n"
        "inbox 가 비어 있어도 < 이고 부수 효과를 APPLIED 일 때만 일으키는 규칙을 지키면, 이미 반영된 이벤트의 재전달은 STALE 이라 부수 효과가 나가지 않는다 (실측: psql 2026-10-13)", "note")
    d.save()


if __name__ == "__main__":
    for f in (outcomes, holes, version_only, side_effect, retention):
        f()
    finish()
