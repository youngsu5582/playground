#!/usr/bin/env python3
"""01.04 블로그판 01 그림. 실행: python3 -I docs/diagrams/draw_blog01.py (레슨 폴더에서)"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[4] / "tools"))
from diagram import Diagram, P, finish, timeline as _timeline  # noqa: E402

OUT = pathlib.Path(__file__).parent


def timeline(*a, **k):
    return _timeline(*a, out=OUT, **k)


def intro():
    timeline("blog01-intro", "도입: 재고 10 에서 두 구매자가 동시에 산다",
             "A 는 3 개, B 는 4 개를 산다. 차례로 처리하면 어느 순서든 재고는 3 이 된다",
             [("A", "1  SELECT qty", "본 값: 10", None),
              ("B", "2  SELECT qty", "본 값: 10", None),
              ("A", "3  UPDATE qty = 7  → COMMIT", "10 - 3 = 7  (앱이 계산한 값)", None),
              ("B", "4  UPDATE qty = 6  → COMMIT", "10 - 4 = 6  (A 의 3 개가 사라진다)", "bad")],
             [(2, 3, "A 가 쓴 7 을\nB 가 덮어쓴다")],
             "7 개가 팔렸는데 재고는 4 만 줄었다. 에러도 음수도 없다 — 숫자만 조용히 어긋난다.\n"
             "읽는 문장과 쓰는 문장이 따로라서, 그 사이에 남이 끼어들 수 있었다.",
             "A 의 판매가 흔적 없이 사라졌다")


def rmw():
    d = Diagram("blog01-rmw", 1460, 440, "읽고 계산해서 쓰기 (read-modify-write)",
                "세 단계는 서로 다른 문장이다. 문장과 문장 사이가 틈이다", out=OUT)
    xs = [40, 540, 1040]
    cards = [("① 읽기", "SELECT qty FROM stock\nWHERE sku = ?", "행 락을 잡지 않는다", P["as_bg"], P["front"]),
             ("② 확인", "if (row.qty() < n)\n    return false", "앱 메모리 안의 판단", P["note_bg"], P["line"]),
             ("③ 쓰기", "UPDATE stock SET qty = ?\n앱이 계산한 절대 값 (읽은 값 - n)", "읽은 값이 낡았어도 그대로 덮어쓴다",
              P["bad_bg"], P["red"])]
    for i, (t, code, note, bg, st) in enumerate(cards):
        d.card(f"c{i}", xs[i], 110, 380, 160, t, code + "\n\n" + note, bg=bg, stroke=st, title_size=18, body_size=14,
               mono_body=False)
    for i in range(2):
        d.arrow([(xs[i] + 380, 195), (xs[i + 1], 195)], P["red"], "틈", dashed=True, start=f"c{i}", end=f"c{i+1}",
                label_size=15)
    d.card("note", 40, 310, 1380, 100, "틈 = 문장 사이",
           "A 가 ① 을 하고 B 도 ① 을 하면 둘은 같은 값을 본다. 둘 다 \"재고 있네\" 를 확인한 뒤 ③ 으로 \"읽은 값 - n\" 을 덮어쓴다.\n"
           "트랜잭션 안에서도 ① 과 ③ 은 다른 문장이다. 틈은 문장 사이에 있다.",
           bg=P["note_bg"], stroke=P["line"], title_size=16, body_size=14)
    d.save()


def oversell():
    timeline("blog01-oversell", "초과 판매 (oversell)",
             "\"재고 있다\" 는 판단이 이미 낡았다 — 재고 3, A 와 B 가 각각 2 개를 산다",
             [("A", "1  SELECT qty", "본 값: 3", None),
              ("B", "2  SELECT qty", "본 값: 3", None),
              ("A", "3  확인 3 >= 2  →  UPDATE qty = 1  → COMMIT", "A 에게 성공 응답", None),
              ("B", "4  확인 3 >= 2  →  UPDATE qty = 1  → COMMIT", "B 에게도 성공 응답 (판단이 낡았다)", "bad")],
             [(2, 3, "A 의 판매가\n판단에 안 보인다")],
             "성공 응답 두 건으로 4 개를 팔았는데 재고는 3 에서 1 로, 2 개만 줄었다. 재고는 음수가 아니다.\n"
             "그래서 검사는 불변식으로 한다 — 팔린 수 = 초기 재고 - 최종 재고, 그리고 팔린 수 <= 초기 재고.",
             "약속은 4 개, 재고는 2 개만 줄었다")


def rc_locks():
    d = Diagram("blog01-rc-locks", 1300, 400, "READ COMMITTED 에서 어떤 문장이 행 락을 잡나",
                "락을 잡는 쪽은 쓰는 문장과 잠그는 읽기뿐이다", out=OUT)
    d.card("a", 40, 110, 580, 140, "락을 잡는 문장",
           "UPDATE · DELETE\nSELECT ... FOR UPDATE 같은 잠금 읽기\n\n같은 행에 오는 쓰는 쪽 · 잠그는 쪽을 막는다",
           bg=P["bad_bg"], stroke=P["red"], title_size=18, body_size=15)
    d.card("b", 680, 110, 580, 140, "락을 잡지 않는 문장",
           "일반 SELECT\n\n문장 시작 시점의 스냅샷을 읽는다\n읽기와 쓰기는 서로를 막지 않는다 (MVCC)",
           bg=P["ok_bg"], stroke=P["green"], title_size=18, body_size=15)
    d.card("c", 40, 290, 1220, 80, "그래서 ① 읽기는 틈을 보호하지 못한다",
           "문서 13.3.2: \"Row-level locks do not affect data querying; they block only writers and lockers to the same row\"",
           bg=P["note_bg"], stroke=P["line"], title_size=16, body_size=14)
    d.save()


def three_ways():
    d = Diagram("blog01-three-ways", 1460, 430, "틈을 닫는 세 가지 방법",
                "원인은 하나(틈)이고, 틈을 다루는 방법이 셋이다", out=OUT)
    cols = [("원자 조건부 UPDATE", "틈을 없앤다", "확인과 쓰기를\n한 문장으로 붙인다", "02", P["ok_bg"], P["green"]),
            ("비관 락  FOR UPDATE", "틈은 있지만 잠근다", "읽는 순간 행을 잠가\n남이 끼어들지 못하게 한다", "03", P["rs_bg"], P["orange"]),
            ("낙관 락  WHERE version = ?", "틈은 있고 감지한다", "끼어들었으면 쓰는 순간\n0 행으로 알아챈다", "04", P["as_bg"], P["front"])]
    for i, (t, s, body, n, bg, st) in enumerate(cols):
        x = 40 + i * 470
        d.card(f"k{i}", x, 120, 440, 160, t, s + "\n\n" + body, bg=bg, stroke=st, title_size=18, body_size=16)
        d.pill(f"n{i}", x + 120, 310, 200, 50, f"다음 글 {n}", P["white"], st, size=16)
        d.arrow([(x + 220, 280), (x + 220, 310)], st)
    d.text(40, 390, "비용도 갈린다 — 줄을 서서 기다리나(없앤다 · 잠근다), 진 쪽이 다시 하나(감지한다)", 15, P["muted"])
    d.save()


if __name__ == "__main__":
    for f in (intro, rmw, oversell, rc_locks, three_ways):
        f()
    finish()
