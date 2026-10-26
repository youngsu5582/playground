#!/usr/bin/env python3
"""01.06 블로그 01 그림 (숫자를 어떻게 저장하나). 실행: python3 -I docs/diagrams/draw_blog01.py (레슨 폴더에서)"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[4] / "tools"))
from diagram import Diagram, P, finish  # noqa: E402

OUT = pathlib.Path(__file__).parent


def intro():
    d = Diagram("blog01-intro", 1160, 470, "도입: 1.1 + 2.2 는 3.3 인가",
                "장부의 합계를 = 로 맞춰 보는 대사가 있다고 하자. 같은 식을 두 타입으로 계산했다 (PostgreSQL 16)", out=OUT)
    d.card("f", 40, 110, 520, 160, "float8 (double precision)",
           "SELECT 1.1::float8 + 2.2::float8\n→  3.3000000000000003\n\n1.1 + 2.2 = 3.3   →   false",
           bg=P["bad_bg"], stroke=P["red"], mono_body=True, body_size=15)
    d.card("n", 600, 110, 520, 160, "numeric",
           "SELECT 1.1::numeric + 2.2::numeric\n→  3.3\n\n1.1 + 2.2 = 3.3   →   true",
           bg=P["ok_bg"], stroke=P["green"], mono_body=True, body_size=15)
    d.arrow([(300, 270), (300, 310)], P["red"], "= 로 비교하면")
    d.arrow([(860, 270), (860, 310)], P["green"], "= 로 비교하면")
    d.card("v", 40, 320, 1080, 120, "눈으로는 같은 숫자인데 컴퓨터는 다른 숫자라고 한다",
           "float8 쪽은 \"3.3 에 아주 가까운 값\" 을 들고 있다.  합계를 = 로 맞춰 보는 대사는 틀린 데가 없는데도 경보를 낸다.\n"
           "돈을 어떤 타입에 담느냐가 대사 이전의 문제다 — 이 글은 그 타입을 고르는 이야기다.",
           bg=P["note_bg"], stroke=P["line"], title_size=16)
    d.save()


def binary():
    d = Diagram("blog01-binary", 1160, 480, "왜 float8 은 0.1 을 정확히 못 담나",
                "float8 은 값을 2 진수로 담는다 — 2 로 나누어 떨어지는 값만 정확하다 (일반 개념)", out=OUT)
    d.card("a", 40, 110, 520, 190, "0.5 · 0.25 · 0.125  (2 의 거듭제곱 분수)",
           "0.5   = 2 진수 0.1\n0.25  = 2 진수 0.01\n0.125 = 2 진수 0.001\n\n끝이 있는 2 진 소수 → float8 에 정확히 담긴다",
           bg=P["ok_bg"], stroke=P["green"], mono_body=True)
    d.card("b", 600, 110, 520, 190, "0.1 · 0.2 · 1.1  (10 으로만 나누어 떨어지는 값)",
           "0.1 = 2 진수 0.0001100110011…\n\n1 0 0 1 1 이 끝없이 반복되는 2 진 소수\n→ 8 바이트에 잘라 담는다 = 근사값",
           bg=P["bad_bg"], stroke=P["red"], mono_body=True)
    d.arrow([(300, 300), (300, 340)], P["green"], "정확하다")
    d.arrow([(860, 300), (860, 340)], P["red"], "잘린다")
    d.card("c", 40, 350, 520, 100, "실측 (psql 2026-10-13)", "0.125::float8 + 0.125::float8 = 0.25::float8  →  true",
           bg=P["note_bg"], stroke=P["line"], mono_body=True, title_size=15, body_size=14)
    d.card("d", 600, 350, 520, 100, "실측 (psql 2026-10-13)", "1.1::float8 + 2.2::float8 = 3.3::float8 → false\n(차이 약 4.44e-16)",
           bg=P["note_bg"], stroke=P["line"], mono_body=True, title_size=15, body_size=14)
    d.save()


def float_digits():
    d = Diagram("blog01-float-digits", 1160, 500, "큰 금액은 소수 자리가 아니라 정수 자리에서도 새기 시작한다",
                "float8 은 정밀도가 최소 15 자리 (문서 8.1) — 17 자리 금액은 센트를 못 담는다", out=OUT)
    d.card("i", 40, 110, 520, 130, "정수 17 자리",
           "12345678901234567 :: bigint\n→ :: float8 → :: bigint\n→ 12345678901234568   (끝자리가 바뀐다)",
           bg=P["bad_bg"], stroke=P["red"], mono_body=True)
    d.card("m", 600, 110, 520, 130, "금액 12345678901234567.89",
           "float8   1.2345678901234568e+16   (센트 소실)\nnumeric  12345678901234567.89   (그대로)",
           bg=P["rs_bg"], stroke=P["orange"], mono_body=True)
    d.arrow([(300, 240), (300, 290)], P["red"], "정밀도 최소 15 자리")
    d.arrow([(860, 240), (860, 290)], P["orange"], "자리 수가 넘는다")
    d.card("v", 40, 300, 1080, 150, "정리",
           "문서(8.1): double precision 은 범위 약 1E-307 ~ 1E+308, 정밀도 최소 15 자리 — 17 자리 금액은 이 보장을 넘는다.\n"
           "실측(psql 2026-10-13): 위 두 줄. 값이 \"조금 틀린다\" 가 아니라 끝자리가 바뀌어 센트가 사라진다.\n"
           "이 레슨 구현 테스트의 방법 검사도 같은 금액(12345678901234567.89)을 쓴다.",
           bg=P["note_bg"], stroke=P["line"], title_size=16)
    d.save()


def layout():
    d = Diagram("blog01-numeric-layout", 1280, 440, "numeric(12, 2) 는 어떻게 생겼나",
                "precision 12 = 전체 유효 자릿수, scale 2 = 소수점 아래 자리 수 → 정수부는 12 - 2 = 10 자리까지", out=OUT)
    x0, w = 60, 70
    for i in range(10):
        d.pill(f"i{i}", x0 + i * (w + 4), 120, w, 60, "0~9", P["as_bg"], P["front"], size=20)
    d.text(x0 + 10 * (w + 4) + 6, 138, ".", 40, P["ink"], weight=700)
    for i in range(2):
        d.pill(f"f{i}", x0 + 10 * (w + 4) + 40 + i * (w + 4), 120, w, 60, "0~9", P["rs_bg"], P["orange"], size=20)
    d.text(x0 + 5 * (w + 4), 200, "정수부 최대 10 자리  (precision - scale)", 16, P["front"], align="center", weight=700)
    d.text(x0 + 10 * (w + 4) + 40 + (w + 4), 200, "소수부 2 자리 (scale)", 16, P["orange"], align="center", weight=700)
    d.card("max", 40, 250, 600, 150, "저장할 수 있는 범위",
           "정수부 10 자리 + 소수부 2 자리\n문서 8.1 의 예: NUMERIC(3, 1) 은 1 자리로 반올림하고\n-99.9 ~ 99.9 를 저장할 수 있다 — 같은 규칙이다",
           bg=P["ok_bg"], stroke=P["green"], mono_body=False)
    d.card("lim", 680, 250, 560, 150, "numeric 자체의 한계 (문서 8.1)",
           "선언할 수 있는 precision 최대 1000\n선언 없는 numeric: 소수점 앞 131072 자리 · 뒤 16383 자리까지",
           bg=P["note_bg"], stroke=P["line"])
    d.save()


def rounding():
    d = Diagram("blog01-rounding", 1160, 470, "반올림은 타입마다 규칙이 다르다",
                "정확히 가운데인 값(ties)을 어느 쪽으로 보내나 — 문서 8.1: numeric 은 0 에서 먼 쪽, float8 은 (대부분의 머신에서) 가장 가까운 짝수", out=OUT)
    d.pill("h0", 40, 100, 260, 52, "식", P["note_bg"], P["line"], size=15)
    d.pill("h1", 310, 100, 380, 52, "numeric — 0 에서 먼 쪽", P["ok_bg"], P["green"], size=15)
    d.pill("h2", 700, 100, 420, 52, "float8 — 가장 가까운 짝수", P["bad_bg"], P["red"], size=15)
    rows = [("round(2.5)", "3", "2"), ("round(3.5)", "4", "4"), ("2.675 → numeric(12, 2)", "2.68", "해당 없음 (scale 선언은 numeric 의 것)"),
            ("-2.675 → numeric(12, 2)", "-2.68  (0 에서 먼 쪽)", "해당 없음")]
    for r, (a, b, c) in enumerate(rows):
        y = 168 + r * 70
        d.pill(f"a{r}", 40, y, 260, 56, a, P["white"], P["line"], size=14, mono=True)
        d.pill(f"b{r}", 310, y, 380, 56, b, P["white"], P["line"], size=15)
        d.pill(f"c{r}", 700, y, 420, 56, c, P["white"], P["line"], size=14)
    d.save()


def store_flow():
    d = Diagram("blog01-store-flow", 1300, 560, "numeric(12, 2) 에 값을 넣으면 일어나는 일",
                "순서가 중요하다 — 반올림이 먼저, 자릿수 검사가 그다음 (문서 8.1)", out=OUT)
    d.pill("v", 40, 120, 200, 70, "들어온 값", P["note_bg"], P["line"], size=16)
    d.pill("s1", 330, 120, 280, 70, "1. scale(2) 로 반올림", P["rs_bg"], P["orange"], size=16)
    d.pill("s2", 700, 120, 300, 70, "2. 정수부가 10 자리 넘나?", P["as_bg"], P["front"], size=16)
    d.pill("ok", 1070, 120, 190, 70, "저장", P["ok_bg"], P["green"], size=16)
    d.arrow([(240, 155), (330, 155)], P["muted"])
    d.arrow([(610, 155), (700, 155)], P["muted"])
    d.arrow([(1000, 155), (1070, 155)], P["green"], "아니오")
    d.pill("er", 700, 250, 300, 70, "numeric field overflow", P["bad_bg"], P["red"], size=16)
    d.arrow([(850, 190), (850, 250)], P["red"], "예")
    d.card("e1", 40, 360, 600, 150, "예 1 — 조용히 반올림되어 저장",
           "2.675  →  scale 2 로 반올림  →  2.68  →  저장\n에러도 경고도 없다 (실측: psql 2026-10-13)",
           bg=P["rs_bg"], stroke=P["orange"], mono_body=False)
    d.card("e2", 680, 360, 580, 150, "예 2 — 반올림이 정수부를 넘치게 한다",
           "9999999999.995  →  반올림  →  10000000000.00\n→  정수부 11 자리  →  에러 (실측: psql 2026-10-13)\n\"must round to an absolute value less than 10^10\"",
           bg=P["bad_bg"], stroke=P["red"])
    d.save()


def app_path():
    d = Diagram("blog01-app-path", 1280, 520, "앱에서 돈이 지나가는 길",
                "DB 가 numeric 이어도 중간에 double 을 거치면 소용없다 (이 레슨 구현 테스트의 방법 검사)", out=OUT)
    d.pill("a1", 40, 120, 260, 64, "BigDecimal 금액", P["as_bg"], P["front"], size=16)
    d.pill("a2", 400, 120, 330, 64, "setBigDecimal / getBigDecimal", P["as_bg"], P["front"], size=15)
    d.pill("a3", 830, 120, 400, 64, "numeric(20, 2) 컬럼", P["ok_bg"], P["green"], size=16)
    d.arrow([(300, 152), (400, 152)], P["green"])
    d.arrow([(730, 152), (830, 152)], P["green"])
    d.text(40, 205, "끝까지 십진 정확값 — 금액이 그대로 오간다", 15, P["green"], weight=700)
    d.pill("b1", 40, 290, 260, 64, "BigDecimal 금액", P["as_bg"], P["front"], size=16)
    d.pill("b2", 400, 290, 280, 64, "doubleValue()  → double", P["bad_bg"], P["red"], size=15)
    d.pill("b3", 920, 290, 310, 64, "numeric(20, 2) 컬럼", P["white"], P["line"], size=16)
    d.arrow([(300, 322), (400, 322)], P["red"])
    d.arrow([(680, 322), (920, 322)], P["red"], "값이 이미 변했다")
    d.text(40, 375, "double 은 17 자리 금액에서 센트를 못 담는다 — 받는 쪽 컬럼이 아무리 정확해도 늦다", 15, P["red"], weight=700)
    d.card("n", 40, 420, 1190, 80, "계산도 DB 안에서",
           "UPDATE account SET balance = balance + ?  — 읽어 와 앱에서 더하지 않는다 (04 에서 이어진다)",
           bg=P["note_bg"], stroke=P["line"], title_size=15)
    d.save()


if __name__ == "__main__":
    for f in (intro, binary, float_digits, layout, rounding, store_flow, app_path):
        f()
    finish()
