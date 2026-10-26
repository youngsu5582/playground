#!/usr/bin/env python3
"""01 트랙 블로그판 06 (outbox) 그림. 실행: python3 -I docs/diagrams/draw_blog_t06.py (트랙 폴더에서)"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from blog_common import Diagram, P, finish, tw, kc, vchain, hchain, sequence, matrix, new, card_h, ARROW  # noqa: E402


def dual_lost():
    d = sequence("blog-t06-dual-lost", "경우 1 — 커밋 후 발행 전에 앱이 죽는다",
                 "DB 커밋 → 발행 순서. 유실",
                 [("앱 (주문 서비스)", "a"), ("DB", "ok"), ("브로커 (Kafka)", "b")],
                 [("msg", 0, 1, "1  DB 커밋 성공 (주문 저장됨)", "ok"),
                  ("note", 0, "2  앱 크래시 / 브로커 장애", "bad"),
                  ("note", 2, "3  메시지는 나가지 않는다", "bad")],
                 w=1200, pitch=80,
                 bottom_note=("결과: DB 에는 있고 이벤트는 영영 없다 (유실)", "후속 시스템(정산 · 알림)은 이 주문을 영영 모른다", "bad"))
    d.save()


def dual_ghost():
    d = sequence("blog-t06-dual-ghost", "경우 2 — 발행 후 커밋이 실패한다",
                 "발행 → DB 커밋 순서. 유령 이벤트",
                 [("앱 (주문 서비스)", "a"), ("DB", "ok"), ("브로커 (Kafka)", "b")],
                 [("msg", 0, 2, "1  메시지 발행 성공 (소비자가 받음)", "b"),
                  ("msg", 0, 1, "2  DB 커밋 실패 / 롤백", "bad"),
                  ("note", 1, "3  주문은 없다", "bad")],
                 w=1200, pitch=80,
                 bottom_note=("결과: 존재하지 않는 사건이 퍼진다 (유령 이벤트)", "롤백된 주문의 알림이 나간 건 — 두 시스템은 하나의 커밋으로 묶이지 않는다", "bad"))
    d.save()


def outbox():
    d = hchain("blog-t06-outbox", "outbox — 발행할 것을 같은 트랜잭션에 DB 행으로 쓴다",
               "원자성은 DB 한 곳에서만 요구하고, 발행은 재시도 가능한 일로 바꾼다",
               [("DB 한 트랜잭션", "UPDATE orders\nINSERT outbox\nCOMMIT\n둘 다 남거나 둘 다 없다", "ok"),
                ("릴레이 (별도 프로세스)", "outbox 행을 읽어\n브로커에 발행한다\n폴링 또는 CDC", "a"),
                ("Kafka", "key = aggregate_id\n같은 키는 같은 파티션", "b"),
                ("소비자", "at-least-once 라\n멱등 처리 (inbox · version)", "warn")],
               labels=("읽는다", "발행", "전달"), gap=90, h=170, top=120, extra=140)
    d.card("n", 40, 360, 1320, 110, "중복은 어디서 생기나",
           "릴레이가 발행한 뒤 \"발행함\" 표시 전에 죽으면 다음에 같은 행을 또 발행한다 → 전달은 at-least-once\n그래서 outbox 행의 id 가 곧 소비자가 거르는 messageId 다 (01.05 문서 03 inbox)",
           bg=P["note_bg"], stroke=P["line"], title_size=16, body_size=14)
    d.save()


def polling():
    d = new("blog-t06-polling", 1400, 540, "폴링 릴레이 둘 — SKIP LOCKED 는 기다리지 않고 다음 행을 집는다",
            "(실측: psql 2026-10-13, PostgreSQL 16) 일반 테이블 outbox_demo 6행 — 릴레이 A 가 트랜잭션을 연 채 4초 쉬는 동안")
    for i in range(6):
        bg, st = (P["as_bg"], P["front"]) if i < 2 else ((P["ok_bg"], P["green"]) if i < 4 else (P["note_bg"], P["line"]))
        d.pill(f"r{i}", 40 + i * 120, 110, 100, 50, f"행 {i + 1}", bg, st, size=15)
    d.card("A", 40, 200, 420, 130, "릴레이 A",
           "LIMIT 2 FOR UPDATE SKIP LOCKED\n→ 1 · 2 번을 잡았다\n트랜잭션을 연 채 4초 쉰다",
           bg=P["as_bg"], stroke=P["front"], title_size=16, body_size=14)
    d.card("B", 490, 200, 420, 130, "릴레이 B  (SKIP LOCKED)",
           "같은 쿼리를 보냈다\n→ 기다리지 않고 3 · 4 번을 받았다",
           bg=P["ok_bg"], stroke=P["green"], title_size=16, body_size=14)
    d.card("B2", 940, 200, 420, 130, "릴레이 B2  (FOR UPDATE 만)",
           "lock_timeout = 1s 에서\ncanceling statement due to lock timeout\n(while locking tuple (0,1))\n— A 가 쥔 동안 줄을 선다",
           bg=P["bad_bg"], stroke=P["red"], title_size=16, body_size=14)
    d.arrow([(150, 200), (150, 164)], P["front"], "1 · 2 를 잡는다", label_at=(240, 182))
    d.arrow([(520, 200), (520, 182), (390, 182), (390, 164)], P["green"], "3 · 4 를 받는다", label_at=(470, 182))
    d.card("c", 40, 370, 1320, 130, "이것이 폴링 릴레이에 주는 것",
           "발행하는 동안 행 락이 유지된다 — SELECT · 발행 · UPDATE · COMMIT 이 한 트랜잭션이므로 브로커가 느리면 락도 길다\n릴레이가 죽으면 트랜잭션이 롤백되어 행이 다시 미발행이 된다 — 발행 후 표시 전 죽음 = 중복 발행\nB 가 3 · 4 번을 A 의 1 · 2 번보다 먼저 커밋할 수 있다 → 순서가 깨질 수 있다 (아래 그림)",
           bg=P["note_bg"], stroke=P["line"], title_size=16, body_size=14)
    d.save()


def order_flip():
    d = sequence("blog-t06-order-flip", "릴레이가 여럿이면 순서가 뒤집힌다 (해석)",
                 "실측은 \"다른 릴레이가 다른 행을 동시에 잡는다\" 까지다 — 같은 aggregate_id 의 두 이벤트 e1 · e2 로 그린 예시",
                 [("릴레이 A", "a"), ("릴레이 B", "b"), ("브로커", "ok")],
                 [("note", 0, "e1 을 집는다", "a"),
                  ("note", 1, "e2 를 집는다", "b"),
                  ("msg", 1, 2, "B 가 먼저 발행 · 표시 · 커밋 (e2)", "bad"),
                  ("msg", 0, 2, "A 가 나중에 (e1)", "bad")],
                 w=1200, pitch=80,
                 bottom_note=("브로커에는 e2, e1 순서로 쌓인다", "대응 (해석): 릴레이를 하나로 두거나, 릴레이마다 aggregate_id 해시 범위를 맡겨 같은 키는 한 릴레이만 읽게 한다", "warn"))
    d.save()


def cursor_miss():
    d = sequence("blog-t06-cursor-miss", "id 커서로 읽는 폴러는 늦게 커밋된 행을 놓친다 (해석)",
                 "bigserial 번호는 INSERT 시점에 배정되고 커밋은 그 뒤에 일어난다 — 그림의 숫자는 예시",
                 [("트랜잭션 A", "a"), ("트랜잭션 B", "b"), ("폴러 (id > 마지막 본 id)", "warn")],
                 [("note", 0, "INSERT outbox → id 10 (커밋 전)", "a"),
                  ("note", 1, "INSERT outbox → id 11, COMMIT", "b"),
                  ("msg", 2, 1, "id 11 을 읽는다 → 커서 = 11", "warn"),
                  ("note", 0, "COMMIT (id 10)", "a"),
                  ("note", 2, "id > 11 만 읽으므로\nid 10 은 영영 못 본다", "bad")],
                 w=1200, pitch=78,
                 bottom_note=("대안: published_at IS NULL 플래그로 읽는다", "늦게 커밋된 행도 다음 폴링에서 잡힌다. 폴링 간격 = 발행 지연의 하한이다 (해석). 대신 인프라가 DB 하나라 단순하다", "ok"))
    d.save()


def cdc():
    d = hchain("blog-t06-cdc", "CDC — outbox 테이블이 아니라 WAL 의 변경을 읽는다",
               "PostgreSQL 논리 디코딩 (문서 49.2 · 49.6)",
               [("WAL", "커밋된 변경만\n디코딩 대상\n롤백된 트랜잭션은 제외", "ok"),
                ("복제 슬롯", "원 서버에서 일어난 순서대로\n재생할 수 있는 변경의 흐름\n연결과 무관하게 유지", "a"),
                ("릴레이", "예: Debezium\nOutbox Event Router", "b"),
                ("Kafka", "aggregateid 가\n메시지 키", "w")],
               labels=("커밋 순서", "읽는다", "발행"), gap=70, h=160, top=120, extra=210)
    d.card("dup", 40, 340, 650, 160, "그래도 중복은 있다 (문서 49.2)",
           "슬롯은 평소 각 변경을 한 번만 내보내지만\n크래시 뒤 슬롯 위치가 이전 LSN 으로 돌아가면 최근 변경이 다시 온다\n슬롯의 현재 위치는 체크포인트 때만 영속된다\n→ CDC 도 at-least-once — 중복 처리는 클라이언트 책임",
           bg=P["bad_bg"], stroke=P["red"], title_size=16, body_size=14)
    d.card("cost", 710, 340, 650, 160, "운영 비용 (문서 49.2)",
           "슬롯이 필요로 하는 WAL 과 카탈로그 행은 VACUUM · WAL 정리가\n지우지 못해 저장소를 먹는다\n극단적으로 트랜잭션 ID 랩어라운드를 막으려고 DB 가 멈출 수 있다\n— 쓰지 않는 슬롯은 지워야 한다 · 릴레이가 죽어 있는 동안 WAL 이 쌓인다",
           bg=P["todo_bg"], stroke=P["orange"], title_size=16, body_size=14)
    d.save()


def poll_vs_cdc():
    d = matrix("blog-t06-poll-vs-cdc", "폴링 vs CDC",
               "읽는 곳 · 순서 · 중복 · 운영",
               ["폴링", "CDC (논리 디코딩)"],
               [("읽는 곳", [("outbox 테이블 (쿼리)", "a"), ("WAL (슬롯)", "b")]),
                ("순서", [("릴레이가 여럿이면 깨질 수 있다 (실측)\n· 커서 주의", "warn"), ("커밋 순서 (문서 49.6)", "ok")]),
                ("중복", [("발행 후 표시 전에 죽으면", "warn"), ("슬롯이 이전 LSN 으로 돌아가면 (문서 49.2)", "warn")]),
                ("운영", [("락 · 폴링 부하,\noutbox 정리를 직접", "w"), ("슬롯이 WAL 을 붙잡는다 · 별도 컴포넌트", "w")])],
               w=1400, first_w=200, row_h=84, size=14)
    d.save()


def key_partition():
    d = new("blog-t06-key-partition", 1400, 560, "순서 — 같은 키는 같은 파티션, 파티션 안에서만 순서가 있다",
            "outbox 에서 순서가 필요한 이벤트는 같은 aggregate_id 를 메시지 키로 보낸다 (Debezium 도 aggregateid 를 키로 쓴다)")
    d.card("o", 40, 130, 380, 260, "outbox 행",
           "aggregate_id = 주문 A  이벤트 a1\naggregate_id = 주문 B  이벤트 b1\naggregate_id = 주문 A  이벤트 a2\naggregate_id = 주문 B  이벤트 b2\n\n(그림의 이름은 예시)",
           bg=P["ok_bg"], stroke=P["green"], title_size=16, body_size=14)
    d.card("p0", 600, 130, 760, 110, "파티션 x — 키: 주문 A", "a1 → a2   파티션 안에서는 순서가 지켜진다", bg=P["as_bg"], stroke=P["front"], title_size=16, body_size=14)
    d.card("p1", 600, 280, 760, 110, "파티션 y — 키: 주문 B", "b1 → b2", bg=P["bff_bg"], stroke=P["back"], title_size=16, body_size=14)
    d.arrow([(420, 200), (600, 185)], P["front"], "키 = 주문 A", label_at=(510, 168), start="o", end="p0")
    d.arrow([(420, 330), (600, 335)], P["back"], "키 = 주문 B", label_at=(510, 360), start="o", end="p1")
    d.card("n", 40, 430, 1320, 100, "outbox 가 정하는 것은 \"발행 순서\" 이고 사건의 순서가 아니다",
           "릴레이 순서가 흔들릴 수 있으므로 소비자는 version 으로 역전을 거른다 (01.05 문서 04) — outbox 행에 업무 version 을 넣어 두면 된다 (해석)",
           bg=P["note_bg"], stroke=P["line"], title_size=15, body_size=14)
    d.save()


def kafka_tx_scope():
    d = new("blog-t06-kafka-tx-scope", 1400, 520, "Kafka 트랜잭션은 Kafka 안만 묶는다",
            "DB 커밋과 발행 사이의 틈은 Kafka 트랜잭션으로 닫히지 않는다")
    d.card("k", 40, 120, 600, 220, "Kafka 트랜잭션의 범위",
           "여러 파티션 쓰기 · 오프셋의\n원자성\n\n외부 시스템은 협조가 필요하다\n(exactly-once 의 범위 — 01.05 문서 01)",
           bg=P["bff_bg"], stroke=P["back"], title_size=17, body_size=14)
    d.card("db", 760, 120, 600, 220, "DB — 별개 자원",
           "주문을 DB 에 쓰는 것은 그 트랜잭션 밖이다\nDB 커밋과 Kafka 커밋이 한 번에 성공 · 실패하게\n하는 문장이 Kafka 문서에 없다\n(이 문서에서 확인한 범위)",
           bg=P["ok_bg"], stroke=P["green"], title_size=17, body_size=14)
    d.arrow([(640, 230), (760, 230)], P["red"], "묶이지\n않는다", start="k", end="db", both=True)
    d.card("o", 40, 380, 1320, 100, "그래서 outbox 는 두 시스템을 묶지 않는다 (해석)",
           "원자성은 DB 한 곳에서만 요구하고, 나머지를 \"재시도 가능한 일\" 로 바꾼다\n소비 쪽 트랜잭션 + AfterRollbackProcessor 가 외부 DB 까지 exactly-once 가 아니라는 점은 01.05 문서 06",
           bg=P["note_bg"], stroke=P["line"], title_size=16, body_size=14)
    d.save()


if __name__ == "__main__":
    for f in (dual_lost, dual_ghost, outbox, polling, order_flip, cursor_miss, cdc, poll_vs_cdc, key_partition, kafka_tx_scope):
        f()
    finish()
