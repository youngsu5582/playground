#!/usr/bin/env python3
"""
그림 라이브러리 — 같은 레이아웃 정의에서 두 파일을 뽑는다.
  <name>.excalidraw  편집용 원본 (excalidraw.com · VS Code · Obsidian 플러그인)
  <name>.svg         GitHub · Obsidian 에서 바로 보이는 미리보기

레슨의 diagrams/draw.py 가 이걸 import 한다:
    import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "tools"))
    from diagram import Diagram, P, legend, finish
    d = Diagram("mvcc", 1200, 700, "제목", "부제", out=pathlib.Path(__file__).parent)
    d.card("k", x, y, w, h, "제목", "본문"); d.arrow([...], P["front"], "라벨"); d.save(); finish()

색 규칙: 파랑 front · 보라 back · 주황 채울 곳 · 빨강 공격/실패 · 초록 정상/방어 · 회색 제공된 배관.
이모지는 SVG 렌더러에서 깨진다 — 쓰지 않는다.
"""
import json
import pathlib
import random
import sys
from html import escape

random.seed(20261006)

P = dict(
    ink="#1e1e1e", muted="#868e96", line="#adb5bd",
    front="#1971c2", back="#6741d9", red="#e03131", green="#2f9e44", orange="#e8590c", yellow="#f08c00",
    as_bg="#e7f5ff", rs_bg="#fff4e6", bff_bg="#f3f0ff", br_bg="#f8f9fa", todo_bg="#fff3bf",
    ok_bg="#ebfbee", bad_bg="#fff5f5", note_bg="#f1f3f5", white="#ffffff", given_bg="#f1f3f5",
)
SANS = "Pretendard, 'Apple SD Gothic Neo', 'Noto Sans KR', 'Malgun Gothic', system-ui, sans-serif"
MONO = "'SF Mono', Menlo, Consolas, 'D2Coding', monospace"
LH = 1.25
WARN = []


def cw(ch, mono):
    o = ord(ch)
    if o >= 0x1100:
        return 1.0
    if mono:
        return 0.61
    if ch == " ":
        return 0.28
    if ch in "il.,:;'|!·()[]{}/-":
        return 0.32
    if ch in "mwMW@%":
        return 0.86
    if ch.isupper():
        return 0.66
    if ch.isdigit():
        return 0.57
    return 0.54


def tw(s, size, mono=False):
    return sum(cw(c, mono) for c in s) * size


class Diagram:
    def __init__(self, name, w, h, title, subtitle=None, out=None):
        self.name, self.w, self.h = name, w, h
        self.out = pathlib.Path(out) if out else pathlib.Path.cwd()
        self.out.mkdir(parents=True, exist_ok=True)
        self.ex, self.shapes, self.lines, self.texts = [], [], [], []
        self.boxes, self.rect_el = {}, {}
        self.n = 0
        self.colors = set()
        self.text(40, 26, title, 26, P["ink"], weight=700)
        if subtitle:
            self.text(40, 66, subtitle, 15, P["muted"])

    # ── 내부 ──
    def _id(self, p):
        self.n += 1
        return f"{self.name}-{p}-{self.n}"

    def _base(self, t, x, y, w, h, stroke, bg, sw=2, dashed=False, rounded=True, rough=1, group=None):
        e = {"id": self._id(t), "type": t, "x": x, "y": y, "width": w, "height": h, "angle": 0,
             "strokeColor": stroke, "backgroundColor": bg, "fillStyle": "solid", "strokeWidth": sw,
             "strokeStyle": "dashed" if dashed else "solid", "roughness": rough, "opacity": 100,
             "groupIds": [group] if group else [], "frameId": None,
             "roundness": ({"type": 3} if rounded else None),
             "seed": random.randint(1, 2 ** 31 - 1), "version": 1, "versionNonce": random.randint(1, 2 ** 31 - 1),
             "isDeleted": False, "boundElements": [], "updated": 1759708800000, "link": None, "locked": False}
        self.ex.append(e)
        return e

    # ── 기본 도형 ──
    def text(self, x, y, s, size=15, color=None, align="left", mono=False, weight=400, group=None,
             container=None, valign="top"):
        color = color or P["ink"]
        lines = s.split("\n")
        w = max(tw(l, size, mono) for l in lines)
        h = len(lines) * size * LH
        left = x - w / 2 if align == "center" else (x - w if align == "right" else x)
        top = y - h / 2 if valign == "middle" else y
        e = self._base("text", left, top, w, h, color, "transparent", sw=1, rounded=False, group=group)
        e.update({"text": s, "originalText": s, "fontSize": size, "fontFamily": 3 if mono else 2,
                  "textAlign": align, "verticalAlign": "middle" if valign == "middle" else "top",
                  "containerId": container, "lineHeight": LH, "autoResize": True})
        anchor = {"left": "start", "center": "middle", "right": "end"}[align]
        fam = MONO if mono else SANS
        spans = []
        for i, line in enumerate(lines):
            by = top + i * size * LH + size * (0.88 + (LH - 1) / 2)
            spans.append(f'<tspan x="{x:.1f}" y="{by:.1f}">{escape(line) if line else "&#160;"}</tspan>')
        self.texts.append(f'<text font-family="{escape(fam)}" font-size="{size}" font-weight="{weight}" '
                          f'fill="{color}" text-anchor="{anchor}" xml:space="preserve">{"".join(spans)}</text>')
        return e

    def rect(self, key, x, y, w, h, bg, stroke, sw=2, dashed=False, rounded=True, group=None):
        e = self._base("rectangle", x, y, w, h, stroke, bg, sw=sw, dashed=dashed, rounded=rounded, group=group)
        if key:
            self.boxes[key] = (x, y, w, h)
            self.rect_el[key] = e
        da = ' stroke-dasharray="7 5"' if dashed else ""
        rx = 10 if rounded else 0
        self.shapes.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{bg}" '
                           f'stroke="{stroke}" stroke-width="{sw}"{da}/>')
        return e

    def diamond(self, key, x, y, w, h, text, bg, stroke, size=14):
        e = self._base("diamond", x, y, w, h, stroke, bg, rounded=False)
        self.boxes[key] = (x, y, w, h)
        self.rect_el[key] = e
        pts = f"{x + w / 2},{y} {x + w},{y + h / 2} {x + w / 2},{y + h} {x},{y + h / 2}"
        self.shapes.append(f'<polygon points="{pts}" fill="{bg}" stroke="{stroke}" stroke-width="2"/>')
        t = self.text(x + w / 2, y + h / 2, text, size, P["ink"], align="center", valign="middle", container=e["id"])
        e["boundElements"].append({"type": "text", "id": t["id"]})
        return e

    def ellipse(self, key, cx, cy, r, text, bg, stroke, size=13):
        e = self._base("ellipse", cx - r, cy - r, 2 * r, 2 * r, stroke, bg, rounded=False)
        self.boxes[key] = (cx - r, cy - r, 2 * r, 2 * r)
        self.rect_el[key] = e
        self.shapes.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{bg}" stroke="{stroke}" stroke-width="2"/>')
        t = self.text(cx, cy, text, size, stroke, align="center", valign="middle", container=e["id"], weight=700)
        e["boundElements"].append({"type": "text", "id": t["id"]})
        return e

    def card(self, key, x, y, w, h, title, body=None, bg=None, stroke=None, title_size=17, body_size=14,
             mono_body=False, align="left", dashed=False, title_color=None, sw=2):
        bg, stroke = bg or P["white"], stroke or P["ink"]
        g = self._id("g")
        self.rect(key, x, y, w, h, bg, stroke, sw=sw, dashed=dashed, group=g)
        tx = x + w / 2 if align == "center" else x + 16
        self.text(tx, y + 12, title, title_size, title_color or P["ink"], align=align, weight=700, group=g)
        used = 12 + title_size * LH * len(title.split("\n"))
        if body:
            self.text(tx, y + used + 6, body, body_size, P["ink"], align=align, mono=mono_body, group=g)
            used += 6 + body_size * LH * len(body.split("\n"))
            for line in body.split("\n"):
                if tw(line, body_size, mono_body) > w - 28:
                    WARN.append(f"{self.name}:{key} 넓이 초과 '{line[:30]}…'")
        for line in title.split("\n"):
            if tw(line, title_size) > w - 28:
                WARN.append(f"{self.name}:{key} 제목 넓이 초과")
        if used > h - 4:
            WARN.append(f"{self.name}:{key} 높이 초과 {used:.0f}>{h}")

    def pill(self, key, x, y, w, h, text, bg, stroke, size=14, mono=False):
        e = self.rect(key, x, y, w, h, bg, stroke)
        t = self.text(x + w / 2, y + h / 2, text, size, P["ink"], align="center", valign="middle",
                      container=e["id"], mono=mono)
        e["boundElements"].append({"type": "text", "id": t["id"]})
        for line in text.split("\n"):
            if tw(line, size, mono) > w - 12:
                WARN.append(f"{self.name}:{key} pill 넓이 초과 '{line}'")
        return e

    def anchor(self, key, side, t=0.5):
        x, y, w, h = self.boxes[key]
        return {"n": (x + w * t, y), "s": (x + w * t, y + h), "w": (x, y + h * t), "e": (x + w, y + h * t)}[side]

    def arrow(self, pts, color, label=None, dashed=False, start=None, end=None, both=False, sw=2,
              label_size=13, head=True, label_at=None):
        self.colors.add(color)
        x0, y0 = pts[0]
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        e = self._base("arrow" if head else "line", x0, y0, max(xs) - min(xs), max(ys) - min(ys), color,
                       "transparent", sw=sw, dashed=dashed, rounded=False)
        e.update({"points": [[px - x0, py - y0] for px, py in pts], "lastCommittedPoint": None,
                  "startArrowhead": "arrow" if (both and head) else None,
                  "endArrowhead": "arrow" if head else None, "elbowed": False})
        if head:
            for k, side in ((start, "startBinding"), (end, "endBinding")):
                if k:
                    e[side] = {"elementId": self.rect_el[k]["id"], "focus": 0, "gap": 6}
                    self.rect_el[k]["boundElements"].append({"type": "arrow", "id": e["id"]})
                else:
                    e[side] = None
        d = "M " + " L ".join(f"{px:.1f} {py:.1f}" for px, py in pts)
        mid = f"url(#ah{color[1:]})"
        da = ' stroke-dasharray="8 6"' if dashed else ""
        marks = (f' marker-end="{mid}"' if head else "") + (f' marker-start="{mid}"' if both and head else "")
        self.lines.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{sw}"{da}{marks}/>')
        if label:
            n = len(pts)
            if label_at:                 # 라벨 자리를 직접 정한다 (화살표끼리 라벨이 겹칠 때)
                lx, ly = label_at
            elif n % 2:
                lx, ly = pts[n // 2]
            else:
                (ax, ay), (bx, by) = pts[n // 2 - 1], pts[n // 2]
                lx, ly = (ax + bx) / 2, (ay + by) / 2
            lines = label.split("\n")
            lw = max(tw(l, label_size) for l in lines) + 12
            lh = len(lines) * label_size * LH + 6
            self.texts.append(f'<rect x="{lx - lw / 2:.1f}" y="{ly - lh / 2:.1f}" width="{lw:.1f}" height="{lh:.1f}" '
                              f'rx="4" fill="#ffffff" fill-opacity="0.95"/>')
            t = self.text(lx, ly, label, label_size, color, align="center", valign="middle", container=e["id"])
            e["boundElements"].append({"type": "text", "id": t["id"]})
        return e

    def line(self, pts, color, dashed=True, sw=1.5):
        return self.arrow(pts, color, dashed=dashed, sw=sw, head=False)

    # ── 출력 ──
    def save(self):
        doc = {"type": "excalidraw", "version": 2, "source": "oauth-oidc-playground/docs/diagrams",
               "elements": self.ex, "appState": {"viewBackgroundColor": "#ffffff", "gridSize": None}, "files": {}}
        (self.out / f"{self.name}.excalidraw").write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
        markers = "".join(
            f'<marker id="ah{c[1:]}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" '
            f'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{c}"/></marker>' for c in sorted(self.colors))
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
               f'viewBox="0 0 {self.w} {self.h}"><defs>{markers}</defs>'
               f'<rect width="100%" height="100%" fill="#ffffff"/>'
               + "".join(self.shapes) + "".join(self.lines) + "".join(self.texts) + "</svg>")
        (self.out / f"{self.name}.svg").write_text(svg, encoding="utf-8")
        print(f"  {self.name}: {len(self.ex)} elements")


def timeline(name, title, sub, steps, arrows=(), verdict=None, vtitle=None, vcolor="bad",
             level="READ COMMITTED", level_b=None, out=None, width=1160, lane=28):
    """두 세션(A · B) 타임라인 — 블로그형 문서의 기본 그림.

    steps:  [(side, sql, note, kind)]   side "A" | "B" · kind None | "bad"(빨강 — 문제가 생기는 곳) | "ok"(초록)
    arrows: [(i, j, label)] 또는 [(i, j, label, frac)]
            i 번 카드 → j 번 카드 (반대 열). label 은 화살표의 뜻 — 한 줄 9자 안팎 · 두 줄까지 ("\n").
            frac = 라벨을 세로 구간의 어디에 둘지(0 = i 쪽, 1 = j 쪽, 기본 0.5) — 화살표가 둘 이상이면 서로 다르게.
    verdict/vtitle: 맨 아래 결론 카드 (vcolor "bad" | "ok" | "note")
    """
    ca, cw_, cb = 60, 440, 660                     # 열 A x · 카드 폭 · 열 B x — 가운데 통로 500~660 에 라벨이 들어간다
    top, pitch, ch = 150, 84, 68
    n = len(steps)
    h = top + n * pitch + (150 if verdict else 30)
    d = Diagram(name, width, h, title, sub, out=out)
    d.pill("hA", ca, 96, cw_, 38, f"세션 A  ({level})", P["as_bg"], P["front"], size=15)
    d.pill("hB", cb, 96, cw_, 38, f"세션 B  ({level_b or level})", P["bff_bg"], P["back"], size=15)
    d.arrow([(30, 150), (30, top + n * pitch - 10)], P["muted"], sw=2)
    d.text(30, 118, "시간", 14, P["muted"], align="center")
    for i, (side, sql, note, kind) in enumerate(steps):
        x = ca if side == "A" else cb
        y = top + i * pitch
        if kind == "bad":
            bg, st = P["bad_bg"], P["red"]
        elif kind == "ok":
            bg, st = P["ok_bg"], P["green"]
        else:
            bg, st = (P["as_bg"], P["front"]) if side == "A" else (P["bff_bg"], P["back"])
        d.card(f"s{i}", x, y, cw_, ch, sql, note, bg=bg, stroke=st, title_size=15, body_size=14,
               sw=3 if kind == "bad" else 2)
    k = len(arrows)
    for idx, a in enumerate(arrows):
        i, j, label = a[0], a[1], a[2]
        frac = a[3] if len(a) > 3 else 0.5
        gx = 580 + (idx - (k - 1) / 2) * lane        # 화살표가 여럿이면 통로 안에서 나란히
        yi, yj = top + i * pitch + ch / 2, top + j * pitch + ch / 2
        if steps[i][0] == "A":
            pts = [(ca + cw_, yi), (gx, yi), (gx, yj), (cb, yj)]
        else:
            pts = [(cb, yi), (gx, yi), (gx, yj), (ca + cw_, yj)]
        d.arrow(pts, P["red"], label=label, start=f"s{i}", end=f"s{j}", label_size=12,
                label_at=(gx, yi + (yj - yi) * frac) if label else None)
    if verdict:
        vy = top + n * pitch + 6
        bg, st = {"bad": (P["bad_bg"], P["red"]), "ok": (P["ok_bg"], P["green"])}.get(vcolor, (P["note_bg"], P["line"]))
        d.card("v", ca, vy, cb + cw_ - ca, 112, vtitle, verdict, bg=bg, stroke=st, title_size=16, body_size=14,
               title_color=st if vcolor != "note" else None)
    d.save()
    return d


def legend(d, x, y, items):
    """items: [(color, dashed, text)]"""
    for i, (c, dashed, label) in enumerate(items):
        yy = y + i * 26
        d.line([(x, yy + 9), (x + 46, yy + 9)], c, dashed=dashed, sw=3)
        d.text(x + 56, yy, label, 14, P["ink"])




def finish():
    """레이아웃 경고(넓이·높이 초과)를 찍는다. 경고가 있으면 PNG 로 렌더링해서 눈으로 확인할 것:
    rsvg-convert -w 1400 x.svg -o /tmp/x.png"""
    if WARN:
        print("레이아웃 경고")
        for w in WARN:
            print("   ", w)
