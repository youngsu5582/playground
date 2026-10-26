#!/usr/bin/env python3
"""01.05 블로그판 01 그림. 실행: python3 -I docs/diagrams/draw_blog01.py (레슨 폴더에서)"""
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
    d = Diagram("blog01-intro", 1360, 420, "도입: 처리는 끝났는데 오프셋을 저장하기 전에 죽었다",
                "재배포 · 리밸런스 직후 알림이 두 번 나가는 장애의 가장 흔한 모양", out=OUT)
    chain(d, "i", 130, 150, [
        ("1  레코드를 읽는다", "컨슈머가 poll 로 레코드를 받는다\n저장된 위치는 아직 옛 값", "a"),
        ("2  처리한다", "알림을 보내고 DB 에 반영한다\n처리는 성공했다", "ok"),
        ("3  저장 전에 죽는다", "오프셋 커밋 전에 프로세스가 끊긴다\n저장된 위치는 여전히 옛 값", "bad"),
        ("4  재시작한다", "마지막으로 저장된 위치부터\n다시 읽는다", "warn")],
        w=270, gap=60, labels=["처리 끝", "끊김", "재시작"])
    box(d, "n", 40, 310, 1280, 80, "로그에는 레코드가 한 번만 있다",
        "그런데 컨슈머는 같은 레코드를 두 번 읽었다 — 알림이 두 번 나간다. 브로커의 중복이 아니라 컨슈머의 재읽기다", "note")
    d.save()


def three_guarantees():
    d = Diagram("blog01-three", 1360, 400, "세 가지 전달 보장과 각각의 대가",
                "Kafka 문서 Message Delivery Semantics 가 나누는 세 가지", out=OUT)
    for i, (t, b, k) in enumerate([
            ("at-most-once", "메시지를 잃을 수 있지만\n다시 전달되지는 않는다\n\n대가: 유실", "warn"),
            ("at-least-once", "잃지 않지만\n다시 전달될 수 있다\n\n대가: 중복  (Kafka 의 기본 형태)", "bad"),
            ("exactly-once", "한 번만 처리된다\n\n대가: 협조가 필요하다\n(Kafka 안은 트랜잭션, 밖은 앱)", "ok")]):
        box(d, f"g{i}", 40 + i * 440, 120, 400, 200, t, b, k)
    d.text(40, 340, "문서는 문제를 발행(publish)의 보장과 소비(consume)의 보장으로 나눈다 — 중복은 양쪽 모두에서 생길 수 있다", 14, P["muted"])
    d.save()


def commit_order():
    d = Diagram("blog01-commit-order", 1360, 560, "오프셋을 언제 저장하나 — 순서가 보장을 정한다",
                "컨슈머의 위치(position)는 \"다음에 읽을 오프셋\" 하나의 정수다", out=OUT)
    d.text(40, 104, "위치를 먼저 저장하는 순서", 16, P["ink"], weight=700)
    chain(d, "u", 134, 130, [
        ("1  위치를 저장한다", "다음에 읽을 위치를 먼저 커밋", "a"),
        ("2  처리 중 죽는다", "저장은 됐고 처리는 못 했다", "bad"),
        ("3  재시작한다", "저장된 위치부터 읽는다\n그 메시지는 건너뛴다", "warn")],
        w=380, gap=70, labels=["처리 전", "재시작"])
    d.text(1280, 270, "at-most-once (유실)", 15, P["orange"], align="right", weight=700)
    d.text(40, 304, "처리를 먼저 하는 순서", 16, P["ink"], weight=700)
    chain(d, "l", 334, 130, [
        ("1  처리한다", "알림 · DB 반영을 먼저 끝낸다", "ok"),
        ("2  저장 전에 죽는다", "처리는 됐고 저장은 못 했다", "bad"),
        ("3  재시작한다", "마지막 저장 위치부터 읽는다\n처음 몇 건은 이미 처리된 것", "warn")],
        w=380, gap=70, labels=["저장 전", "재시작"])
    d.text(1280, 470, "at-least-once (중복)", 15, P["red"], align="right", weight=700)
    d.save()


def producer_retry():
    d = Diagram("blog01-producer-retry", 1360, 640, "발행 쪽 중복 — 프로듀서 재시도와 idempotent producer",
                "브로커 ack 를 못 받은 프로듀서가 같은 레코드를 다시 보낸다", out=OUT)
    d.text(40, 104, "0.11.0.0 이전, 또는 idempotence 가 꺼진 경우", 16, P["ink"], weight=700)
    chain(d, "p", 134, 140, [
        ("프로듀서가 보낸다", "레코드 R 을 전송", "a"),
        ("브로커는 썼다", "그런데 ack 가 프로듀서에\n닿지 못한다", "warn"),
        ("프로듀서가 재시도한다", "ack 를 못 받았으니\n같은 R 을 다시 보낸다", "a"),
        ("로그에 R 이 두 번", "재시도가 중복을 만든다", "bad")],
        w=290, gap=40, labels=None)
    d.text(40, 322, "idempotent producer (0.11.0.0 부터, enable.idempotence 기본 true)", 16, P["ink"], weight=700)
    chain(d, "q", 352, 140, [
        ("프로듀서가 보낸다", "브로커가 프로듀서에 ID 를 주고\n레코드마다 시퀀스 번호가 붙는다", "a"),
        ("ack 를 못 받아 재시도", "같은 ID · 같은 시퀀스 번호로\nR 을 다시 보낸다", "a"),
        ("브로커가 버린다", "이미 본 시퀀스 번호라\n중복을 버린다", "ok"),
        ("로그에 R 이 한 번", "프로듀서 세션이 로그에 쓰는\n중복만 막는다", "ok")],
        w=290, gap=40, labels=None)
    box(d, "n", 40, 530, 1280, 80, "막지 못하는 것",
        "앱이 같은 이벤트를 새로 두 번 send() 하면 시퀀스가 서로 다른 별개 레코드다 (해석) — 컨슈머의 재읽기도 막지 못한다", "note")
    d.save()


def eos_scope():
    d = Diagram("blog01-eos-scope", 1360, 560, "exactly-once 는 어디까지인가",
                "문서가 말하는 범위는 Kafka 안이고, 외부 시스템에는 협조가 필요하다", out=OUT)
    d.text(40, 104, "Kafka 안 — 토픽에서 읽고 토픽에 쓴다", 16, P["ink"], weight=700)
    chain(d, "k", 134, 110, [
        ("토픽 A", "입력 레코드", "a"),
        ("처리 + 쓰기", "Kafka Streams 또는\ntransactional producer", "ok"),
        ("토픽 B", "read_committed 컨슈머는\n커밋된 것만 읽는다", "ok")],
        w=380, gap=70, labels=["읽는다", "트랜잭션"])
    d.text(40, 280, "Kafka 밖 — DB · 알림 API 에 반영한다", 16, P["ink"], weight=700)
    chain(d, "x", 310, 130, [
        ("토픽", "at-least-once 로 받는다", "a"),
        ("컨슈머", "DB · 알림 API 에\n부수 효과를 낸다", "warn"),
        ("외부 시스템", "브로커 트랜잭션 밖이라\n\"협조가 필요하다\"", "bad")],
        w=380, gap=70, labels=["읽는다", "반영"])
    box(d, "n", 40, 470, 1280, 70, "문서의 해법과 이 레슨의 방향",
        "문서: 오프셋을 출력과 함께 저장 (Connect HDFS 예). (해석) DB 컨슈머의 현실적 형태 = at-least-once 로 받고 DB 쪽에서 멱등하게 처리", "note")
    d.save()


def acks():
    d = Diagram("blog01-acks", 1360, 460, "acks — 프로듀서가 기다리는 확인",
                "기본값은 all (Kafka 4.0 producer configs)", out=OUT)
    for i, (t, b, k) in enumerate([
            ("acks=0", "브로커 확인을 전혀 기다리지 않는다\n(retries 효과 없음, 오프셋은 늘 -1)\n\n잃는 경우: 보냈는지조차 모른다", "bad"),
            ("acks=1", "리더가 자기 로컬 로그에 쓰면 응답\n팔로워는 기다리지 않는다\n\n잃는 경우: 응답 뒤 복제 전에 리더가\n죽으면 \"the record will be lost\"", "warn"),
            ("acks=all  (기본)", "리더가 ISR 전체의 확인을 기다린다\nISR 에 복제본이 하나라도 살아 있는 한\n레코드는 사라지지 않는다 (가장 강한 보장)\n\n구멍: 다음 그림", "ok")]):
        box(d, f"a{i}", 40 + i * 440, 120, 400, 240, t, b, k)
    d.text(40, 390, "enable.idempotence(기본 true)가 acks=all 을 요구하므로 충돌하는 acks 를 명시하면 idempotence 가 꺼지거나 ConfigException 이다", 14, P["muted"])
    d.save()


def min_isr():
    d = Diagram("blog01-min-isr", 1360, 560, "acks=all 의 구멍과 min.insync.replicas",
                "acks=all 은 \"현재 ISR\" 전체를 기다린다 — ISR 이 리더 하나로 줄어 있다면?", out=OUT)
    d.text(40, 104, "min.insync.replicas = 1 (기본)", 16, P["ink"], weight=700)
    chain(d, "m", 134, 130, [
        ("ISR 이 리더 하나로 줄었다", "팔로워들이 ISR 에서 빠졌다", "warn"),
        ("acks=all 쓰기", "리더 하나의 확인으로 성공한다\n방어가 없다", "bad"),
        ("그 하나가 죽는다", "문서 Design: 2 복제본 토픽에서\n남은 하나가 죽으면 잃을 수 있다", "bad")],
        w=380, gap=70, labels=["쓴다", "장애"])
    d.text(40, 300, "min.insync.replicas = 2 · 복제 계수 3 · acks=all", 16, P["ink"], weight=700)
    chain(d, "n", 330, 130, [
        ("ISR 이 리더 하나로 줄었다", "ISR 이 최솟값 2 아래다", "warn"),
        ("acks=all 쓰기", "최소 2 개의 확인을 못 채운다\n프로듀서가 NotEnoughReplicas 또는\nNotEnoughReplicasAfterAppend", "ok"),
        ("파티션이 쓰기를 거부한다", "일관성을 위해 가용성을 내준다\n(거부를 앱이 처리해야 한다)", "ok")],
        w=380, gap=70, labels=["쓴다", "거부"])
    d.text(40, 490, "복제 계수 3 · min.insync.replicas=2 · acks=all 이면 과반이 쓴 뒤에야 성공이다 (Broker configs 의 예)", 14, P["muted"])
    d.save()


def leader_election():
    d = Diagram("blog01-leader-election", 1360, 540, "리더 선출과 유실 — unclean.leader.election.enable",
                "커밋된 메시지는 \"ISR 의 모든 복제본이 자기 로그에 적용한\" 메시지다", out=OUT)
    box(d, "a", 40, 110, 1280, 110, "리더가 죽으면 — ISR 의 남은 멤버 중 하나가 새 리더가 된다",
        "ISR 멤버는 커밋된 메시지를 전부 갖고 있으니 선출로는 커밋된 메시지를 잃지 않는다\n"
        "acks=1 로 리더만 확인한 레코드는 커밋이 아니라서 선출 뒤 사라질 수 있다 (해석)", "ok")
    d.text(40, 250, "ISR 이 전멸했다면 — 두 갈래", 16, P["ink"], weight=700)
    box(d, "b", 40, 285, 620, 200, "unclean.leader.election.enable = false  (기본)",
        "ISR 복제본이 돌아오길 기다린다\n(0.11.0.0 이후 기본, 가용성을 희생)\n\n가용성을 내주는 대신\n커밋된 메시지는 지켜진다", "ok")
    box(d, "c", 700, 285, 620, 200, "unclean.leader.election.enable = true",
        "ISR 밖의 복제본을 최후의 수단으로 리더로 뽑는다\n가장 먼저 돌아온 복제본이 뒤처졌더라도 리더가 된다\n\n그 복제본에 없는 커밋 메시지가 유실된다\n(일관성 대신 가동 시간을 고르는 설정)", "bad")
    d.save()


def poll_interval():
    d = Diagram("blog01-poll-interval", 1360, 480, "처리가 길어지면 정상 동작인데 중복이 난다",
                "max.poll.interval.ms 기본 300000 (5분) · max.poll.records 기본 500 (Consumer configs)", out=OUT)
    chain(d, "r", 120, 150, [
        ("1  poll() 로 받는다", "한 번에 최대 500 건\n(max.poll.records)", "a"),
        ("2  처리가 느리다", "레코드당 처리가 길어\n다음 poll() 이 늦어진다", "warn"),
        ("3  기본 5분을 넘긴다", "poll() 간격이 max.poll.interval.ms\n를 넘으면 실패한 것으로 간주", "bad"),
        ("4  리밸런스", "파티션이 다른 멤버에게 간다\n마지막 커밋 위치부터 읽는다", "warn")],
        w=270, gap=60, labels=["", "", ""])
    box(d, "n", 40, 310, 1280, 130, "(해석) 처리 중이던 레코드가 다른 컨슈머에게 다시 간다 = 재처리",
        "에러도 장애도 아닌 정상 동작이다. 확인은 리밸런스 로그와 처리 시간 · 배치 크기(max.poll.records)\n"
        "대응: 배치를 줄이거나 처리를 가볍게 한다 (상한을 늘리면 실패 감지가 늦어지는 대가 — 해석). 어차피 재전달은 오므로 inbox 로 멱등하게 둔다", "note")
    d.save()


if __name__ == "__main__":
    for f in (intro, three_guarantees, commit_order, producer_retry, eos_scope, acks, min_isr, leader_election, poll_interval):
        f()
    finish()
