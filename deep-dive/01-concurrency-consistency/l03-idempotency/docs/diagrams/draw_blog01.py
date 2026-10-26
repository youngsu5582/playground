#!/usr/bin/env python3
"""01.03 블로그판 01 그림. 실행: python3 -I docs/diagrams/draw_blog01.py (레슨 폴더에서)"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[4] / "tools"))
from diagram import Diagram, P, finish  # noqa: E402

OUT = pathlib.Path(__file__).parent


def double_charge():
    d = Diagram("blog01-double-charge", 1260, 640, "도입: 응답이 사라지면 클라이언트는 같은 요청을 다시 보낸다",
                "결제 10,000 원을 요청했는데 응답이 오지 않았다 — 서버는 이미 처리했다", out=OUT)
    d.pill("hc", 60, 96, 440, 38, "클라이언트", P["as_bg"], P["front"], size=15)
    d.pill("hs", 760, 96, 440, 38, "서버", P["bff_bg"], P["back"], size=15)
    d.card("c1", 60, 160, 440, 70, "1  POST /payments  (10,000 원)", "결제를 요청한다", bg=P["as_bg"], stroke=P["front"], title_size=15)
    d.card("s1", 760, 160, 440, 70, "처리한다", "결제를 실행하고 DB 에 기록한다", bg=P["bff_bg"], stroke=P["back"], title_size=15)
    d.arrow([(500, 195), (760, 195)], P["muted"], "요청", start="c1", end="s1")
    d.card("s2", 760, 260, 440, 70, "2  응답 200 을 보낸다", "처리는 이미 끝났다", bg=P["bff_bg"], stroke=P["back"], title_size=15)
    d.card("c2", 60, 260, 440, 70, "응답이 오지 않는다 — 타임아웃", "클라이언트는 결과를 모른다", bg=P["todo_bg"], stroke=P["orange"], title_size=15)
    d.arrow([(760, 295), (500, 295)], P["red"], "응답 유실", dashed=True, start="s2", end="c2")
    d.card("c3", 60, 360, 440, 70, "3  같은 요청을 다시 보낸다", "재시도 — 정상적인 동작이다", bg=P["as_bg"], stroke=P["front"], title_size=15)
    d.card("s3", 760, 360, 440, 70, "같은 결제를 또 처리하면", "10,000 원이 두 번 결제된다", bg=P["bad_bg"], stroke=P["red"], title_size=15, sw=3)
    d.arrow([(500, 395), (760, 395)], P["red"], "재시도", start="c3", end="s3")
    d.card("v", 60, 470, 1140, 130, "재시도는 막을 수 없고, 막아서도 안 된다",
           "재시도를 하지 않으면 첫 요청이 아예 서버에 닿지 못한 경우에 요청이 영영 유실된다.\n"
           "재시도하는 쪽도 클라이언트만이 아니다 — 게이트웨이 · 로드밸런서 · 메시지 브로커(at-least-once 재전송)가 한다.\n"
           "그래서 같은 요청이 두 번 와도 효과가 한 번이도록 막는 일은 서버의 몫이다.",
           bg=P["bad_bg"], stroke=P["red"], title_size=16, body_size=14, title_color=P["red"])
    d.save()


def timeout_three():
    d = Diagram("blog01-timeout-three", 1360, 560, "타임아웃은 실패가 아니라 \"모름\" 이다",
                "서버에서 실제로 일어난 일은 셋 중 하나인데, 클라이언트에게는 똑같이 보인다 (해석)", out=OUT)
    d.pill("req", 40, 100, 1280, 46, "클라이언트: 요청을 보냈고, 응답을 못 받았다", P["as_bg"], P["front"], size=16)
    cases = [("1. 요청이 도착하지 못했다", "서버: 아무 일도 일어나지 않았다", P["note_bg"], P["muted"]),
             ("2. 처리했지만 응답이 사라졌다", "서버: 처리 끝, 응답이 오는 길에 유실", P["ok_bg"], P["green"]),
             ("3. 아직 처리 중이다", "서버: 느릴 뿐, 아직 처리 중", P["todo_bg"], P["orange"])]
    for i, (t, b, bg, st) in enumerate(cases):
        x = 40 + i * 436
        d.card(f"k{i}", x, 210, 408, 100, t, b, bg=bg, stroke=st, title_size=16, body_size=14)
        d.arrow([(x + 204, 146), (x + 204, 210)], P["muted"], start="req", end=f"k{i}")
        d.arrow([(x + 204, 310), (x + 204, 370)], P["muted"], "클라이언트가\n보는 것", label_size=12)
    d.pill("all", 40, 370, 1280, 56, "세 경우 모두 \"응답 없음\" — 다시 보내도 안전한지 클라이언트는 판단할 수 없다", P["bad_bg"], P["red"], size=16)
    d.card("v", 40, 450, 1280, 90, "그래서 안전하게 만드는 쪽은 서버다",
           "재시도를 막는 것은 답이 아니다 — 1번 경우에서 요청이 유실된다. 서버가 \"같은 요청이 또 왔다\" 를 알아보고 효과를 한 번으로 만든다.",
           bg=P["note_bg"], stroke=P["line"], title_size=16, body_size=14)
    d.save()


def methods():
    d = Diagram("blog01-methods", 1360, 600, "HTTP 메서드의 멱등 — RFC 9110 §9.2.2",
                "같은 요청을 여러 번 보내도 서버에 미치는 의도된 효과가 한 번 보낸 것과 같으면 멱등이다", out=OUT)
    d.card("idem", 40, 100, 620, 150, "멱등인 표준 메서드", "PUT\nDELETE\n안전한(safe) 메서드",
           bg=P["ok_bg"], stroke=P["green"], title_size=17, body_size=16, title_color=P["green"])
    d.card("post", 700, 100, 620, 150, "이 목록에 없는 메서드", "POST — 결제 승인 · 주문 생성이 대개 여기에 해당한다\n"
           "프로토콜 수준에서는 안전한 재시도 보장이 없다",
           bg=P["bad_bg"], stroke=P["red"], title_size=17, body_size=15, title_color=P["red"])
    d.text(40, 280, "멱등이 중요한 이유: 통신 실패가 나면 요청을 자동으로 반복할 수 있기 때문이다 (RFC 9110). 같은 절의 두 규칙은 이렇다", 15, P["muted"])
    d.card("r1", 40, 320, 620, 130, "클라이언트 (SHOULD NOT)",
           "멱등하지 않은 메서드의 요청을 자동으로 재시도하면 안 된다\n"
           "— 재시도해도 안전하다는 것을 아는 수단이 없다면",
           bg=P["todo_bg"], stroke=P["orange"], title_size=16, body_size=14)
    d.card("r2", 700, 320, 620, 130, "프록시 (MUST NOT)",
           "멱등하지 않은 요청을 자동으로 재시도하면 안 된다",
           bg=P["todo_bg"], stroke=P["orange"], title_size=16, body_size=14)
    d.card("v", 40, 480, 1280, 90, "POST 는 서버가 별도 장치를 둬야 한다",
           "그 장치의 업계 관례가 멱등 키(Idempotency-Key)다. 뒤에서 본다.",
           bg=P["note_bg"], stroke=P["line"], title_size=16, body_size=14)
    d.save()


def effect_vs_response():
    d = Diagram("blog01-effect-vs-response", 1260, 520, "멱등은 \"응답이 같다\" 가 아니라 \"효과가 같다\"",
                "두 번째 호출의 상태 코드가 달라도, 서버에 남는 효과가 한 번이면 멱등이다 (해석 — RFC 의 \"의도된 효과\" 문구에서 읽은 것)", out=OUT)
    d.pill("h1", 60, 100, 540, 38, "첫 번째 호출", P["as_bg"], P["front"], size=15)
    d.pill("h2", 660, 100, 540, 38, "두 번째 호출 (같은 요청)", P["bff_bg"], P["back"], size=15)
    d.card("a1", 60, 160, 540, 90, "응답: 201 Created", "결제가 한 건 생겼다", bg=P["ok_bg"], stroke=P["green"], title_size=16)
    d.card("a2", 660, 160, 540, 90, "응답: 200 OK", "새로 만들지 않고, 처음 결과를 알려 준다", bg=P["ok_bg"], stroke=P["green"], title_size=16)
    d.arrow([(600, 205), (660, 205)], P["muted"], "재요청", label_size=11, start="a1", end="a2")
    d.pill("eff", 60, 290, 1140, 56, "서버에 남은 결제는 여전히 한 건 — 효과가 같다", P["ok_bg"], P["green"], size=16)
    d.card("v", 60, 380, 1140, 100, "응답까지 똑같이 돌려줄지는 별개의 설계 선택이다",
           "저장해 둔 첫 응답을 그대로 재생(replay)하는 것은 멱등의 정의가 요구하는 것이 아니다 (문서 06 에서 다룬다).",
           bg=P["note_bg"], stroke=P["line"], title_size=16, body_size=14)
    d.save()


def key_flow():
    d = Diagram("blog01-key-flow", 1400, 660, "멱등 키 관례 — 클라이언트가 키를 만들고, 서버가 그 키로 중복을 알아본다",
                "POST 를 멱등하게 만드는 업계 관례 (Stripe API · IETF 초안이 같은 방식)", out=OUT)
    d.card("c1", 40, 110, 400, 100, "1  클라이언트가 키를 만든다", "요청마다 고유한 키\nUUID v4 같은 무작위 문자열을 권한다", bg=P["as_bg"], stroke=P["front"], title_size=16)
    d.card("c2", 500, 110, 400, 100, "2  헤더로 보낸다", "Idempotency-Key: <키>\n요청 본문과 함께", bg=P["as_bg"], stroke=P["front"], title_size=16)
    d.card("c3", 960, 110, 400, 100, "3  서버가 처음 보는 키다", "처리하고, 첫 요청의 상태 코드와\n본문을 저장해 둔다", bg=P["bff_bg"], stroke=P["back"], title_size=16)
    d.arrow([(440, 160), (500, 160)], P["muted"], "전송", label_size=11, start="c1", end="c2")
    d.arrow([(900, 160), (960, 160)], P["muted"], "도착", label_size=11, start="c2", end="c3")
    d.card("r1", 40, 290, 400, 100, "4  응답을 못 받았다", "같은 키로 다시 보낸다\n(재시도에서도 그대로 쓴다)", bg=P["todo_bg"], stroke=P["orange"], title_size=16)
    d.card("r2", 500, 290, 400, 100, "5  서버가 같은 키를 본다", "중복이다 — 새로 처리하지 않는다", bg=P["bff_bg"], stroke=P["back"], title_size=16)
    d.card("r3", 960, 290, 400, 100, "6  저장된 응답을 돌려준다", "재생(replay)", bg=P["ok_bg"], stroke=P["green"], title_size=16)
    d.arrow([(440, 340), (500, 340)], P["muted"], "전송", label_size=11, start="r1", end="r2")
    d.arrow([(900, 340), (960, 340)], P["muted"], "조회", label_size=11, start="r2", end="r3")
    d.arrow([(1160, 210), (1160, 250), (240, 250), (240, 290)], P["muted"], "시간이 지나\n재시도", label_at=(700, 250), start="c3", end="r1")
    d.card("st", 40, 440, 660, 190, "Stripe API v1 (docs.stripe.com)",
           "키는 255자 이하\n엔드포인트 실행이 시작된 뒤 첫 요청의 상태 코드와 본문을 저장 (500 도 포함)\n"
           "24시간 이상 지난 키는 지울 수 있다 — 지운 뒤 같은 키는 새 요청\n파라미터가 원래 요청과 다르면 에러\n"
           "검증 실패 · 동시 실행 충돌은 결과를 저장하지 않아 재시도할 수 있다",
           bg=P["note_bg"], stroke=P["line"], title_size=16, body_size=13)
    d.card("ie", 720, 440, 640, 190, "IETF 초안 -07 (표준이 아니다)",
           "조회한 2026-10-13 현재 만료(Expired & archived)로 표시\n헤더 값은 Structured Header String\n"
           "키는 고유해야 하고 다른 페이로드에 재사용 금지 (MUST)\n같은 키 + 다른 페이로드 -> 422 · 처리 중 -> 409 (SHOULD)\n"
           "키가 없으면 400 (SHOULD) · 만료 정책은 서버가 정해 문서화",
           bg=P["note_bg"], stroke=P["line"], title_size=16, body_size=13)
    d.save()


def key_vs_hash():
    d = Diagram("blog01-key-vs-hash", 1360, 600, "멱등 키와 요청 본문 해시는 다른 것이다",
                "키는 \"같은 의도\" 의 이름표, 해시는 \"같은 내용\" 의 검사다", out=OUT)
    d.card("k", 40, 100, 620, 100, "멱등 키", "이 시도가 같은 의도의 재시도인지 알려 주는 이름표", bg=P["as_bg"], stroke=P["front"], title_size=17)
    d.card("h", 700, 100, 620, 100, "요청 해시 (지문)", "같은 키로 온 요청이 같은 내용인지 확인하는 검사", bg=P["bff_bg"], stroke=P["back"], title_size=17)
    d.pill("t1", 40, 240, 260, 44, "키", P["note_bg"], P["line"], size=14)
    d.pill("t2", 310, 240, 260, 44, "내용", P["note_bg"], P["line"], size=14)
    d.pill("t3", 580, 240, 740, 44, "서버의 판단", P["note_bg"], P["line"], size=14)
    rows = [("같다", "같다", "재시도 — 저장된 응답을 돌려준다", P["ok_bg"], P["green"]),
            ("같다", "다르다", "거절한다 — Stripe 는 에러, IETF 초안은 422", P["bad_bg"], P["red"]),
            ("다르다", "같다", "서로 다른 의도 — 해시만 봤다면 재시도와 구분할 수 없다 (해석)", P["todo_bg"], P["orange"])]
    for i, (a, b, c, bg, st) in enumerate(rows):
        y = 296 + i * 76
        d.pill(f"a{i}", 40, y, 260, 64, a, bg, st, size=16)
        d.pill(f"b{i}", 310, y, 260, 64, b, bg, st, size=16)
        d.pill(f"c{i}", 580, y, 740, 64, c, bg, st, size=14)
    d.card("v", 40, 534, 1280, 50, "본문 해시만으로는 사용자가 같은 금액을 일부러 두 번 결제하는 것과 재시도를 구분할 수 없다 (해석)",
           None, bg=P["note_bg"], stroke=P["line"], title_size=14)
    d.save()


def terms():
    d = Diagram("blog01-terms", 1360, 440, "이 레슨이 쓰는 세 단어 — 선점 · 재생 · 지문",
                "PaymentService 는 키를 DB 의 idempotency_keys 테이블에 두고, 한 번의 호출을 한 트랜잭션으로 처리한다", out=OUT)
    d.card("t1", 40, 100, 410, 150, "선점 (claim)", "이 키를 내가 처리해도 되는지를\n키 행 INSERT 와 동시에 판정하는 것", bg=P["todo_bg"], stroke=P["orange"], title_size=18, body_size=15)
    d.card("t2", 475, 100, 410, 150, "재생 (replay)", "이미 처리된 키에 저장된 응답을\n그대로 돌려주는 것", bg=P["ok_bg"], stroke=P["green"], title_size=18, body_size=15)
    d.card("t3", 910, 100, 410, 150, "지문 (fingerprint)", "같은 키로 온 요청이 같은 내용인지\n알아보는 요약. 이 레슨은 고객 + 금액의\nSHA-256 (PaymentRequest#fingerprint)", bg=P["bff_bg"], stroke=P["back"], title_size=18, body_size=15)
    d.card("who", 40, 300, 1280, 110, "심판은 모든 서버가 공유하는 DB 다",
           "서버가 2대여도 통하게 하는 것이 목표라서, JVM 안 락(synchronized · ConcurrentHashMap)이 아니라 DB 가 중복을 판정한다.\n"
           "엔진이 이 판정을 어떻게 하는지는 02 ~ 05 에서 다룬다.",
           bg=P["note_bg"], stroke=P["line"], title_size=17, body_size=15)
    d.save()


if __name__ == "__main__":
    for f in (double_charge, timeout_three, methods, effect_vs_response, key_flow, key_vs_hash, terms):
        f()
    finish()
