#!/usr/bin/env python3
"""01.01 docs 그림. 실행: python3 -I docs/diagrams/draw.py (레슨 폴더에서)"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[4] / "tools"))
from diagram import Diagram, P, finish  # noqa: E402

OUT = pathlib.Path(__file__).parent


def tuple_visibility():
    d = Diagram("tuple-visibility", 1400, 690, "행 버전(튜플)과 스냅샷 판정 — PostgreSQL 16",
                "같은 논리 행의 세 버전. 스냅샷 108:110:108 이 보는 것은 v2 하나뿐이다 (숫자는 설명용)", out=OUT)
    d.card("v1", 40, 110, 380, 130, "v1   balance = 100",
           "xmin = 100   xmax = 105\n만든 100 : 스냅샷보다 앞 (커밋)\n지운 105 : 스냅샷보다 앞 (커밋)",
           bg=P["note_bg"], stroke=P["muted"], body_size=14, mono_body=True)
    d.card("v2", 510, 110, 380, 130, "v2   balance = 50",
           "xmin = 105   xmax = 110\n만든 105 : 스냅샷보다 앞 (커밋)\n지운 110 : xmax 이상 = 아직 안 일어남",
           bg=P["ok_bg"], stroke=P["green"], body_size=14, mono_body=True)
    d.card("v3", 980, 110, 380, 130, "v3   balance = 20",
           "xmin = 110   xmax = 0\n만든 110 : xmax 이상 = 아직 안 일어남\n지운 이 없음",
           bg=P["note_bg"], stroke=P["muted"], body_size=14, mono_body=True)
    d.arrow([d.anchor("v1", "e"), d.anchor("v2", "w")], P["muted"], "UPDATE (105)", start="v1", end="v2")
    d.arrow([d.anchor("v2", "e"), d.anchor("v3", "w")], P["muted"], "UPDATE (110)", start="v2", end="v3")

    d.pill("j1", 40, 260, 380, 44, "안 보인다 — 이미 지워진 버전", P["bad_bg"], P["red"], size=14)
    d.pill("j2", 510, 260, 380, 44, "보인다 — 만든 쪽 보임, 지운 쪽 안 보임", P["ok_bg"], P["green"], size=14)
    d.pill("j3", 980, 260, 380, 44, "안 보인다 — 아직 만들어지지 않은 버전", P["bad_bg"], P["red"], size=14)

    d.card("snap", 40, 340, 640, 210, "스냅샷  108:110:108   (pg_current_snapshot() 의 형식 xmin:xmax:xip)",
           "xmin = 108   이보다 작은 ID 는 전부 끝났다 (커밋 또는 롤백)\n"
           "xmax = 110   이 이상의 ID 는 스냅샷 이후에 시작 — 안 보인다\n"
           "xip  = 108   스냅샷 순간 진행 중이던 트랜잭션\n\n"
           "ID 가 xmin 과 xmax 사이이고 xip 에 있으면 안 끝난 것,\n"
           "xip 에 없으면 끝난 것 — 커밋 상태를 pg_xact 에서 확인",
           bg=P["as_bg"], stroke=P["front"], title_size=15, body_size=14)
    d.card("rule", 720, 340, 640, 210, "판정 규칙 (단순화)",
           "보이는 버전 =\n"
           "  xmin 의 트랜잭션이 내 스냅샷 기준으로 커밋됐고\n"
           "  xmax 가 0 이거나, 그 트랜잭션이 내 스냅샷 기준으로\n  커밋되지 않은 것 (진행 중이거나 롤백)\n\n"
           "스냅샷을 언제 잡느냐가 격리수준마다 다르다 (문서 03)",
           bg=P["todo_bg"], stroke=P["orange"], title_size=15, body_size=14)
    d.card("note", 40, 580, 1320, 80, "판정에 쓰이는 것은 버전 헤더와 스냅샷뿐",
           "읽기는 행 버전의 xmin/xmax 와 스냅샷만 비교해 판정한다. 아무도 보지 못하게 된 옛 버전(v1)은 VACUUM 이 치운다",
           bg=P["note_bg"], stroke=P["line"], title_size=14, body_size=14)
    d.save()


def ssi_cycle():
    d = Diagram("ssi-rw-cycle", 1300, 590, "write skew 와 rw-의존성 고리 (SSI)",
                "읽은 것을 상대가 덮어쓰면 rw-의존성이 생긴다. 서로 그러면 고리 — 직렬 순서가 없다", out=OUT)
    d.card("a", 60, 140, 380, 160, "트랜잭션 A (SERIALIZABLE)",
           "1. 읽기 : on_call 2명 (alice, bob 모두 봄)\n2. 쓰기 : alice 를 false 로\n3. 커밋",
           bg=P["as_bg"], stroke=P["front"], title_size=16, body_size=14)
    d.card("b", 860, 140, 380, 160, "트랜잭션 B (SERIALIZABLE)",
           "1. 읽기 : on_call 2명 (alice, bob 모두 봄)\n2. 쓰기 : bob 을 false 로\n3. 커밋",
           bg=P["bff_bg"], stroke=P["back"], title_size=16, body_size=14)
    d.arrow([(440, 190), (860, 190)], P["red"], "A 가 읽은 bob 을 B 가 고친다\nA 는 B 보다 먼저인 것처럼 보여야 한다", start="a", end="b")
    d.arrow([(860, 260), (440, 260)], P["red"], "B 가 읽은 alice 를 A 가 고친다\nB 는 A 보다 먼저인 것처럼 보여야 한다", start="b", end="a")
    d.card("cyc", 60, 350, 580, 160, "고리 = 직렬로 늘어놓을 수 없다",
           "A -> B 이고 B -> A 이므로 \"A 먼저\" 도 \"B 먼저\" 도 안 맞는다\n"
           "스냅샷 격리는 읽기-쓰기 관계를 추적하지 않는다 (Q08 · Q09 로 예측)\n"
           "SERIALIZABLE 은 읽은 범위를 SIREAD 락으로 기록해 이 관계를 추적한다",
           bg=P["todo_bg"], stroke=P["orange"], title_size=15, body_size=14)
    d.card("dang", 680, 350, 560, 200, "엔진이 찾는 것: 위험한 구조",
           "T1 -rw-> T2 -rw-> T3  (T2 = pivot)\n"
           "그리고 T3 가 가장 먼저 커밋\n"
           "이 모양이면 고리가 될 수 있다고 보고 취소한다\n"
           "(README-SSI: Tout 이 Tpivot · Tin 보다 먼저 커밋할 때만)\n"
           "실제 고리가 아니어도 취소될 수 있다 = 오탐",
           bg=P["note_bg"], stroke=P["line"], title_size=15, body_size=14)
    d.save()


if __name__ == "__main__":
    tuple_visibility()
    ssi_cycle()
    finish()
