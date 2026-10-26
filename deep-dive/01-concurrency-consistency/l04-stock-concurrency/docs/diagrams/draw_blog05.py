#!/usr/bin/env python3
"""01.04 블로그판 05 그림. 실행: python3 -I docs/diagrams/draw_blog05.py (레슨 폴더에서)"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[4] / "tools"))
from diagram import Diagram, P, finish  # noqa: E402

OUT = pathlib.Path(__file__).parent


def intro():
    d = Diagram("blog05-intro", 1460, 460, "한 행에 몰리는 요청 — 핫 로우 (hot row)",
                "선착순 이벤트: 한 상품에 수많은 사람이 동시에 주문한다", out=OUT)
    for i in range(4):
        d.pill(f"r{i}", 40, 120 + i * 62, 220, 50, f"요청 {i + 1}", P["as_bg"], P["front"], size=15)
    d.text(110, 372, "... 수만 명", 15, P["muted"])
    d.card("row", 520, 160, 340, 140, "재고 행 하나", "세 전략 모두 같은 행에 쓰려면\n행 락을 순서대로 얻어야 한다", bg=P["bad_bg"], stroke=P["red"], title_size=18, body_size=14)
    for i in range(4):
        d.arrow([(260, 145 + i * 62), (520, 230)], P["muted"])
    d.card("q", 960, 110, 460, 250, "그 결과", "줄을 선 요청이 커넥션 · CPU 를 점유한다\n\n서버를 늘려도 한 행은 직렬이다\n\n전략 이름을 아는 것과\n병목을 설명하는 것은 다르다",
           bg=P["note_bg"], stroke=P["line"], title_size=18, body_size=15)
    d.arrow([(860, 230), (960, 230)], P["red"])
    d.save()


def compare():
    d = Diagram("blog05-compare", 1460, 640, "세 전략 한눈에 비교",
                "같은 행 하나에서는 모두 줄을 선다. 갈리는 것은 무엇이 낭비되나", out=OUT)
    heads = ["", "원자 조건부 UPDATE", "비관 락  FOR UPDATE", "낙관 락  version"]
    xs = [40, 270, 650, 1030]
    ws = [220, 370, 370, 390]
    for i, h in enumerate(heads):
        if h:
            d.pill(f"h{i}", xs[i], 100, ws[i], 46, h, P["note_bg"], P["line"], size=15)
    rows = [("틈", ["없다 (한 문장)", "있지만 잠가서\n끼어들 수 없다", "있고 끼어들 수 있다\n쓸 때 감지"]),
            ("왕복", ["1", "3 (읽기 · 쓰기 · 커밋)", "2 (읽기 · 쓰기)\n+ 충돌 때마다 +2"]),
            ("락 보유", ["UPDATE 문장 ~ 커밋", "읽기 ~ 커밋\n(앱 로직 포함)", "UPDATE ~ 커밋"]),
            ("진 쪽", ["기다린 뒤 최신 값으로\n재평가, 다시 할 일 없음", "기다린 뒤 최신 값을\n읽고 진행", "0 행 → 읽기부터\n전부 다시 (버려지는 일)"]),
            ("실패 신호", ["영향 행 0 (품절)", "재고 부족 (앱 판단)", "영향 행 0 (충돌)\n상한 초과 예외"]),
            ("맞는 곳", ["단순 증감 · 기본값", "읽고 복잡하게 판단한 뒤\n쓰기 · 경합 높음", "읽기와 쓰기 사이가 긴 편집\n충돌 드묾"])]
    cols = [(P["ok_bg"], P["green"]), (P["rs_bg"], P["orange"]), (P["as_bg"], P["front"])]
    for r, (name, cells) in enumerate(rows):
        y = 156 + r * 78
        d.pill(f"n{r}", xs[0], y, ws[0], 68, name, P["note_bg"], P["line"], size=15)
        for c, t in enumerate(cells):
            d.pill(f"c{r}{c}", xs[c + 1], y, ws[c + 1], 68, t, cols[c][0], cols[c][1], size=14)
    d.save()


def waste():
    d = Diagram("blog05-waste", 1460, 400, "줄 선 동안 무엇이 낭비되나",
                "세 전략 모두 같은 행 하나에서는 줄을 선다. 차이는 낭비되는 것이다", out=OUT)
    cs = [("원자 조건부 UPDATE", "거의 없음", "락 보유가 문장 하나라서\n기다린 쪽도 다시 할 일이 없다", P["ok_bg"], P["green"]),
          ("비관 락", "락 보유 시간", "읽기부터 COMMIT 까지\n뒤의 줄이 그만큼 길어진다", P["rs_bg"], P["orange"]),
          ("낙관 락", "진 쪽의 읽기와 계산 전부", "0 행이면 버리고 처음부터\n재시도 폭풍이 날 수 있다", P["bad_bg"], P["red"])]
    for i, (t, w, b, bg, st) in enumerate(cs):
        d.card(f"c{i}", 40 + i * 470, 110, 440, 230, t, f"낭비: {w}\n\n{b}", bg=bg, stroke=st, title_size=18, body_size=16)
    d.save()


def decision():
    d = Diagram("blog05-decision", 1460, 560, "선택 순서 (해석 — 위 근거를 엮은 판단)",
                "위에서 아래로 내려가며 처음 맞는 것을 고른다", out=OUT)
    qs = [("1  조건 하나 + 증감인가?", "원자 UPDATE  (02)", P["ok_bg"], P["green"]),
          ("2  읽은 값으로 앱이 복잡한 판단을 하고\n한 문장으로 못 쓰고, 짧은 트랜잭션인가?", "비관 락  (03)\n락 구간에 외부 호출 금지", P["rs_bg"], P["orange"]),
          ("3  읽은 시점과 쓰는 시점이 다른 트랜잭션이거나\n충돌이 드문 쓰기인가?", "낙관 락  (04)", P["as_bg"], P["front"]),
          ("4  한 행에 몰리는 차감인가?", "1 이 기본 — 그것으로도 모자라면\n핫 로우 대안으로 간다", P["bad_bg"], P["red"])]
    for i, (q, a, bg, st) in enumerate(qs):
        y = 110 + i * 108
        d.pill(f"q{i}", 40, y, 760, 84, q, P["note_bg"], P["line"], size=15)
        d.pill(f"a{i}", 960, y, 460, 84, a, bg, st, size=15)
        d.arrow([(800, y + 42), (960, y + 42)], st, "그렇다", start=f"q{i}", end=f"a{i}", label_size=13)
        if i < 3:
            d.arrow([(420, y + 84), (420, y + 108)], P["muted"], "아니다", label_size=12, label_at=(470, y + 96))
    d.save()


def columns():
    d = Diagram("blog05-columns", 1460, 520, "관찰 테스트 표의 칸 읽는 법",
                "StockObservationTest 는 단언 없이 표를 찍는다", out=OUT)
    cols = [("성공 · 품절", "reserve 가 true / false\n를 돌려준 수"),
            ("재시도소진", "reserve 가 예외를 던진 수\n재고가 남았는데 상한(20)을\n넘겨 포기한 구매자 (낙관 락만)"),
            ("남은재고", "초기 재고 - 성공 수\n와 같아야 한다 (불변식, 01)"),
            ("재시도", "낙관 락이 version 충돌로\n다시 읽은 총 횟수"),
            ("걸린ms", "구매자 N 명이 동시에 시작해\n모두 끝날 때까지")]
    for i, (t, b) in enumerate(cols):
        d.card(f"c{i}", 40 + i * 280, 110, 265, 180, t, b, bg=P["note_bg"] if i != 1 else P["bad_bg"], stroke=P["line"] if i != 1 else P["red"], title_size=17, body_size=13)
    sc = [("경합 낮음", "구매자 4 · 재고 1000"), ("경합 높음", "구매자 50 · 재고 1000"), ("품절 경쟁", "구매자 50 · 재고 10")]
    for i, (t, b) in enumerate(sc):
        d.card(f"s{i}", 40 + i * 470, 330, 440, 90, t, b, bg=P["as_bg"], stroke=P["front"], title_size=17, body_size=15)
    d.text(40, 450, "숫자는 실행마다 다르다 — 절대 값이 아니라 모양을 본다", 16, P["red"], weight=700)
    d.save()


def serial():
    d = Diagram("blog05-serial", 1460, 470, "같은 행의 처리량은 락 보유 시간에 묶인다 (해석)",
                "서버를 늘려도 한 행의 갱신은 줄을 서서 하나씩 지나간다", out=OUT)
    d.text(40, 110, "서버 1 대", 16, P["ink"], weight=700)
    d.text(40, 250, "서버 3 대", 16, P["ink"], weight=700)
    for row, y in ((0, 140), (1, 280)):
        for i in range(5):
            d.pill(f"b{row}{i}", 40 + i * 270, y, 250, 56, f"락 보유 + 커밋  ({chr(65 + i)})", P["rs_bg"], P["orange"], size=14)
    d.card("n", 40, 370, 1380, 70, "한 건의 락 보유 시간 + 커밋 = 한 칸. 같은 행의 처리량은 이 칸의 역수에 묶인다 — 서버 수와 무관하다", None,
           bg=P["note_bg"], stroke=P["line"], title_size=15)
    d.save()


def buckets():
    d = Diagram("blog05-buckets", 1460, 480, "대안 1 — 재고 버킷 분할 (해석 / 일반 설계)",
                "재고 1000 을 10 개 행(버킷)에 100 씩 나눈다. 이 레슨에서 구현 · 실측하지 않았다", out=OUT)
    for i in range(4):
        d.pill(f"r{i}", 40, 120 + i * 62, 200, 50, f"구매자 {i + 1}", P["as_bg"], P["front"], size=15)
    for i in range(4):
        d.pill(f"k{i}", 480, 120 + i * 62, 300, 50, f"버킷 {i + 1}  (100)", P["ok_bg"], P["green"], size=15)
        d.arrow([(240, 145 + i * 62), (480, 145 + i * 62)], P["green"])
    d.text(480, 375, "... 버킷 10 개", 15, P["muted"])
    d.card("g", 860, 110, 560, 110, "얻는 것", "줄이 10 개로 나뉜다", bg=P["ok_bg"], stroke=P["green"], title_size=17, body_size=15)
    d.card("c", 860, 250, 560, 200, "대가", "총재고 조회는 합계다\n마지막 재고가 버킷마다 흩어져\n한 버킷이 비면 다른 버킷을 시도해야 한다\n버킷 선택에 SKIP LOCKED 를 쓰는 변형이 있으나\n문서는 범용에 부적합하다고 한다",
           bg=P["bad_bg"], stroke=P["red"], title_size=17, body_size=14)
    d.save()


def queue():
    d = Diagram("blog05-queue", 1460, 420, "대안 2 — 큐로 직렬화 (해석 / 일반 설계)",
                "같은 SKU 의 요청을 한 소비자가 순서대로 처리하게 모은다. 이 레슨에서 확인하지 않았다", out=OUT)
    d.pill("r", 40, 130, 220, 80, "요청들\n(SKU 를 키로)", P["as_bg"], P["front"], size=15)
    d.pill("q", 340, 130, 300, 80, "큐\n(같은 SKU = 한 줄)", P["note_bg"], P["muted"], size=15)
    d.pill("c", 720, 130, 260, 80, "소비자 1 개\n순서대로 처리", P["rs_bg"], P["orange"], size=15)
    d.pill("d", 1060, 130, 360, 80, "DB 원자 UPDATE\n(마지막 방어선)", P["ok_bg"], P["green"], size=15)
    d.arrow([(260, 170), (340, 170)], P["muted"])
    d.arrow([(640, 170), (720, 170)], P["muted"])
    d.arrow([(980, 170), (1060, 170)], P["muted"])
    d.card("g", 40, 250, 680, 130, "얻는 것", "DB 행 락 경합이 없고 대기가 큐에서 일어난다", bg=P["ok_bg"], stroke=P["green"], title_size=16, body_size=14)
    d.card("c2", 740, 250, 680, 130, "대가", "응답이 비동기(접수 → 결과 통지)가 된다\n큐 순서 보장 범위는 큐 제품의 문서로 확인해야 한다", bg=P["bad_bg"], stroke=P["red"], title_size=16, body_size=14)
    d.save()


def reservation():
    d = Diagram("blog05-reservation", 1460, 440, "대안 3 — 예약(reservation) + 만료 (해석 / 일반 설계)",
                "\"재고를 잡는다\" 와 \"결제로 확정한다\" 를 나눈다. 이 레슨에서 구현하지 않았다", out=OUT)
    d.pill("a", 40, 130, 340, 90, "재고 잡기\nreserved 수량을 올리고\n만료 시각을 둔다", P["as_bg"], P["front"], size=14)
    d.pill("b", 480, 130, 340, 90, "결제 대기\n(이 동안 락을 쥐지 않는다)", P["note_bg"], P["muted"], size=14)
    d.pill("c", 920, 60 + 70, 500, 40, "결제 성공 → 확정", P["ok_bg"], P["green"], size=14)
    d.pill("e", 920, 190, 500, 40, "결제 안 됨 → 만료 처리로 돌려 놓는다", P["bad_bg"], P["red"], size=14)
    d.arrow([(380, 175), (480, 175)], P["muted"])
    d.arrow([(820, 175), (920, 150)], P["green"])
    d.arrow([(820, 175), (920, 210)], P["red"])
    d.card("g", 40, 270, 680, 110, "얻는 것", "결제 대기 시간 동안 락을 쥐지 않는다", bg=P["ok_bg"], stroke=P["green"], title_size=16, body_size=14)
    d.card("c2", 740, 270, 680, 110, "대가", "만료 작업 · 이중 처리 방지 · 보상 로직이 생긴다\n재고 = 가용 + 예약 의 두 숫자를 일관되게 관리해야 한다", bg=P["bad_bg"], stroke=P["red"], title_size=16, body_size=14)
    d.save()


if __name__ == "__main__":
    for f in (intro, compare, waste, decision, columns, serial, buckets, queue, reservation):
        f()
    finish()
