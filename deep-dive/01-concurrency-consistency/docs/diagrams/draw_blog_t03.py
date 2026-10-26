#!/usr/bin/env python3
"""01 트랙 블로그판 03 (도구 고르기) 그림. 실행: python3 -I docs/diagrams/draw_blog_t03.py (트랙 폴더에서)"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from blog_common import Diagram, P, finish, tw, kc, vchain, hchain, sequence, matrix, new, card_h, ARROW  # noqa: E402


def intro():
    d = new("blog-t03-intro", 1400, 560, "같은 증상, 다른 처방",
            "\"가끔 중복 · 가끔 음수 · 가끔 500\" — 증상은 같아도 원인의 모양에 따라 도구가 달라진다")
    d.card("sym", 40, 200, 300, 150, "증상", "가끔 중복\n가끔 음수\n가끔 500", bg=P["bad_bg"], stroke=P["red"], title_size=17, body_size=15)
    causes = [("틈 — 읽고 나서 쓰는 사이", "같은 행을 읽고 계산해 덮어쓴다", "원자 UPDATE · 락", "a", 110),
              ("다른 행 write skew", "같은 근거를 읽고 서로 다른 행을 고친다", "SERIALIZABLE + 재시도", "warn", 250),
              ("재전달", "같은 요청 · 이벤트가 두 번 온다", "유니크 키 · inbox · version", "ok", 390)]
    for i, (t, b, c, k, y) in enumerate(causes):
        bg, st = kc(k)
        d.card(f"c{i}", 460, y, 520, 110, t, b, bg=bg, stroke=st, title_size=16, body_size=14)
        d.pill(f"t{i}", 1060, y + 25, 300, 60, c, P["white"], st, size=15)
        d.arrow([(340, 275), (400, 275), (400, y + 55), (460, y + 55)], ARROW[k], None, start="sym", end=f"c{i}")
        d.arrow([(980, y + 55), (1060, y + 55)], ARROW[k], "처방", start=f"c{i}", end=f"t{i}")
    d.save()


def skeleton():
    d = hchain("blog-t03-skeleton", "답의 뼈대 — 도구 이름이 아니라 문제의 모양에서 시작한다",
               "(해석 — 레슨 docs 를 엮은 순서)",
               [("1  모양을 가른다", "같은 행인가\n다른 행인가\n같은 요청인가\n이벤트인가", "a"),
                ("2  DB 의 보증", "한 문장으로 되는\n보증이 있으면\n그것을 쓴다", "ok"),
                ("3  없으면", "락 또는\n격리수준", "warn"),
                ("4  실패 신호", "SQLSTATE · 영향 행 수를\n받아 트랜잭션 전체를\n재시도", "bad"),
                ("5  부수효과", "커밋 뒤로 뺀다", "b")],
               labels=("", "", "", ""), gap=60, h=170, top=120, bs=14)
    d.save()


def signals():
    d = new("blog-t03-signals", 1400, 460, "실패했다는 신호는 두 종류다",
            "호출 코드가 어느 쪽 신호를 읽는지가 곧 설계의 일부다")
    d.card("L", 40, 110, 640, 220, "영향 행 수가 신호인 도구",
           "에러가 아니라 0 이 돌아온다\n\n원자 조건부 UPDATE   0 = 조건 불충족\n낙관 락                 0 = 충돌 (version 불일치)\nON CONFLICT DO NOTHING   0 = 이미 선점됨\n조건부 upsert           0 = 중복 또는 STALE\n\n같은 0 이라도 대상 행이 없을 때도 0 이다\n호출 코드가 0 을 해석하는 자리가 설계다",
           bg=P["ok_bg"], stroke=P["green"], title_size=17, body_size=14)
    d.card("R", 720, 110, 640, 220, "SQLSTATE 가 신호인 도구",
           "메시지 문구가 아니라 코드로 판정한다\n\n40001  직렬화 실패\n40P01  데드락\n55P03  락 타임아웃 · NOWAIT\n23505  유니크 위반\n\n(01.01 · 01 에러 코드 절)",
           bg=P["bad_bg"], stroke=P["red"], title_size=17, body_size=14)
    d.card("n", 40, 360, 1320, 70, "예방이 가능하면 재시도보다 우선이다",
           "데드락은 락 순서를 하나로 정해 감지될 일 자체를 없애고, 재시도는 2차 방어선이다 (01.02 · 05)",
           bg=P["note_bg"], stroke=P["line"], title_size=15, body_size=14)
    d.save()


def isolation_up():
    d = new("blog-t03-isolation-up", 1400, 590, "격리수준은 언제 올리나",
            "기본(READ COMMITTED)에서 시작한다 — 올리지 않고도 되는 문제가 대부분이다 (해석)")
    d.card("a", 40, 110, 420, 160, "같은 행 증감 — 올릴 필요 없다",
           "읽기가 쓰기를 막지 않는 MVCC 위에서\n원자 UPDATE 로 이미 안전하다\n기다린 쪽이 최신 버전에\nWHERE 를 다시 평가하기 때문 (01.01 · 04)",
           bg=P["ok_bg"], stroke=P["green"], title_size=16, body_size=14)
    d.card("b", 490, 110, 420, 160, "다른 행 write skew — 올린다",
           "서로 다른 행을 고쳐서 행 락이 못 잡는 이상\nREPEATABLE READ 는 못 막는다\n(직렬화 이상이 표 13.1 에서 가능)\nSERIALIZABLE 만 막는다",
           bg=P["todo_bg"], stroke=P["orange"], title_size=16, body_size=14)
    d.card("c", 940, 110, 420, 160, "REPEATABLE READ 로 올리면",
           "스냅샷 이후 바뀐 행을 고칠 때\n40001 이 새로 생긴다\n재평가로 조용히 넘어가던 같은 행\nUPDATE 가 에러로 바뀐다 (01.01 · 04)",
           bg=P["bad_bg"], stroke=P["red"], title_size=16, body_size=14)
    d.text(490, 300, "올릴 때의 대가 (01.01 · 05)", 16, P["muted"], weight=700)
    costs = [("1  전체 재시도 필수", "블로킹이 늘지는 않지만\n실패가 40001 로 나온다", "bad"),
             ("2  오탐", "읽고 쓰는 행이 겹치지 않아도\nSIREAD 락이 페이지 · 릴레이션\n단위로 커지면 실패 (시퀀셜 스캔 읽기 등)", "warn"),
             ("3  감시 오버헤드", "긴 읽기 전용 리포트는\nREAD ONLY DEFERRABLE 로 피한다", "a")]
    for i, (t, b, k) in enumerate(costs):
        bg, st = kc(k)
        d.card(f"k{i}", 40 + i * 450, 330, 420, 130, t, b, bg=bg, stroke=st, title_size=16, body_size=14)
    d.card("n", 40, 490, 1320, 70, "SERIALIZABLE 에서 읽은 값은 커밋이 성공하기 전에는 유효하다고 여기지 않는다",
           "(DEFERRABLE 읽기 전용은 읽는 즉시 유효 — 01.01 · 05, 문서 13.2.3)", bg=P["note_bg"], stroke=P["line"], title_size=15, body_size=14)
    d.save()


def jvm_lock():
    d = new("blog-t03-jvm-lock", 1400, 560, "JVM 락은 그 JVM 안만 조정한다",
            "같은 멱등 키 요청이 서로 다른 인스턴스로 들어오면 각자 \"처음 보는 요청\" 이라고 판단한다")
    d.card("i1", 40, 120, 400, 150, "인스턴스 1 (JVM)", "synchronized · ConcurrentHashMap\n\"이 키는 처음 본다\" → 처리", bg=P["as_bg"], stroke=P["front"], title_size=16, body_size=14)
    d.card("i2", 40, 320, 400, 150, "인스턴스 2 (JVM)", "자기 락 · 자기 맵\n\"이 키는 처음 본다\" → 처리", bg=P["bff_bg"], stroke=P["back"], title_size=16, body_size=14)
    d.card("db", 560, 120, 460, 350, "DB — 심판은 데이터와 같은 곳에",
           "유니크 제약 · 행 락 · 조건부 UPDATE\n\n두 인스턴스가 같은 키를 INSERT 하면\n하나만 성공한다\n\n01.03 구현 테스트의 방법 검사가\n\"인스턴스가 둘이어도 DB 가\n중복을 막는가\" 로 이 해법을 거른다",
           bg=P["ok_bg"], stroke=P["green"], title_size=16, body_size=14)
    d.arrow([(440, 195), (560, 195)], P["front"], "INSERT", start="i1", end="db")
    d.arrow([(440, 395), (560, 395)], P["back"], "INSERT", start="i2", end="db")
    d.card("w", 1080, 120, 280, 350, "서버가 한 대여도 (해석)",
           "확장하면 바로 깨진다\n키별 락 맵 정리가 필요하다\n심판이 데이터와\n다른 곳에 있다",
           bg=P["note_bg"], stroke=P["line"], title_size=15, body_size=14)
    d.card("n", 40, 500, 1320, 50, "분산 락(Redis 등)은 이 트랙의 범위 밖 — 동작을 주장하지 않는다",
           None, bg=P["white"], stroke=P["line"], title_size=14)
    d.save()


def retry_loop():
    d = hchain("blog-t03-retry-loop", "재시도는 트랜잭션 전체를, 바깥에서",
               "40001 은 UPDATE 에서도 COMMIT 에서도 난다 — commit() 도 같은 try 안에 둔다",
               [("시도 1", "BEGIN\n읽기 · 계산 · 쓰기\nCOMMIT → 40001", "bad"),
                ("실패 판정", "SQLSTATE 로\n(메시지 문구 X)", "warn"),
                ("대기", "무작위 대기(지터)\n횟수 상한", "note"),
                ("시도 2", "처음부터 다시\n새 트랜잭션\n새로 읽는다", "a"),
                ("결과", "성공\n또는 명확한 실패\n(정상 결과 품절과 구분)", "ok")],
               labels=("", "", "", ""), gap=56, h=150, top=120, extra=160)
    d.card("n", 40, 330, 1320, 110, "이어서 쓰지 않고 처음부터 하는 이유",
           "앞서 읽은 값이 이미 틀렸고, 실패한 트랜잭션은 중단 상태(25P02)라 이어갈 수 없다\n재시도는 @Transactional 경계 바깥, 트랜잭션 메서드와 다른 빈에 둔다 (해석 — 문서 05)\n재시도는 work 를 다시 실행하므로 외부 호출 · 메시지 발행이 시도마다 중복된다 → 커밋 뒤로 · outbox · 상대에게 멱등 키",
           bg=P["note_bg"], stroke=P["line"], title_size=15, body_size=14)
    d.save()


def combos():
    d = new("blog-t03-combos", 1400, 690, "조합하는 법 — 문제 하나에 도구 하나만 쓰는 경우는 드물다",
            "레슨 docs 가 이미 보여 주는 조합")
    d.text(40, 100, "멱등 키 + 재고 차감", 17, P["front"], weight=700)
    a = [("키 선점", "01.03 — 같은 요청을 거른다", "ok"), ("재고 차감", "01.04 — 원자 UPDATE", "a"),
         ("외부 결제 호출", "DB 롤백으로 못 되돌린다\n키를 상대에게도 넘기거나 outbox", "warn")]
    for i, (t, b, k) in enumerate(a):
        bg, st = kc(k)
        d.card(f"a{i}", 40 + i * 460, 130, 400, 110, t, b, bg=bg, stroke=st, title_size=15, body_size=14)
    d.arrow([(440, 185), (500, 185)], P["muted"], None, start="a0", end="a1")
    d.arrow([(900, 185), (960, 185)], P["muted"], None, start="a1", end="a2")
    d.text(40, 280, "이벤트 소비 + 상태 반영", 17, P["green"], weight=700)
    b = [("inbox 판정", "messageId PK + ON CONFLICT DO NOTHING", "ok"), ("version 조건부 upsert", "inbox 판정과 한 트랜잭션에", "a"),
         ("부수효과", "반영이 일어났을 때만", "warn")]
    for i, (t, b_, k) in enumerate(b):
        bg, st = kc(k)
        d.card(f"b{i}", 40 + i * 460, 310, 400, 110, t, b_, bg=bg, stroke=st, title_size=15, body_size=14)
    d.arrow([(440, 365), (500, 365)], P["muted"], None, start="b0", end="b1")
    d.arrow([(900, 365), (960, 365)], P["muted"], None, start="b1", end="b2")
    d.card("hot", 40, 470, 1320, 180, "한 행이 병목이면 (01.04 · 05)",
           "1  락 보유 시간을 줄이는 것이 먼저\n2  그래도 안 되면 버킷 분할 · 큐 · 예약 같은 줄 자체를 나누는 설계 (모두 해석 · 일반 설계, 해당 문서가 대가를 적음)\n3  마지막 방어선으로 원자 조건부 UPDATE 를 남긴다\n서버를 늘려도 한 행은 서버 수와 무관하게 직렬이다",
           bg=P["note_bg"], stroke=P["line"], title_size=16, body_size=14)
    d.save()


if __name__ == "__main__":
    for f in (intro, skeleton, signals, isolation_up, jvm_lock, retry_loop, combos):
        f()
    finish()
