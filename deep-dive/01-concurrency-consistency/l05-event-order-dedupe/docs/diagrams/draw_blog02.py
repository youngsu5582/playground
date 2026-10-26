#!/usr/bin/env python3
"""01.05 블로그판 02 그림. 실행: python3 -I docs/diagrams/draw_blog02.py (레슨 폴더에서)"""
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



def intro():
    d = Diagram("blog02-intro", 1360, 470, "도입: 일어난 순서와 받은 순서가 다르다",
                "한 배송 건의 이벤트 — 늦게 온 과거 이벤트가 상태를 과거로 되돌린다", out=OUT)
    d.text(40, 104, "배송에서 실제로 일어난 순서", 16, P["ink"], weight=700)
    chain(d, "t", 134, 90, [("v1  접수", "", "a"), ("v2  포장", "", "a"), ("v3  출고", "", "a")], w=300, gap=110, labels=["다음", "다음"])
    d.text(40, 254, "컨슈머가 받아 처리한 순서", 16, P["ink"], weight=700)
    chain(d, "r", 284, 90, [("v1  접수", "", "a"), ("v3  출고", "", "ok"), ("v2  포장  (늦게 도착)", "", "bad")], w=300, gap=110, labels=["처리", "처리"])
    box(d, "n", 40, 394, 1280, 56, "마지막에 처리한 것이 이긴다 — 최종 상태가 과거(포장)가 된다. 에러도 경고도 없고 데이터만 틀린다", None, "note")
    d.save()


def partition_order():
    d = Diagram("blog02-partition", 1360, 500, "Kafka 가 보장하는 것 — 한 토픽-파티션 안의 순서",
                "컨슈머는 파티션 안의 이벤트를 쓰인 순서 그대로 읽는다. 파티션 사이 순서를 보장한다는 문서는 확인하지 못했다", out=OUT)
    for lane, (name, recs, y, k) in enumerate([("파티션 0", ["a1", "a2", "a3"], 130, "ok"), ("파티션 1", ["b1", "b2", "b3"], 270, "ok")]):
        d.text(40, y + 28, name, 16, P["ink"], weight=700)
        for i, r in enumerate(recs):
            d.pill(f"p{lane}{i}", 190 + i * 150, y, 120, 70, r, P["ok_bg"], P["green"], size=18)
            if i:
                d.arrow([(190 + (i - 1) * 150 + 120, y + 35), (190 + i * 150, y + 35)], P["green"])
        d.arrow([(190 + 2 * 150 + 120, y + 35), (740, y + 35)], P["green"], label="쓰인 순서\n그대로 읽는다", label_size=12)
        box(d, f"c{lane}", 750, y - 5, 250, 80, f"컨슈머 (파티션 {lane})", "한 파티션은 구독 그룹에서\n한 번에 한 컨슈머만 소비", "a")
    box(d, "x", 1040, 160, 280, 150, "파티션 사이", "a1 과 b1 중 무엇이 먼저인가는\n정해져 있지 않다\n토픽 전체의 순서는 없다", "warn")
    box(d, "n", 40, 400, 1280, 70, "같은 이벤트 키는 같은 파티션으로 간다 (키를 해시해 파티션을 정한다)",
        "그래서 \"같은 키의 순서\" 는 지켜진다. 로그 컴팩션은 메시지를 지울 뿐 순서를 바꾸지 않는다", "note")
    d.save()


def key_choice():
    d = Diagram("blog02-key", 1360, 520, "키를 무엇으로 잡느냐가 순서의 단위를 정한다",
                "한 주문에 배송이 둘일 때 — 해석: 필요한 순서 단위에 키를 맞춘다", out=OUT)
    box(d, "a", 40, 110, 620, 220, "키 = shipmentId", "배송 S1 의 이벤트 → 한 파티션에 쓰인 순서대로\n배송 S2 의 이벤트 → (같거나) 다른 파티션\n\n한 배송 건 안의 순서가 보존된다", "ok")
    box(d, "b", 700, 110, 620, 220, "키 = orderId  (주문 id)", "같은 주문의 두 배송 이벤트가 한 파티션에 섞여 있다\n한 shipmentId 의 순서는 그 안에서 보존되므로\n대개 문제가 없다\n\n하지만 다른 주문의 배송 사이는 순서가 없다", "warn")
    box(d, "n", 40, 360, 1280, 110, "정말 필요한 순서 단위가 무엇인지가 먼저다 (해석)",
        "배송 건 하나의 순서가 필요하다면 키 또는 version 의 단위를 shipmentId 로 둔다 — version 도 같은 배송 건 안의 순번으로 매긴다\n"
        "파티션을 늘리면 같은 키가 다른 파티션으로 갈 수 있어 순서가 중요한 토픽의 증설은 위험하다 (해석)", "note")
    d.save()


def retry_reorder():
    d = Diagram("blog02-retry", 1360, 560, "프로듀서 재시도가 순서를 바꾸는 경우",
                "max.in.flight.requests.per.connection 기본 5 · retries 가 켜져 있을 때 (Kafka 4.0 producer configs)", out=OUT)
    d.text(40, 104, "enable.idempotence 가 꺼져 있고 in-flight > 1", 16, P["ink"], weight=700)
    chain(d, "x", 134, 130, [
        ("배치 1, 2 를 연달아 전송", "응답을 기다리지 않고\n두 요청이 날아가 있다", "a"),
        ("배치 1 만 실패한다", "배치 2 는 먼저 로그에 쓰인다", "warn"),
        ("배치 1 을 재시도한다", "재시도된 1 이 2 뒤에 쓰인다", "bad"),
        ("로그: 2, 1", "프로듀서가 보낸 순서와\n다르게 쓰였다", "bad")], w=290, gap=40)
    d.text(40, 300, "idempotence 를 켜거나 재시도를 끈 경우", 16, P["ink"], weight=700)
    chain(d, "y", 330, 100, [
        ("재시도해도", "순서가 보존된다고 문서가 쓴다", "ok"),
        ("idempotence 는 기본 켜짐", "(enable.idempotence 기본 true)", "ok")], w=620, gap=40)
    box(d, "n", 40, 460, 1280, 70, "문서가 보장을 말하는 것은 프로듀서 재시도로 인한 재정렬이다",
        "앱의 병렬 처리 · 재시도 큐 같은 다른 경로는 별개다 (다음 그림)", "note")
    d.save()


def app_made():
    d = Diagram("blog02-app-made", 1360, 470, "앱이 만드는 역전 세 가지 (해석)",
                "로그에 쓰인 순서가 곧 사건의 순서는 아니고, 읽는 순서가 곧 처리 순서도 아니다", out=OUT)
    for i, (t, b) in enumerate([
            ("스레드 풀로 병렬 처리", "읽는 순서는 보존돼도\n처리 완료 순서는 뒤집힌다\n(느린 레코드가 뒤에 끝난다)"),
            ("재시도 큐 · 지연 토픽 · 수동 재처리", "실패한 이벤트를 다른 토픽에 돌렸다가\n다시 흘리면 뒤에 쓰인 이벤트가\n먼저 처리된다"),
            ("리밸런스 중 겹침", "이전 담당 컨슈머가 처리 중인 레코드와\n새 담당이 읽기 시작한 뒤 레코드가\n잠깐 겹친다 — 같은 키가 순서 없이")]):
        bg, st = KC["note"]
        d.card(f"k{i}", 40 + i * 440, 120, 400, 190, t, b, bg=bg, stroke=st, title_size=16, body_size=14, dashed=True)
    box(d, "n", 40, 340, 1280, 90, "여러 생산자가 같은 키에 쓰거나, 이벤트 소스가 Kafka 가 아니면 (해석)",
        "각자의 전송 시각 순서가 로그에 쓰인 순서와 다를 수 있다. 웹훅 · 외부 폴링은 외부 시스템의 전송 순서에 달렸다 — \"도착 순서\" 를 믿지 않는 것이 출발점", "note")
    d.save()


if __name__ == "__main__":
    for f in (intro, partition_order, key_choice, retry_reorder, app_made):
        f()
    finish()
