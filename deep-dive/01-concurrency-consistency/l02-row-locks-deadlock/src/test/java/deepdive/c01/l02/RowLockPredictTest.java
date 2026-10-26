package deepdive.c01.l02;

import deepdive.testkit.PostgresLab;
import deepdive.testkit.Predict;
import deepdive.testkit.Session;
import deepdive.testkit.Session.Pending;
import deepdive.testkit.SqlFailure;
import deepdive.testkit.Timeline;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.time.Duration;

import static deepdive.testkit.Session.Isolation.READ_COMMITTED;

/**
 * [예측] 각 테스트의 {@code String 예측 = "?";} 를 <b>돌리기 전에</b> 내 답으로 바꾼다.
 * 답 형식은 질문 끝 괄호에 있다 — 숫자는 "2", 예/아니오는 "true"/"false", 결과는 "성공"/"에러 55P03" 처럼.
 * 띄어쓰기·대소문자는 상관없다.
 *
 * <p>모든 시나리오는 진짜 PostgreSQL 16 에서 세션(A, B, 필요하면 C)으로 돈다. 출력에 찍히는 타임라인을 같이 읽는다.
 * 답이 쉽게 안 나오면 README ② 원리 → diagrams/ 그림을 보고 다시.
 *
 * <pre>
 * jobs(id, status)            — 1·2·3번, 모두 pending
 * account(id, balance)        — 1번 · 2번, 잔고 100
 * parent(id, name) · child(id, parent_id → parent)   — parent 1번 하나
 * </pre>
 */
@DisplayName("[예측] 01.02 행 락 · 데드락 — 10문항")
class RowLockPredictTest {

    static final Duration GRACE = Duration.ofMillis(300);
    final PostgresLab lab = PostgresLab.get();

    @BeforeEach
    void reset() {
        lab.exec(
                "DROP TABLE IF EXISTS jobs, account, child, parent",
                "CREATE TABLE jobs (id int PRIMARY KEY, status text NOT NULL DEFAULT 'pending', claimed_by text)",
                "INSERT INTO jobs (id) VALUES (1), (2), (3)",
                "CREATE TABLE account (id int PRIMARY KEY, balance bigint NOT NULL CHECK (balance >= 0))",
                "INSERT INTO account VALUES (1, 100), (2, 100)",
                "CREATE TABLE parent (id int PRIMARY KEY, name text NOT NULL)",
                "INSERT INTO parent VALUES (1, 'orig')",
                "CREATE TABLE child (id int PRIMARY KEY, parent_id int NOT NULL REFERENCES parent (id))");
    }

    // ── 1. 같은 행을 노리면 ──────────────────────────────────────

    @Test
    void Q01_FOR_UPDATE_로_잡힌_행을_UPDATE_하면() {
        Timeline.reset("Q01 A 가 1번을 FOR UPDATE — B 가 같은 행을 UPDATE");
        try (Session a = lab.session("A"); Session b = lab.session("B")) {
            a.begin(READ_COMMITTED);
            b.begin(READ_COMMITTED);
            a.query("SELECT id FROM jobs WHERE id = 1 FOR UPDATE"); // 읽기만 했다. 고치지 않았다
            Pending<Integer> bUpdate = b.updateAsync("UPDATE jobs SET status = 'running' WHERE id = 1");
            boolean bWaited = bUpdate.isWaiting(GRACE);
            a.commit();
            bUpdate.await(Duration.ofSeconds(5));
            b.commit();

            String 예측 = "?";
            Predict.확인("A 가 커밋하기 전, B 의 UPDATE 는 기다리나? (A 는 행을 읽고 잠갔을 뿐 고치지 않았다 · 답: true / false)", 예측, bWaited);
        }
    }

    @Test
    void Q02_락이_걸린_행을_평범한_SELECT_로_읽으면() {
        Timeline.reset("Q02 A 가 1번을 잠그고 고치는 중 — B 가 평범한 SELECT");
        try (Session a = lab.session("A"); Session b = lab.session("B")) {
            a.begin(READ_COMMITTED);
            b.begin(READ_COMMITTED);
            a.query("SELECT id FROM jobs WHERE id = 1 FOR UPDATE");
            a.update("UPDATE jobs SET status = 'running' WHERE id = 1"); // 커밋 전
            Pending<Object> bRead = b.async(() -> b.one("SELECT status FROM jobs WHERE id = 1"));
            boolean bWaited = bRead.isWaiting(GRACE);
            Object bSaw = bRead.await(Duration.ofSeconds(5));
            a.rollback();
            b.rollback();

            String 예측_대기 = "?";
            String 예측_값 = "?";
            Predict.확인("B 의 SELECT 는 A 가 끝나길 기다리나? (답: true / false)", 예측_대기, bWaited);
            Predict.확인("B 가 읽은 status 는? (A 는 running 으로 바꾸고 커밋 전 · 답: pending / running)", 예측_값, bSaw);
        }
    }

    // ── 2. 줄을 서지 않으려면 ─────────────────────────────────────

    @Test
    void Q03_NOWAIT_는_락이_잡혀_있으면() {
        Timeline.reset("Q03 A 가 1번을 잡고 있다 — B 가 FOR UPDATE NOWAIT");
        try (Session a = lab.session("A"); Session b = lab.session("B")) {
            a.begin(READ_COMMITTED);
            b.begin(READ_COMMITTED);
            a.query("SELECT id FROM jobs WHERE id = 1 FOR UPDATE");
            String nowait;
            try {
                b.query("SELECT id FROM jobs WHERE id = 1 FOR UPDATE NOWAIT");
                nowait = "성공";
            } catch (SqlFailure f) {
                nowait = "에러 " + f.sqlState();
            }
            String next;
            try {
                b.query("SELECT 1");
                next = "성공";
            } catch (SqlFailure f) {
                next = "에러 " + f.sqlState();
            }
            a.rollback();
            b.rollback();

            String 예측_NOWAIT = "?";
            String 예측_다음 = "?";
            Predict.확인("B 의 FOR UPDATE NOWAIT 는? (답: \"성공\" 또는 \"에러 \" + SQLState — 예: 에러 23505)", 예측_NOWAIT, nowait);
            Predict.확인("같은 트랜잭션에서 B 의 다음 문장 SELECT 1 은? (답: \"성공\" 또는 \"에러 \" + SQLState)", 예측_다음, next);
        }
    }

    @Test
    void Q04_lock_timeout_을_걸고_UPDATE_하면() {
        Timeline.reset("Q04 B 가 lock_timeout = 100ms — 잡힌 행을 UPDATE");
        try (Session a = lab.session("A"); Session b = lab.session("B")) {
            a.begin(READ_COMMITTED);
            a.query("SELECT id FROM jobs WHERE id = 1 FOR UPDATE");
            b.update("SET lock_timeout = '100ms'");
            long started = System.nanoTime();
            String outcome;
            try {
                b.update("UPDATE jobs SET status = 'running' WHERE id = 1");
                outcome = "성공";
            } catch (SqlFailure f) {
                outcome = "에러 " + f.sqlState();
            }
            long waitedMillis = (System.nanoTime() - started) / 1_000_000;
            a.rollback();
            Timeline.note("B 가 포기하기까지 걸린 시간 " + waitedMillis + "ms");

            String 예측 = "?";
            Predict.확인("B 의 UPDATE 는? (답: \"성공\" 또는 \"에러 \" + SQLState — Q03 의 NOWAIT 와 비교)", 예측, outcome);
        }
    }

    @Test
    void Q05_SKIP_LOCKED_는_잡힌_행을() {
        Timeline.reset("Q05 A 가 1번을 잡고 있다 — B 가 SKIP LOCKED 로 하나 집는다");
        try (Session a = lab.session("A"); Session b = lab.session("B")) {
            a.begin(READ_COMMITTED);
            a.query("SELECT id FROM jobs WHERE id = 1 FOR UPDATE");
            Object picked = b.one("SELECT id FROM jobs WHERE status = 'pending' ORDER BY id LIMIT 1 FOR UPDATE SKIP LOCKED");
            a.rollback();

            String 예측 = "?";
            Predict.확인("B 가 집은 작업 id 는? (pending 은 1·2·3 · 답: 숫자)", 예측, picked);
        }
    }

    @Test
    void Q06_SKIP_LOCKED_없이_LIMIT_1_FOR_UPDATE_는_기다린_뒤() {
        Timeline.reset("Q06 A 가 1번을 running 으로 바꾸는 중 — B 가 SKIP LOCKED 없이 FOR UPDATE LIMIT 1");
        try (Session a = lab.session("A"); Session b = lab.session("B")) {
            a.begin(READ_COMMITTED);
            b.begin(READ_COMMITTED);
            a.update("UPDATE jobs SET status = 'running' WHERE id = 1"); // 커밋 전
            Pending<Object> bPick = b.async(() -> b.one("SELECT id FROM jobs WHERE status = 'pending' ORDER BY id LIMIT 1 FOR UPDATE"));
            boolean bWaited = bPick.isWaiting(GRACE);
            a.commit();
            Object picked = bPick.await(Duration.ofSeconds(5));
            b.rollback();

            String 예측_대기 = "?";
            String 예측_결과 = "?";
            Predict.확인("A 가 커밋하기 전, B 는 기다리나? (답: true / false)", 예측_대기, bWaited);
            Predict.확인("A 가 커밋한 뒤 B 가 받은 id 는? (1번은 이제 running · 답: 숫자 / 없으면 \"없음\")", 예측_결과, picked == null ? "없음" : picked);
        }
    }

    // ── 3. 락의 종류 ────────────────────────────────────────────

    @Test
    void Q07_FOR_SHARE_끼리는_서로_막나() {
        Timeline.reset("Q07 FOR SHARE — 공유 락끼리, 그리고 UPDATE 와");
        try (Session a = lab.session("A"); Session b = lab.session("B"); Session c = lab.session("C")) {
            a.begin(READ_COMMITTED);
            b.begin(READ_COMMITTED);
            c.begin(READ_COMMITTED);
            a.query("SELECT id FROM jobs WHERE id = 1 FOR SHARE");
            Pending<Object> bShare = b.async(() -> b.one("SELECT id FROM jobs WHERE id = 1 FOR SHARE"));
            boolean shareWaited = bShare.isWaiting(GRACE);
            bShare.await(Duration.ofSeconds(5));
            Pending<Integer> cUpdate = c.updateAsync("UPDATE jobs SET status = 'running' WHERE id = 1");
            boolean updateWaited = cUpdate.isWaiting(GRACE);
            a.rollback();
            b.rollback();
            cUpdate.await(Duration.ofSeconds(5));
            c.rollback();

            String 예측_공유 = "?";
            String 예측_갱신 = "?";
            Predict.확인("A 가 FOR SHARE 로 잡은 행을 B 도 FOR SHARE 하면 기다리나? (답: true / false)", 예측_공유, shareWaited);
            Predict.확인("A · B 가 FOR SHARE 로 잡은 행을 C 가 UPDATE 하면 기다리나? (답: true / false)", 예측_갱신, updateWaited);
        }
    }

    @Test
    void Q08_자식_INSERT_가_부모_행에_거는_락() {
        Timeline.reset("Q08 A 가 자식 INSERT (커밋 전) — 부모 1번을 B 는 이름만 고치고(커밋), 그다음 C 는 지운다");
        try (Session a = lab.session("A"); Session b = lab.session("B"); Session c = lab.session("C")) {
            a.begin(READ_COMMITTED);
            b.begin(READ_COMMITTED);
            c.begin(READ_COMMITTED);
            a.update("INSERT INTO child VALUES (1, 1)"); // 부모 1번을 참조한다. 부모는 고치지 않았다
            Pending<Integer> bRename = b.updateAsync("UPDATE parent SET name = 'renamed' WHERE id = 1");
            boolean renameWaited = bRename.isWaiting(GRACE);
            bRename.await(Duration.ofSeconds(5));
            b.commit(); // B 를 끝낸다 — 남겨 두면 C 의 대기가 A 때문인지 B 때문인지 구분이 안 된다
            Pending<Integer> cDelete = c.updateAsync("DELETE FROM parent WHERE id = 1");
            boolean deleteWaited = cDelete.isWaiting(GRACE);
            a.rollback();
            cDelete.await(Duration.ofSeconds(5));
            c.rollback();

            String 예측_이름 = "?";
            String 예측_삭제 = "?";
            Predict.확인("B 의 UPDATE parent SET name … (키가 아닌 열) 는 기다리나? (답: true / false)", 예측_이름, renameWaited);
            Predict.확인("B 가 이미 커밋한 뒤, C 의 DELETE FROM parent WHERE id = 1 은 기다리나? (남은 건 A 의 미커밋 자식 INSERT 뿐 · 답: true / false)", 예측_삭제, deleteWaited);
        }
    }

    // ── 4. 누가 누구를 기다리나 · 데드락 ──────────────────────────

    @Test
    void Q09_기다리는_세션을_시스템_뷰에서_보면() {
        Timeline.reset("Q09 B 가 A 를 기다리는 중 — 세 번째 세션 C 가 들여다본다");
        try (Session a = lab.session("A"); Session b = lab.session("B")) {
            a.begin(READ_COMMITTED);
            b.begin(READ_COMMITTED);
            int aPid = a.pid();
            int bPid = b.pid();
            a.update("UPDATE jobs SET status = 'running' WHERE id = 1");
            Pending<Integer> bUpdate = b.updateAsync("UPDATE jobs SET status = 'running' WHERE id = 1");
            bUpdate.isWaiting(GRACE);
            Object waitEvent = lab.one("SELECT wait_event_type || '/' || wait_event FROM pg_stat_activity WHERE pid = " + bPid);
            Object blockedByA = lab.one("SELECT pg_blocking_pids(" + bPid + ") = ARRAY[" + aPid + "]");
            Timeline.note("C 가 본 것 — wait_event " + waitEvent + " · pg_blocking_pids(B) = " + lab.one("SELECT pg_blocking_pids(" + bPid + ")") + " (A 의 pid = " + aPid + ")");
            a.rollback();
            bUpdate.await(Duration.ofSeconds(5));
            b.rollback();

            String 예측_대기 = "?";
            String 예측_차단 = "?";
            Predict.확인("pg_stat_activity 에서 B 의 wait_event_type/wait_event 는? (답: 형식 Type/event — 예: IO/DataFileRead)", 예측_대기, waitEvent);
            Predict.확인("pg_blocking_pids(B 의 pid) 는 A 의 pid 하나만 담고 있나? (답: true / false)", 예측_차단, blockedByA);
        }
    }

    /**
     * 누가 끊기나는 공식 문서가 "예측하지 말라"고 한 부분이다 — 문항으로 내지 않고 Timeline 에 출력만 한다.
     * (A 의 대기가 deadlock_timeout 을 넘긴 뒤 B 가 순환을 닫으면 B 가, 간격이 짧으면 A 가 끊기는 게 이 랩의 실측이다. NOTES 해설.)
     */
    @Test
    void Q10_반대_순서로_잡으면_데드락() {
        Timeline.reset("Q10 A 는 1→2, B 는 2→1 순서로 UPDATE");
        try (Session a = lab.session("A"); Session b = lab.session("B")) {
            a.begin(READ_COMMITTED);
            b.begin(READ_COMMITTED);
            a.update("UPDATE account SET balance = balance - 10 WHERE id = 1");
            b.update("UPDATE account SET balance = balance - 10 WHERE id = 2");
            Pending<Integer> aSecond = a.updateAsync("UPDATE account SET balance = balance + 10 WHERE id = 2"); // B 를 기다린다
            aSecond.isWaiting(GRACE); // 기다림이 deadlock_timeout(200ms) 보다 길어졌다. 아직 순환은 없다
            String failedSession = "없음";
            String failedState = "없음";
            try {
                b.update("UPDATE account SET balance = balance + 10 WHERE id = 1"); // A 를 기다린다 — 이제 순환
            } catch (SqlFailure f) {
                failedSession = "B";
                failedState = f.sqlState();
            }
            try {
                aSecond.await(Duration.ofSeconds(5));
            } catch (SqlFailure f) {
                failedSession = "A";
                failedState = f.sqlState();
            }
            a.rollback();
            b.rollback();
            Timeline.note("엔진이 끊은 쪽: " + failedSession + " (" + failedState + ") — 누가 끊기는지는 보장이 아니다. 출력을 보고 NOTES 에 적는다");

            String 예측 = "?";
            Predict.확인("한쪽 세션이 엔진에게 끊긴다. 그 에러의 SQLState 는? (답: SQLState 다섯 글자)", 예측, failedState);
        }
    }
}
