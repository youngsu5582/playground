#!/usr/bin/env python3
"""01.05 docs 그림. 실행: python3 -I docs/diagrams/draw.py (레슨 폴더에서)"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[4] / "tools"))
from diagram import Diagram, P, finish  # noqa: E402

OUT = pathlib.Path(__file__).parent


def dup_order_paths():
    d = Diagram("dup-order-paths", 1440, 800, "중복과 역전이 생기는 길 — 어디까지 브로커가 막고 어디부터 앱 몫인가",
                "Kafka 문서에서 확인한 것은 실선 카드, 앱 구조에서 이은 판단(해석)은 점선 카드", out=OUT)

    d.rect("pa", 40, 110, 680, 650, P["white"], P["line"], dashed=True)
    d.text(60, 124, "같은 메시지가 두 번 온다", 17, P["ink"], weight=700)
    d.card("d1", 65, 170, 630, 150, "1  프로듀서 재시도",
           "브로커 ack 를 못 받아 같은 레코드를 다시 보낸다\n"
           "idempotent producer 가 막는다 (프로듀서 ID + 시퀀스 번호)\n"
           "막는 범위 = 프로듀서가 로그에 쓰는 중복. 컨슈머 쪽 재전달은 아니다",
           bg=P["ok_bg"], stroke=P["green"], title_size=16, body_size=13)
    d.card("d2", 65, 345, 630, 190, "2  컨슈머가 처리한 뒤 오프셋 커밋 전에 죽음",
           "처리(DB 반영) -> 크래시 -> 오프셋은 옛 위치\n"
           "재시작하면 마지막 커밋 위치부터 다시 읽는다 = 같은 레코드 재처리\n"
           "Kafka 기본이 at-least-once 인 이유. 외부 시스템(DB)은\n"
           "브로커 트랜잭션 밖이라 앱이 거른다 -> inbox",
           bg=P["rs_bg"], stroke=P["orange"], title_size=16, body_size=13)
    d.card("d3", 65, 560, 630, 170, "3  리밸런스  (해석)",
           "처리는 끝났는데 커밋 전에 파티션이 다른 컨슈머로 넘어간다\n"
           "새 담당은 마지막 커밋 위치부터 읽는다 -> 2 와 같은 모양의 재처리\n"
           "(max.poll.interval.ms 초과 -> 컨슈머 실패 간주 -> 리밸런스는 문서)",
           bg=P["note_bg"], stroke=P["muted"], title_size=16, body_size=13, dashed=True)

    d.rect("pb", 760, 110, 640, 650, P["white"], P["line"], dashed=True)
    d.text(780, 124, "순서가 뒤집힌다", 17, P["ink"], weight=700)
    d.card("o1", 785, 170, 590, 120, "지켜지는 것 — 한 파티션 안",
           "같은 파티션의 레코드는 쓴 순서 그대로 읽힌다\n"
           "같은 키는 같은 파티션으로 간다 (같은 배송 건 = 같은 키)",
           bg=P["ok_bg"], stroke=P["green"], title_size=16, body_size=13)
    d.card("o2", 785, 315, 590, 130, "안 지켜지는 것 — 파티션 사이 · 키를 바꾸면",
           "문서의 보장은 토픽-파티션 단위다. 토픽 전체 순서는 없다\n"
           "배송 이벤트를 주문 키로 넣었다면 그 두 키 사이 순서는 없다",
           bg=P["rs_bg"], stroke=P["orange"], title_size=16, body_size=13)
    d.card("o3", 785, 470, 590, 120, "재시도 + in-flight 여러 개",
           "idempotence 가 꺼져 있고 max.in.flight > 1 이면 재시도로\n"
           "순서가 바뀔 수 있다. idempotence 가 켜져 있으면(기본) 보존",
           bg=P["rs_bg"], stroke=P["orange"], title_size=16, body_size=13)
    d.card("o4", 785, 615, 590, 120, "앱이 만드는 역전  (해석)",
           "컨슈머가 레코드를 스레드 풀로 병렬 처리 · 재시도 큐로 돌린 레코드 ·\n"
           "여러 생산자가 한 키에 쓰는 경우 -> 도착 순서 = 처리 순서가 아니다",
           bg=P["note_bg"], stroke=P["muted"], title_size=16, body_size=13, dashed=True)
    d.save()


if __name__ == "__main__":
    dup_order_paths()
    finish()
