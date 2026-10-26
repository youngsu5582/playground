#!/usr/bin/env python3
"""01.05 블로그판 06 그림. 실행: python3 -I docs/diagrams/draw_blog06.py (레슨 폴더에서)"""
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



def listener_twice():
    d = Diagram("blog06-listener-twice", 1360, 520, "@KafkaListener 가 같은 레코드로 두 번 호출되는 길",
                "리스너는 같은 레코드를 여러 번 받는다고 가정하고 짠다", out=OUT)
    items = [("처리 후 커밋 전 크래시 · 리밸런스", "마지막 커밋 위치부터 다시 읽는다\n(문서 01)", "warn"),
             ("BATCH 모드에서 배치 중간 실패", "배치 전체가 재전달된다", "warn"),
             ("에러 핸들러의 재시도", "DefaultErrorHandler 기본 최초 + 9 회\nseek 로 같은 레코드를 다시 호출", "warn"),
             ("프로듀서가 같은 이벤트를 두 번 발행 (해석)", "브로커 입장에선 서로 다른 레코드", "note")]
    for i, (t, b, k) in enumerate(items):
        box(d, f"w{i}", 40 + (i % 2) * 660, 110 + (i // 2) * 170, 620, 150, t, b, k, dashed=(k == "note"))
    d.text(40, 460, "에러 핸들러의 재시도마다 inbox 판정이 다시 돈다 — 반영이 실패한 시도는 롤백되어 inbox 에 남지 않는다 (문서 03: 한 트랜잭션)", 14, P["muted"])
    d.save()


def ackmode():
    d = Diagram("blog06-ackmode", 1360, 560, "오프셋 커밋 시점 — 컨테이너 AckMode (트랜잭션을 쓰지 않을 때)",
                "Spring Kafka 레퍼런스 · Message Listener Containers (2026-10-13 조회)", out=OUT)
    rows = [("BATCH  (기본)", "poll 이 돌려준 레코드를 모두 처리한 뒤 커밋", "ok"),
            ("RECORD", "레코드마다 리스너가 반환될 때 커밋", "a"),
            ("TIME · COUNT · COUNT_TIME", "배치 처리 뒤 시간 · 개수 조건", "a"),
            ("MANUAL", "리스너가 acknowledge() 를 부르면 BATCH 처럼", "a"),
            ("MANUAL_IMMEDIATE", "acknowledge() 호출 즉시 커밋", "a")]
    for i, (t, b, k) in enumerate(rows):
        y = 110 + i * 70
        box(d, f"m{i}", 40, y, 440, 60, t, None, k)
        box(d, f"n{i}", 500, y, 820, 60, b, None, "note")
    d.text(40, 480, "enable.auto.commit: 2.3 부터 프레임워크가 false 로 둔다 (\"명시적으로 설정하지 않는 한\") — 커밋은 컨테이너가 한다", 14, P["ink"])
    d.text(40, 506, "BATCH 에서 배치 중간에 죽으면 배치 전체가 재전달된다. RECORD 는 중복을 줄이지만 커밋이 잦다 (해석 — 비용은 측정하지 않았다)", 14, P["muted"])
    d.save()


def error_handler():
    d = Diagram("blog06-error-handler", 1360, 640, "리스너가 예외를 던지면 — DefaultErrorHandler",
                "기본 백오프 FixedBackOff(0L, 9) — 간격 0, 재시도 9회 (Spring Kafka · Handling Exceptions)", out=OUT)
    chain(d, "e", 120, 140, [
        ("리스너가 예외를 던진다", "컨테이너가 에러 핸들러를 부른다", "bad"),
        ("보류 중인 오프셋 커밋", "문서: 에러 핸들러를 부르기 전에\n먼저 한다", "a"),
        ("seek 로 되감아 재호출", "같은 레코드를 같은 리스너가\n다시 받는다", "warn"),
        ("최초 1회 + 재시도 9회", "= 열 번 (문서의 (0L, 9) 에서\n센 계산이다)", "warn")], w=290, gap=40)
    box(d, "r", 40, 300, 620, 140, "열 번을 넘기면 recoverer", "기본 복구: 레코드를 ERROR 로그로 남기고 건너뛴다\nDeadLetterPublishingRecoverer 로 바꾸면 DLT 로 간다\n(기본 대상 <원본토픽>-dlt, 같은 파티션 — DLT 파티션 수가 원본 이상)", "ok")
    box(d, "f", 700, 300, 620, 140, "fatal 예외는 재시도 없이 첫 실패에서 복구", "DeserializationException ·\nMessageConversionException 등\nError(예: OutOfMemoryError)는 이 핸들러를 거치지 않고\n컨슈머가 종료된다", "bad")
    box(d, "b", 40, 470, 1280, 130, "배치 리스너 · 시도 횟수",
        "배치 리스너는 배치 전체가 재처리된다 — 재전달될 때 레코드 수 · 순서가 같다는 보장이 없다고 문서가 쓴다\n"
        "KafkaHeaders.DELIVERY_ATTEMPT 로 시도 횟수를 알 수 있지만 컨테이너 속성 deliveryAttemptHeader=true 로 켜야 한다 (기본 꺼짐)", "note")
    d.save()


def config_mistakes():
    d = Diagram("blog06-mistakes", 1360, 520, "흔한 구성 실수 네 가지 (해석)",
                "리스너 구성이 inbox · 한 트랜잭션 · 멱등 설계를 무너뜨리는 곳", out=OUT)
    items = [("리스너 안에서 예외를 삼킨다", "컨테이너는 성공으로 보고 커밋한다\n반영이 실패해도 이벤트가 사라진다"),
             ("REQUIRES_NEW 로 inbox 만 별도 저장", "문서 03 의 \"따로 커밋\" (독립된 물리 트랜잭션이라\n따로 커밋/롤백 — Spring 전파 문서)"),
             ("재시도 횟수만큼 외부 호출이 나간다", "부수 효과는 inbox 밖 → outbox · 멱등 키 (문서 05)"),
             ("복구기가 DLT 로 보낸 메시지를 나중에 재투입", "보관 기간이 지났으면 inbox 를 통과한다 (문서 05)")]
    for i, (t, b) in enumerate(items):
        box(d, f"x{i}", 40 + (i % 2) * 660, 110 + (i // 2) * 190, 620, 170, t, b, "bad")
    d.save()


def mysql_rows():
    d = Diagram("blog06-mysql-rows", 1360, 560, "MySQL ON DUPLICATE KEY UPDATE 의 영향 행 수 — 행마다",
                "PostgreSQL 은 \"삽입 또는 갱신 = 1\" — MySQL 은 갱신이 2 인 것이 함정이다 (MySQL 8.0 Reference Manual)", out=OUT)
    for i, (t, b, k) in enumerate([("새 행으로 삽입", "영향 행 수 1", "ok"), ("기존 행 갱신", "영향 행 수 2", "warn"), ("기존 행을 현재 값으로 \"설정\"\n(값이 안 바뀜)", "영향 행 수 0", "a")]):
        box(d, f"r{i}", 40 + i * 440, 110, 400, 150, t, b, k)
    box(d, "c", 40, 290, 1280, 90, "CLIENT_FOUND_ROWS 플래그로 연결하면", "값이 안 바뀐 경우가 0 이 아니라 1 이다", "note")
    box(d, "n", 40, 410, 1280, 120, "판정 코드는 드라이버 설정과 함께 직접 확인해야 한다 (확인하지 않음)",
        "문서 규칙대로라면 STALE 은 0 이고 APPLIED 는 갱신 2 · 최초 삽입 1 이다 (해석)\n그래서 \"영향 행 수 1 = 갱신\" 이라고 읽으면 틀린다 — 1 은 삽입이다", "bad")
    d.save()


def mysql_deadlock():
    d = Diagram("blog06-mysql-lock", 1360, 560, "MySQL 에서 같은 키를 동시에 INSERT 하면 (InnoDB Locks Set 의 3세션 예)",
                "PostgreSQL 은 같은 상황에서 transactionid 로 기다리다 결론이 난다 (실측: 문서 03 · Q09)", out=OUT)
    chain(d, "s", 110, 150, [
        ("세션 1: INSERT 후 ROLLBACK", "같은 키를 먼저 넣는다\n첫 세션이 롤백한다", "a"),
        ("세션 2 · 3: 같은 키 INSERT", "중복 키 에러 → 중복 인덱스 레코드에\n공유 락이 잡힌다", "warn"),
        ("롤백 뒤 배타 락 경쟁", "나머지가 공유 락을 쥔 채 서로\n배타 락을 기다린다 → 데드락", "bad")], w=380, gap=70, labels=["", ""])
    box(d, "o", 40, 300, 620, 130, "INSERT … ON DUPLICATE KEY UPDATE", "중복 시 공유가 아니라 배타 락\n기본키 중복이면 배타 인덱스 레코드 락\n유니크 키 중복이면 배타 next-key 락", "note")
    box(d, "i", 700, 300, 620, 130, "(해석 — 이 레슨에서 MySQL 을 실행하지 않았다)", "inbox 처럼 같은 키를 동시에 넣는 곳에서는\n데드락 처리(재시도)가 필요하다는 뜻으로 읽을 수 있다\nInnoDB 는 한쪽을 롤백하므로 재시도가 필요하다", "note", dashed=True)
    d.text(40, 460, "기본 격리수준이 InnoDB 는 REPEATABLE READ (01.01 문서 01) — 위 락 동작은 격리수준에 따라 달라질 수 있다 (해석 — 문서의 예는 격리수준별로 나누지 않았다)", 13, P["muted"])
    d.save()


def mysql_cond():
    d = Diagram("blog06-mysql-cond", 1360, 600, "MySQL 에서 version 조건부 upsert 를 짜려면 (해석 — 문서 예시 아님)",
                "ON DUPLICATE KEY UPDATE 에는 WHERE 가 없다 — 구문에 assignment 목록만 있다", out=OUT)
    d.card("sql", 40, 110, 700, 200, "값 표현식으로 조건을 만든다", "INSERT INTO shipment (id, version, status) VALUES (?, ?, ?) AS new\nON DUPLICATE KEY UPDATE\n  status  = IF(new.version > version, new.status,  status),\n  version = IF(new.version > version, new.version, version);",
           bg=P["note_bg"], stroke=P["ink"], title_size=15, body_size=13, mono_body=True)
    box(d, "a", 780, 110, 540, 200, "주의 (해석)", "같은 문장의 대입이 왼쪽에서 오른쪽으로 평가돼\n앞에서 바꾼 version 을 뒤의 조건이 보게 된다면\n틀린다 — 대입 순서 · 평가를 직접 확인해야 한다", "warn")
    box(d, "b", 40, 340, 700, 110, "STALE 이면", "모든 열이 현재 값으로 설정돼 영향 행 수가 0 일 것이라고\n읽을 수 있다 (해석 — 문서의 \"현재 값으로 설정 = 0\" 규칙에서 이은 것)", "note")
    box(d, "c", 780, 340, 540, 110, "VALUES() 와 별칭", "VALUES() 로 새 행을 참조하는 방식은 8.0.20 부터\ndeprecated, 행 별칭(AS new)은 8.0.19 부터 (문서)", "note")
    d.text(40, 480, "UNIQUE 인덱스가 여럿이고 여러 행이 매치되면 한 행만 갱신된다 — 문서도 여러 unique 인덱스 테이블에는 이 구문을 피하라고 한다", 14, P["muted"])
    d.save()


if __name__ == "__main__":
    for f in (listener_twice, ackmode, error_handler, config_mistakes, mysql_rows, mysql_deadlock, mysql_cond):
        f()
    finish()
