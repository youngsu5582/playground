#!/usr/bin/env python3
"""01.05 블로그판 03 그림. 실행: python3 -I docs/diagrams/draw_blog03.py (레슨 폴더에서)"""
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



def inbox_flow():
    d = Diagram("blog03-inbox-flow", 1360, 470, "inbox 패턴 — 넣어 보고, 영향 행 수로 갈린다",
                "CREATE TABLE inbox (message_id text PRIMARY KEY)  — 처리한 메시지의 신원", out=OUT)
    box(d, "m", 40, 150, 270, 120, "메시지 도착", "messageId = m-4", "a")
    box(d, "q", 400, 150, 380, 120, "INSERT INTO inbox\nVALUES (?) ON CONFLICT DO NOTHING", "확인과 삽입을 한 문장이\n유니크 인덱스로 원자적으로 한다", "warn")
    box(d, "y", 890, 100, 430, 110, "실제로 넣었다 → 처음 보는 메시지", "처리한다 (상태 반영)", "ok")
    box(d, "n", 890, 240, 430, 110, "충돌해서 안 넣었다 → 이미 처리한 메시지", "DUPLICATE — 건너뛴다", "bad")
    d.arrow([(310, 210), (400, 210)], P["muted"], start="m", end="q")
    d.arrow([(780, 190), (890, 155)], P["green"], label="넣은 행이\n있다", start="q", end="y", label_size=12)
    d.arrow([(780, 230), (890, 295)], P["red"], label="넣은 행이\n없다", start="q", end="n", label_size=12)
    d.text(40, 400, "세 번째 단계: 기록과 처리를 한 트랜잭션으로 커밋한다 (다음 그림)", 15, P["muted"])
    d.save()


def check_then_act():
    timeline("blog03-check-then-act", "\"있나 확인 → 없으면 넣기\" 는 두 단계다 (check-then-act)",
             "SELECT 로 확인하는 코드 — 같은 messageId m-3 이 두 컨슈머에 동시에 온다",
             [("A", "1  SELECT FROM inbox WHERE id = 'm-3'", "결과 없음  → 처음 본다고 판단", None),
              ("B", "2  SELECT FROM inbox WHERE id = 'm-3'", "결과 없음  → 처음 본다고 판단", None),
              ("A", "3  처리 + INSERT INTO inbox  → COMMIT", "A 가 처리를 끝낸다", None),
              ("B", "4  처리 + INSERT INTO inbox", "B 도 이미 처리를 시작했다", "bad")],
             [(2, 3, "A 가 넣은 것을\nB 는 못 본다")],
             "확인과 삽입 사이에 같은 id 가 끼어들었다. 둘 다 \"처음 본다\" 고 판단해 같은 메시지를 두 번 처리한다.\n"
             "(해석 — 처리가 INSERT 앞에 있는 코드를 예로 든 장면이다. PK 가 있으면 B 의 INSERT 는 에러가 나지만 처리는 이미 두 번 일어난 뒤다)\n"
             "INSERT 한 문장이 유니크 인덱스를 통해 확인과 삽입을 원자적으로 하게 하는 것이 PK 를 쓰는 이유다.",
             "확인과 삽입이 두 단계라 사이가 샌다", level="READ COMMITTED")


def tx_compare():
    d = Diagram("blog03-tx-compare", 1360, 620, "inbox 기록은 반영과 같은 트랜잭션이어야 한다",
                "inbox 는 \"처리했다\" 는 주장이다 — 처리 결과와 같이 참이거나 같이 사라져야 한다", out=OUT)
    d.text(40, 104, "inbox 를 먼저 커밋하고 반영은 따로", 16, P["ink"], weight=700)
    chain(d, "s", 134, 130, [
        ("inbox INSERT → 커밋", "\"처리됨\" 이 먼저 확정된다", "a"),
        ("반영이 실패한다", "상태는 그대로인데\ninbox 에는 처리됨", "bad"),
        ("재전달: inbox 충돌", "\"이미 처리\" 로 건너뛴다", "warn"),
        ("이벤트가 영영 사라진다", "반영되지 않았는데\ninbox 는 처리됨이라고 말한다", "bad")], w=290, gap=40)
    d.text(40, 320, "inbox 와 반영이 한 트랜잭션", 16, P["ink"], weight=700)
    chain(d, "o", 350, 130, [
        ("BEGIN → inbox INSERT", "같은 트랜잭션 안에서 기록", "a"),
        ("반영이 실패한다", "예외 → ROLLBACK", "bad"),
        ("inbox 기록도 사라진다", "롤백된 INSERT 는 다른 세션에\n영구히 보이지 않는다", "ok"),
        ("재전달이 곧 재시도", "처음 보는 메시지로 통과해\n정상 반영된다", "ok")], w=290, gap=40)
    box(d, "n", 40, 510, 1280, 80, "반영만 하고 inbox 기록은 없음 → 중복 반영 (Q01)",
        "(해석) 이 구조는 \"재전달되는 at-least-once\" 와 짝이다 — 롤백된 처리를 브로커가 다시 보내 준다는 전제 위에서 inbox 가 재시도 장치가 된다", "note")
    d.save()


def requires_new():
    d = Diagram("blog03-requires-new", 1360, 430, "Spring 에서는 경계가 어디냐의 문제다 (해석)",
                "REQUIRES_NEW 는 \"독립된 물리 트랜잭션\" 이라 안쪽이 바깥과 별개로 커밋/롤백한다 (Spring 전파 문서)", out=OUT)
    box(d, "a", 40, 120, 620, 190, "같은 @Transactional 메서드 안", "inbox INSERT → 반영 → 커밋\n\n예외가 나면 둘 다 롤백된다\n= 한 트랜잭션", "ok")
    box(d, "b", 700, 120, 620, 190, "inbox 저장을 다른 빈의 REQUIRES_NEW 로 뺀다", "inbox 는 따로 커밋, 반영은 바깥 트랜잭션\n\n반영이 실패해도 inbox 는 남는다\n= 앞 그림의 \"따로 커밋\"", "bad")
    d.text(40, 345, "JPA 로 inbox 를 save() 하면 중복 시 예외가 나고 영속성 컨텍스트가 오염될 수 있어, 영향 행 수 판정에는 네이티브 쿼리가 낫다 (해석, 확인하지 않음)", 13, P["muted"])
    d.save()


def rr_40001():
    timeline("blog03-rr-40001", "격리수준을 올리면 — REPEATABLE READ 의 INSERT ON CONFLICT",
             "스냅샷을 잡은 뒤, 그 사이 다른 세션이 커밋한 m-1 에 INSERT … ON CONFLICT DO NOTHING (실측: psql 2026-10-13)",
             [("A", "1  BEGIN (REPEATABLE READ); SELECT 1", "스냅샷이 잡힌다", None),
              ("B", "2  INSERT m-1  → COMMIT", "A 의 스냅샷 이후의 커밋", None),
              ("A", "3  INSERT m-1 ON CONFLICT DO NOTHING", "ERROR 40001  (concurrent update)", "bad")],
             [(1, 2, "A 의 스냅샷에\n안 보이는 행")],
             "READ COMMITTED 였다면 에러가 아니라 건너뛰는 것으로 끝난다. RR 에서는 스냅샷 이후의 커밋과 충돌하면 40001 이다.\n"
             "스냅샷 시작 전에 커밋돼 있던 행과의 충돌은 에러 없이 건너뛰었다. RR 로 올린 컨슈머는 40001 재시도를 구현해야 한다.",
             "격리수준을 올리면 건너뛰기 대신 직렬화 실패가 난다", level="REPEATABLE READ", level_b="READ COMMITTED")


def concurrent_branches():
    d = Diagram("blog03-concurrent", 1360, 560, "같은 messageId 가 동시에 — 둘째는 첫째의 결말에 따라 정해진다",
                "inbox 의 PK 유니크 인덱스가 줄을 세운다 (실측: psql 2026-10-13)", out=OUT)
    box(d, "a", 40, 110, 560, 110, "세션 A: BEGIN; INSERT 'm-5' ON CONFLICT DO NOTHING", "아직 커밋 전 — A 의 트랜잭션 ID 가 열려 있다", "a")
    box(d, "b", 760, 110, 560, 110, "세션 B: 같은 INSERT", "멈춘다 — Lock / transactionid\n상대 트랜잭션 ID 가 끝나기를 기다린다", "warn")
    d.arrow([(600, 165), (760, 165)], P["red"], label="B 가\n기다린다", label_size=12, start="a", end="b")
    box(d, "c", 40, 290, 560, 190, "A 가 COMMIT 하면", "B 는 충돌로 보고 건너뛴다 (DUPLICATE)\n\n에러가 아니다 — 결과는 0행\ninbox 에는 m-5 한 건", "ok")
    box(d, "r", 760, 290, 560, 190, "A 가 ROLLBACK 하면", "A 의 기록은 사라졌다\nB 가 넣고 진행한다 (처음 보는 메시지)\n\ninbox 에는 m-5 한 건", "ok")
    d.arrow([(320, 220), (320, 290)], P["green"], label="커밋", label_size=12)
    d.arrow([(1040, 220), (1040, 290)], P["green"], label="롤백", label_size=12)
    d.text(40, 505, "이 대기는 행이 아니라 트랜잭션의 끝을 기다린다 — 그래서 inbox INSERT 는 반영과 같은 트랜잭션 안에 있어야 의미가 맞다", 14, P["muted"])
    d.save()


if __name__ == "__main__":
    for f in (inbox_flow, check_then_act, tx_compare, requires_new, rr_40001, concurrent_branches):
        f()
    finish()
