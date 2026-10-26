#!/usr/bin/env python3
"""01.06 원장과 대사 그림. 실행: python3 -I diagrams/draw.py (레슨 폴더에서)"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "tools"))
from diagram import Diagram, P, finish  # noqa: E402

OUT = pathlib.Path(__file__).parent


def ledger_reconciliation():
    d = Diagram("ledger-reconciliation", 1440, 940, "원장과 대사 — 맞아야 하는 숫자를 기록하고, 틀렸을 때 알아채기",
                "잔고는 결과일 뿐, 거래 내역(원장)이 근거다. 같은 사실을 두 곳에 적어 두면 서로 맞춰 볼 수 있다", out=OUT)

    # ── 왼쪽: 원장 ──
    d.rect("pa", 40, 110, 640, 790, P["white"], P["line"], dashed=True)
    d.text(60, 124, "원장 — 쌓기만 한다, 잔고는 그 합 (Q05 · Q07)", 17, P["ink"], weight=700)

    d.card("t1", 60, 170, 600, 190, "거래 T1 = 이체 100.00 (계좌 1 → 계좌 2)  ·  한 트랜잭션",
           "ledger  (T1, 계좌 1, -100.00)   (T1, 계좌 2, +100.00)   ← 두 다리\n"
           "account 계좌 1 잔고 -100.00 · 계좌 2 잔고 +100.00  (balance = balance + ?)\n"
           "posted_txn  T1 선점 (같은 거래를 두 번 반영하지 않는다 · Q08)\n"
           "돈 = numeric / BigDecimal.  float8 / double 은 0.1 + 0.2 ≠ 0.3 (Q01 · Q02 · Q09)",
           bg=P["as_bg"], stroke=P["front"], title_size=15, body_size=14)

    d.card("r1", 60, 390, 600, 130, "규칙 1 — 다리의 합은 0",
           "CONSTRAINT TRIGGER … DEFERRABLE INITIALLY DEFERRED\n"
           "한 다리만 넣은 문장은 성공 → 커밋 때 P0001 로 롤백 (Q05)\n"
           "SET CONSTRAINTS ALL IMMEDIATE 면 그 문장에서 바로 (Q06)",
           bg=P["ok_bg"], stroke=P["green"], title_size=15, body_size=14)
    d.card("r2", 60, 545, 600, 130, "규칙 2 — 고치지 않는다 (append-only)",
           "행 트리거가 UPDATE · DELETE 를 막는다 (Q07).  고칠 땐 반대 방향 거래를 새로 쌓는다\n"
           "함정: 행 트리거는 TRUNCATE 를 못 본다 — 권한 회수 · TRUNCATE 문장 트리거로 따로",
           bg=P["ok_bg"], stroke=P["green"], title_size=15, body_size=14)
    d.card("r3", 60, 700, 600, 150, "규칙 3 — 잔고는 0 이상 (CHECK)",
           "문장마다 즉시 검사 — 커밋을 기다리지 않는다 (Q04).  CHECK 는 DEFERRABLE 이 아니다\n"
           "에러를 받은 트랜잭션은 실패 상태 → 다음 문장은 25P02\n"
           "그래서 post() 는 23514 를 잡아 롤백하고 '잔고 부족' 으로 돌려준다",
           bg=P["ok_bg"], stroke=P["green"], title_size=15, body_size=14)

    # ── 오른쪽: 대사 ──
    d.rect("pb", 720, 110, 680, 790, P["white"], P["line"], dashed=True)
    d.text(740, 124, "대사 — 두 곳을 맞춰, 어긋난 것만 건진다 (Q10)", 17, P["ink"], weight=700)

    d.card("k1", 740, 170, 270, 120, "계좌 잔고", "account.balance\n(빠른 조회용 요약)",
           bg=P["white"], stroke=P["front"], title_size=15, body_size=14)
    d.card("k2", 1110, 170, 270, 120, "계좌별 원장 합", "SUM(ledger.amount)\nGROUP BY account_id",
           bg=P["white"], stroke=P["back"], title_size=15, body_size=14)
    d.arrow([d.anchor("k1", "e"), d.anchor("k2", "w")], P["orange"], "내부 대사", start="k1", end="k2", both=True)

    d.card("k3", 740, 330, 270, 120, "우리 원장", "거래 id · 금액 (+ 다리)",
           bg=P["white"], stroke=P["back"], title_size=15, body_size=14)
    d.card("k4", 1110, 330, 270, 120, "외부 정산 내역", "상대 시스템이 보낸\n거래 id · 금액",
           bg=P["white"], stroke=P["muted"], title_size=15, body_size=14)
    d.arrow([d.anchor("k3", "e"), d.anchor("k4", "w")], P["orange"], "외부 대사", start="k3", end="k4", both=True)

    d.card("k5", 740, 490, 640, 200, "찾는 것은 '어긋난 행' — 한쪽에만 있는 행이 핵심이라 FULL OUTER JOIN",
           "BALANCE_NOT_MATCH     잔고 ≠ 원장 합 (원장이 없는 계좌는 합 0 으로)\n"
           "LEDGER_WITHOUT_ACCOUNT 원장은 있는데 계좌가 없다\n"
           "OURS_ONLY · THEIRS_ONLY 한쪽에만 있는 거래\n"
           "AMOUNT_DIFFERS         양쪽에 있지만 금액이 다르다\n"
           "INNER JOIN 이면 한쪽에만 있는 행은 아예 안 보인다 (Q10: 1건 vs 3건)",
           bg=P["todo_bg"], stroke=P["orange"], title_size=15, body_size=14)

    d.card("k6", 740, 720, 640, 150, "대사가 '맞다' 고 하는 것의 한계",
           "같은 입력에서 둘 다 틀리면 서로 맞는다 — 대사는 '두 기록의 불일치' 만 찾는다\n"
           "SUM 의 NULL · 0 vs 0.00 · 부동소수 합은 = 비교로 거짓 경보를 낸다 (Q09)\n"
           "결과는 읽기만 한다 — 고치는 건 원인을 본 사람이 반대 거래로",
           bg=P["note_bg"], stroke=P["line"], title_size=15, body_size=14)
    d.save()


if __name__ == "__main__":
    ledger_reconciliation()
    finish()
