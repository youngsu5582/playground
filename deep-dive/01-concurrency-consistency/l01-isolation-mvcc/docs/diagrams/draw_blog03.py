#!/usr/bin/env python3
"""01.01 블로그판 03 그림. 실행: python3 -I docs/diagrams/draw_blog03.py (레슨 폴더에서)"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[4] / "tools"))
from diagram import Diagram, P, finish, timeline as _timeline  # noqa: E402

OUT = pathlib.Path(__file__).parent


def timeline(*a, **k):
    return _timeline(*a, out=OUT, **k)


def intro():
    timeline("blog03-intro", "도입: 한 서비스 메서드 안의 쿼리 두 번",
             "재고 12 인 행 (id = 3). A 는 기본 수준으로 한 트랜잭션 안에서 같은 행을 두 번 읽는다",
             [("A", "1  SELECT stock WHERE id = 3", "본 값: 12", None),
              ("B", "2  UPDATE stock = 9  → COMMIT", "A 의 두 쿼리 사이에 커밋", None),
              ("A", "3  SELECT stock WHERE id = 3", "본 값: 9  (같은 트랜잭션 · 같은 쿼리)", "bad")],
             [(1, 2, "B 의 커밋이\n두 번째 쿼리에 보인다")],
             "두 쿼리가 서로 다른 세상을 봤다. 그 세상을 정하는 것이 스냅샷이고, 이 수준은 쿼리마다 새로 잡는다.\n"
             "수준을 바꾸면 이 장면이 달라진다 — 스냅샷을 \"언제\" 잡느냐가 격리수준을 가르는 지점이다.",
             "같은 트랜잭션인데 답이 바뀐다")


def begin_lag():
    timeline("blog03-begin-lag", "REPEATABLE READ — 스냅샷은 BEGIN 이 아니라 첫 문장에서 잡힌다",
             "재고 30 인 행 (id = 5). A 는 BEGIN 만 해 두고 한참 뒤에 첫 SELECT 를 한다",
             [("A", "1  BEGIN", "아직 스냅샷이 없다", None),
              ("B", "2  UPDATE stock = 28  → COMMIT", "A 가 BEGIN 한 뒤의 커밋", None),
              ("A", "3  SELECT stock WHERE id = 5", "본 값: 28 — 첫 문장이 스냅샷을 잡는다", "bad"),
              ("B", "4  UPDATE stock = 25  → COMMIT", "스냅샷을 잡은 뒤의 커밋", None),
              ("A", "5  SELECT stock WHERE id = 5", "본 값: 28 — 고정된 스냅샷", "ok")],
             [(1, 2, "BEGIN 뒤의 커밋도\n스냅샷에 들어온다", 0.7), (3, 4, "스냅샷 뒤의 커밋은\n안 보인다", 0.5)],
             "BEGIN 은 스냅샷 시점이 아니다. 앱이 BEGIN 만 하고 한참 뒤에 첫 문장을 보내면 그동안의 커밋은 보인다.\n"
             "첫 문장이 스냅샷을 잡은 다음부터는 이후의 커밋이 모두 가려진다.",
             "스냅샷 시점 = 첫 번째 (트랜잭션 제어문이 아닌) 문장의 시작", level="REPEATABLE READ", level_b="autocommit")


def snapshot_anatomy():
    d = Diagram("blog03-snapshot-anatomy", 1400, 600, "스냅샷 한 줄 읽기 — 200:210:200,204,207",
                "pg_current_snapshot() 의 형식은 xmin:xmax:xip_list. 숫자는 설명용이고, 상자 하나가 트랜잭션 ID 하나다", out=OUT)
    ids = list(range(198, 214))
    xip = {200, 204, 207}
    bw = 80
    for i, t in enumerate(ids):
        x = 40 + i * (bw + 2)
        if t < 200:
            bg, st, lab = P["ok_bg"], P["green"], "끝남"
        elif t >= 210:
            bg, st, lab = P["note_bg"], P["muted"], "안 보임"
        elif t in xip:
            bg, st, lab = P["bad_bg"], P["red"], "진행 중"
        else:
            bg, st, lab = P["as_bg"], P["front"], "끝남"
        d.pill(f"t{t}", x, 130, bw, 66, f"{t}\n{lab}", bg, st, size=13)
    d.text(40, 214, "xmin = 200 보다 작은 ID: 전부 끝났다", 14, P["green"])
    d.text(40 + 12 * 82, 214, "xmax = 210 이상:", 14, P["muted"])
    d.text(40 + 12 * 82, 234, "아직 안 끝났다 -> 안 보인다", 14, P["muted"])
    d.text(40 + 3 * 82, 254, "xmin <= ID < xmax 이면서 xip 에 없다 = 이미 끝났다 (커밋이면 보이고, 롤백이면 죽었다)", 14, P["front"])
    cs = [("xmin = 200", "아직 진행 중이던 가장 작은 트랜잭션 ID\n이보다 작은 ID 는 전부 끝났다", P["ok_bg"], P["green"]),
          ("xmax = 210", "끝난 트랜잭션 ID 의 최댓값 + 1\n이 이상의 ID 는 스냅샷 시점에 안 끝났다 -> 안 보인다", P["note_bg"], P["muted"]),
          ("xip_list = 200,204,207", "스냅샷 시점에 진행 중이던 트랜잭션들\n목록에 있으면 안 끝난 것, 없으면 끝난 것", P["bad_bg"], P["red"])]
    for i, (t, b, bg, st) in enumerate(cs):
        d.card(f"c{i}", 40 + i * 450, 310, 430, 120, t, b, bg=bg, stroke=st, title_size=16, body_size=14)
    d.card("n", 40, 460, 1320, 100, "읽는 것은 데이터 복사본이 아니라 \"이 트랜잭션들은 끝났고 이 트랜잭션들은 아직이다\" 라는 기록이다",
           "튜플은 그대로 두고, 읽을 때마다 \"이 튜플을 만든 트랜잭션이 내 스냅샷 기준으로 끝났나\" 를 묻는다\n"
           "함수들은 64비트 xid8 를 쓴다 (튜플 안의 32비트 xid 와 다르다)",
           bg=P["todo_bg"], stroke=P["orange"], title_size=15, body_size=14)
    d.save()


def two_xmins():
    d = Diagram("blog03-two-xmins", 1400, 330, "이름만 같은 두 xmin",
                "튜플의 xmin 과 스냅샷의 xmin 은 다른 것이다", out=OUT)
    d.card("a", 40, 110, 640, 150, "튜플의 xmin  (t_xmin)",
           "이 버전을 만든 트랜잭션 ID\n튜플 헤더에 있다 (xmin · xmax · ctid)\n\"이 버전은 누가 만들었나\"",
           bg=P["as_bg"], stroke=P["front"], title_size=17, body_size=15)
    d.card("b", 720, 110, 640, 150, "스냅샷의 xmin  (xmin:xmax:xip 의 첫 값)",
           "스냅샷 시점에 아직 진행 중이던 가장 작은 트랜잭션 ID\npg_current_snapshot() 이 돌려주는 값\n\"여기보다 작은 ID 는 전부 끝났다\"",
           bg=P["bff_bg"], stroke=P["back"], title_size=17, body_size=15)
    d.save()


def when_snapshot():
    d = Diagram("blog03-when-snapshot", 1400, 520, "스냅샷은 언제 잡히나 — 격리수준이 갈리는 지점",
                "같은 순서의 문장 BEGIN -> SELECT -> SELECT -> SELECT 를 세 수준에서 본다. 깃발 = 새 스냅샷", out=OUT)
    lanes = [("READ COMMITTED", "문장이 시작할 때마다 새로", [0, 1, 1, 1], P["ok_bg"], P["green"]),
             ("REPEATABLE READ", "첫 문장에서 한 번, 이후 고정", [0, 1, 0, 0], P["as_bg"], P["front"]),
             ("SERIALIZABLE", "REPEATABLE READ 와 같다 (+ 충돌 감시)", [0, 1, 0, 0], P["bff_bg"], P["back"])]
    labels = ["BEGIN", "SELECT 1", "SELECT 2", "SELECT 3"]
    for r, (lv, sub, flags, bg, st) in enumerate(lanes):
        y = 120 + r * 120
        d.card(f"l{r}", 40, y, 300, 90, lv, sub, bg=bg, stroke=st, title_size=16, body_size=13)
        for c, (lab, f) in enumerate(zip(labels, flags)):
            x = 400 + c * 240
            if c == 0:
                d.pill(f"p{r}{c}", x, y + 20, 160, 50, lab, P["white"], P["line"], size=14)
            else:
                d.pill(f"p{r}{c}", x, y + 20, 160, 50, lab, P["white"], st, size=14)
            if f:
                d.pill(f"f{r}{c}", x + 30, y - 12, 100, 28, "스냅샷", P["todo_bg"], P["orange"], size=12)
        if r == 0:
            pass
    d.arrow([(400, 480), (1360, 480)], P["muted"], "시간")
    d.save()


def nonblocking():
    d = Diagram("blog03-nonblocking", 1400, 600, "읽기는 쓰기를 막지 않는다 — 세 층에서",
                "읽기는 튜플 헤더와 스냅샷만 비교한다. 락 층에서도 읽기의 락은 쓰기의 락과 충돌하지 않는다", out=OUT)
    cs = [("튜플 판정", "읽기가 하는 일은\n튜플 헤더와 스냅샷 비교뿐\n행 단위에서 일반 읽기가\n락을 기다릴 일은 없다", P["ok_bg"], P["green"], "문서 13.1"),
          ("행 락", "행 락은 데이터 조회에\n영향을 주지 않는다\n같은 행의 쓰는 쪽과\n잠그는 쪽만 막는다", P["as_bg"], P["front"], "문서 13.3.2"),
          ("테이블 락", "SELECT 가 잡는 ACCESS SHARE 는\nACCESS EXCLUSIVE 와만 충돌한다\nACCESS EXCLUSIVE = ALTER TABLE 류\nDDL 이 잡는 락", P["bff_bg"], P["back"], "문서 13.3.1")]
    for i, (t, b, bg, st, src) in enumerate(cs):
        d.card(f"c{i}", 40 + i * 450, 110, 420, 190, t + f"   ({src})", b, bg=bg, stroke=st, title_size=16, body_size=14)
    d.text(40, 330, "예외 — 읽기가 막히거나 쓰기와 부딪히는 경우", 17, P["red"], weight=700)
    ex = [("행 단위", "SELECT ... FOR UPDATE/SHARE 는\n쓰는 쪽과 충돌한다 (문서 13.3.2)"),
          ("테이블 단위", "ACCESS EXCLUSIVE (DDL · VACUUM FULL)\n는 SELECT 의 ACCESS SHARE 와 충돌 (문서 13.3.1)"),
          ("SERIALIZABLE", "READ ONLY DEFERRABLE 은 안전한 스냅샷을\n얻을 때까지 시작이 블록된다 (문서 13.2.3)")]
    for i, (t, b) in enumerate(ex):
        d.card(f"e{i}", 40 + i * 450, 370, 420, 120, t, b, bg=P["bad_bg"], stroke=P["red"], title_size=15, body_size=14)
    d.card("n", 40, 520, 1320, 56, "읽기에 비용이 없다는 말은 아니다 — 스냅샷 판정 비용이 있고(해석), 무엇보다 열린 스냅샷이 VACUUM 을 막는다 (06)", None,
           bg=P["note_bg"], stroke=P["line"], title_size=14)
    d.save()


def measured():
    d = Diagram("blog03-measured", 1400, 520, "실측 — RC 는 문장마다 새 스냅샷, RR 은 고정",
                "T1(753) 이 열려 있는 동안 읽은 스냅샷 (psql 2026-10-13). 읽는 법: xmin = 753 은 T1 이 열려 있어서다", out=OUT)
    d.pill("h0", 40, 110, 520, 46, "시점", P["note_bg"], P["line"], size=14)
    d.pill("h1", 570, 110, 300, 46, "스냅샷", P["note_bg"], P["line"], size=14)
    d.pill("h2", 880, 110, 480, 46, "읽은 balance", P["note_bg"], P["line"], size=14)
    rows = [("바깥이 balance = 50 UPDATE (754) 직후, RR 은 BEGIN 만 한 상태", "753:755:753", "—", None),
            ("RR 의 첫 SELECT (BEGIN 보다 한참 뒤)", "753:755:753", "50 — BEGIN 뒤의 커밋이 보였다", None),
            ("바깥이 balance = 20 UPDATE (755) 한 뒤 RR 의 두 번째 SELECT", "753:755:753 (그대로)", "50", None),
            ("RC 의 첫 SELECT", "753:755:753", "50", None),
            ("RC 의 두 번째 SELECT", "753:756:753 (xmax 가 올랐다)", "20", "bad")]
    for i, (a, b, c, k) in enumerate(rows):
        y = 168 + i * 62
        bg, st = (P["bad_bg"], P["red"]) if k else (P["white"], P["line"])
        d.pill(f"a{i}", 40, y, 520, 52, a, P["white"], P["line"], size=13)
        d.pill(f"b{i}", 570, y, 300, 52, b, bg, st, size=14, mono=True)
        d.pill(f"c{i}", 880, y, 480, 52, c, bg, st, size=14)
    d.text(40, 490, "RC 는 문장마다 스냅샷을 새로 잡아 xmax 가 따라 올라갔고 (755 -> 756), RR 은 고정이다. xmax = 755 는 \"끝난 ID 의 최댓값(754) + 1\"", 14, P["muted"])
    d.save()


def mysql():
    d = Diagram("blog03-mysql", 1400, 430, "InnoDB — 같은 트랜잭션 안의 서로 다른 세계",
                "읽는 방법에 따라 스냅샷을 보기도 하고 최신 데이터를 보기도 한다 (MySQL 8.0)", out=OUT)
    cs = [("일반 SELECT\n(일관된 읽기)", "스냅샷을 읽고 락을 안 건다\nRR: 트랜잭션 안 첫 일관된 읽기가 세운 스냅샷\nRC: 일관된 읽기마다 새 스냅샷", P["ok_bg"], P["green"]),
          ("SELECT ... FOR UPDATE/SHARE\n(잠그는 읽기)", "스냅샷이 아닌 \"최신 데이터\" 를 읽고\n락을 건다", P["bad_bg"], P["red"]),
          ("UPDATE / DELETE\n(DML)", "스냅샷은 DML 에 적용되지 않는다\nRR 에서도 방금 커밋된 행에 영향을 줄 수 있고\n그 변경은 이후 이 트랜잭션에서 보인다", P["bff_bg"], P["back"])]
    for i, (t, b, bg, st) in enumerate(cs):
        d.card(f"c{i}", 40 + i * 450, 110, 420, 190, t, b, bg=bg, stroke=st, title_size=15, body_size=14)
    d.card("n", 40, 330, 1320, 70, "PostgreSQL RR 은 같은 UPDATE 상황에서 40001 로 실패한다 (04)  ·  일반 SELECT 와 FOR UPDATE 가 같은 트랜잭션에서 다른 세계를 볼 수 있다",
           None, bg=P["note_bg"], stroke=P["line"], title_size=14)
    d.save()


if __name__ == "__main__":
    for f in (intro, begin_lag, snapshot_anatomy, two_xmins, when_snapshot, nonblocking, measured, mysql):
        f()
    finish()
