#!/usr/bin/env python3
"""01 트랙 블로그판 그림 공용 도우미 (draw_blog_t0N.py 가 import). 직접 실행하지 않는다."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "tools"))
from diagram import Diagram, P, finish, tw  # noqa: E402,F401

OUT = pathlib.Path(__file__).parent

KINDS = {
    "a": (P["as_bg"], P["front"]), "b": (P["bff_bg"], P["back"]), "ok": (P["ok_bg"], P["green"]),
    "bad": (P["bad_bg"], P["red"]), "warn": (P["todo_bg"], P["orange"]), "note": (P["note_bg"], P["line"]),
    "w": (P["white"], P["line"]), "rs": (P["rs_bg"], P["orange"]),
}
ARROW = {"a": P["front"], "b": P["back"], "ok": P["green"], "bad": P["red"], "warn": P["orange"],
         "note": P["muted"], "w": P["muted"], "rs": P["orange"]}


def card_h(title, body, ts=16, bs=14):
    h = 12 + ts * 1.25 * len(title.split("\n")) + 14
    if body:
        h += 6 + bs * 1.25 * len(body.split("\n"))
    return int(h)


def kc(kind):
    return KINDS[kind]


def new(name, w, h, title, sub):
    return Diagram(name, w, h, title, sub, out=OUT)


def vchain(name, title, sub, specs, labels=(), w=1240, cw=700, top=100, gap=56, notes=None, ts=16, bs=14):
    """세로 흐름. specs: [(title, body, kind)], labels: 카드 i → i+1 화살표 라벨, notes: 카드 오른쪽 설명 {i: text}."""
    hs = [card_h(t, b, ts, bs) for t, b, _ in specs]
    total = top + sum(hs) + gap * (len(specs) - 1) + 30
    d = new(name, w, total, title, sub)
    y = top
    ys = []
    for i, (t, b, k) in enumerate(specs):
        bg, st = kc(k)
        d.card(f"c{i}", 40, y, cw, hs[i], t, b, bg=bg, stroke=st, title_size=ts, body_size=bs)
        if notes and i in notes:
            d.text(40 + cw + 30, y + 10, notes[i], 14, P["muted"])
        ys.append(y)
        y += hs[i] + gap
    for i in range(len(specs) - 1):
        k = specs[i][2]
        y0 = ys[i] + hs[i]
        lab = labels[i] if i < len(labels) else None
        la = (40 + cw / 2 + tw(lab.split("\n")[0], 13) / 2 + 30, y0 + gap / 2) if lab else None
        d.arrow([(40 + cw / 2, y0), (40 + cw / 2, y0 + gap)], ARROW[k], lab, start=f"c{i}", end=f"c{i + 1}", label_at=la)
    return d


def hchain(name, title, sub, specs, labels=(), w=1400, top=110, gap=90, h=None, ts=16, bs=14, extra=0, x0=40):
    """가로 흐름. specs: [(title, body, kind)]."""
    n = len(specs)
    cw = (w - 2 * x0 - gap * (n - 1)) / n
    hh = h or max(card_h(t, b, ts, bs) for t, b, _ in specs)
    d = new(name, w, top + hh + 40 + extra, title, sub)
    for i, (t, b, k) in enumerate(specs):
        bg, st = kc(k)
        x = x0 + i * (cw + gap)
        d.card(f"c{i}", x, top, cw, hh, t, b, bg=bg, stroke=st, title_size=ts, body_size=bs)
    for i in range(n - 1):
        k = specs[i][2]
        x = x0 + i * (cw + gap)
        lab = labels[i] if i < len(labels) else None
        d.arrow([(x + cw, top + hh / 2), (x + cw + gap, top + hh / 2)], ARROW[k], lab, start=f"c{i}", end=f"c{i + 1}")
    return d


def sequence(name, title, sub, lanes, events, w=1200, pitch=74, top=96, bottom_note=None):
    """시퀀스 그림. lanes: [(label, kind)], events:
       ("msg", i, j, label, color_kind)  — 레인 i → j 화살표
       ("note", i, text, kind)           — 레인 i 위에 놓는 카드"""
    n = len(lanes)
    xs = [140 + k * (w - 280) / (n - 1) for k in range(n)]
    bn_h = (card_h(*bottom_note[:2]) + 20) if bottom_note else 0
    h = top + 70 + len(events) * pitch + 20 + bn_h
    d = new(name, w, h, title, sub)
    for k, (lab, kind) in enumerate(lanes):
        bg, st = kc(kind)
        d.pill(f"L{k}", xs[k] - 110, top, 220, 44, lab, bg, st, size=15)
        # 생명선은 노트 카드 구간을 건너뛴다 (카드 글자를 점선이 가로지르지 않게)
        gaps = []
        for idx, ev in enumerate(events):
            if ev[0] == "note" and ev[1] == k:
                yy = top + 70 + idx * pitch + pitch / 2
                nh = 14 * 1.25 * len(ev[2].split("\n")) + 22
                gaps.append((yy - nh / 2 - 2, yy + nh / 2 + 2))
        y0, y1 = top + 44, h - 20 - bn_h
        for ga, gb in sorted(gaps):
            if ga > y0:
                d.line([(xs[k], y0), (xs[k], ga)], P["line"], dashed=True)
            y0 = max(y0, gb)
        if y1 > y0:
            d.line([(xs[k], y0), (xs[k], y1)], P["line"], dashed=True)
    for idx, ev in enumerate(events):
        y = top + 70 + idx * pitch + pitch / 2
        if ev[0] == "msg":
            _, i, j, lab, ck = ev
            x0, x1 = xs[i], xs[j]
            d.arrow([(x0, y), (x1, y)], ARROW[ck], lab, label_at=((x0 + x1) / 2, y - 18), label_size=13)
        elif ev[0] == "note":
            _, i, text, kind = ev
            bg, st = kc(kind)
            nw = max(tw(l, 14) for l in text.split("\n")) + 28
            nh = 14 * 1.25 * len(text.split("\n")) + 22
            d.pill(f"N{idx}", xs[i] - nw / 2, y - nh / 2, nw, nh, text, bg, st, size=14)
    if bottom_note:
        t, body, kind = bottom_note
        bg, st = kc(kind)
        d.card("bn", 40, h - 10 - bn_h + 10, w - 80, card_h(t, body), t, body, bg=bg, stroke=st)
    return d


def matrix(name, title, sub, heads, rows, w=1400, first_w=260, row_h=70, size=14, head_h=56, top=100, notes=None):
    """표 그림. rows: [(label, [(text, kind), ...])]"""
    n = len(heads)
    cw = (w - 80 - first_w - 10 * n) / n
    h = top + head_h + 12 + len(rows) * (row_h + 10) + (60 if notes else 20)
    d = new(name, w, h, title, sub)
    for c, t in enumerate(heads):
        d.pill(f"h{c}", 40 + first_w + 10 + c * (cw + 10), top, cw, head_h, t, P["note_bg"], P["line"], size=size)
    for r, (lab, cells) in enumerate(rows):
        y = top + head_h + 12 + r * (row_h + 10)
        d.pill(f"l{r}", 40, y, first_w, row_h, lab, P["as_bg"], P["front"], size=size)
        for c, (t, kind) in enumerate(cells):
            bg, st = kc(kind)
            d.pill(f"c{r}_{c}", 40 + first_w + 10 + c * (cw + 10), y, cw, row_h, t, bg, st, size=size)
    if notes:
        d.text(40, h - 46, notes, 14, P["muted"])
    return d
