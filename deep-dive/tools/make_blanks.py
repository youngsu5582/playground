#!/usr/bin/env python3
"""
레슨 하나를 '정답 원본(마커 포함)' → '빈칸(학습자가 구현할 상태)' 으로 바꾸고, 정답을 patch 로 남긴다.

마커 문법 (Java 주석, 줄 단위):
    // @answer:begin       ← 정답 코드 (빈칸 상태에서 통째로 사라진다)
    // @answer:end
    // @blank:begin        ← 빈칸 상태에서만 살아나는 코드. 각 줄은 '//b ' 로 시작
    //b return Optional.empty();
    // @blank:end

사용 (deep-dive 루트에서):
    python3 -I tools/make_blanks.py 01-concurrency-consistency/l01-isolation-mvcc          # 미리보기 (아무것도 안 바꿈)
    python3 -I tools/make_blanks.py 01-concurrency-consistency/l01-isolation-mvcc --apply  # 빈칸으로 바꾸고 patch 기록

결과:
    solutions/01.01.patch          빈칸 → 정답 (deep-dive 루트 기준 경로. `git apply --check solutions/01.01.patch`)
    .marked/01.01/…                마커가 든 원본 백업 (gitignore — 다시 만들 때 쓴다)
"""
import difflib
import pathlib
import re
import shutil
import sys

ANS_BEGIN = re.compile(r"^\s*// @answer:begin\s*$")
ANS_END = re.compile(r"^\s*// @answer:end\s*$")
BLANK_BEGIN = re.compile(r"^\s*// @blank:begin\s*$")
BLANK_END = re.compile(r"^\s*// @blank:end\s*$")
BLANK_LINE = re.compile(r"^(\s*)//b ?(.*)$")
LESSON = re.compile(r"(\d\d)-[^/]+/l(\d\d)-[^/]+/?$")


def transform(lines, mode):
    out, state = [], None
    for line in lines:
        if ANS_BEGIN.match(line):
            state = "ans"; continue
        if ANS_END.match(line):
            state = None; continue
        if BLANK_BEGIN.match(line):
            state = "blank"; continue
        if BLANK_END.match(line):
            state = None; continue
        if state == "ans":
            if mode == "answer":
                out.append(line)
            continue
        if state == "blank":
            if mode == "blank":
                m = BLANK_LINE.match(line)
                if not m:
                    raise SystemExit(f"blank 블록 안에 //b 가 아닌 줄: {line!r}")
                out.append(m.group(1) + m.group(2) + "\n")
            continue
        out.append(line)
    if state is not None:
        raise SystemExit("닫히지 않은 블록")
    cleaned = []
    for line in out:  # 블록을 들어낸 자리의 빈 줄 겹침 정리
        if line.strip() == "" and cleaned and cleaned[-1].strip() == "":
            continue
        cleaned.append(line)
    return cleaned


def main():
    root = pathlib.Path.cwd()
    lesson_dir = pathlib.Path(sys.argv[1].rstrip("/"))
    apply = "--apply" in sys.argv
    m = LESSON.search(str(lesson_dir) + "/")
    if not m:
        raise SystemExit("레슨 경로가 아니다 (NN-트랙/lNN-레슨): " + str(lesson_dir))
    lesson_id = f"{m.group(1)}.{m.group(2)}"
    files = sorted(p for p in (root / lesson_dir).rglob("*.java")
                   if "/build/" not in str(p) and "@answer:begin" in p.read_text(encoding="utf-8"))
    if not files:
        raise SystemExit("마커가 있는 파일이 없다 (이미 빈칸 상태?)")
    parts = []
    for p in files:
        rel = p.relative_to(root)
        lines = p.read_text(encoding="utf-8").splitlines(keepends=True)
        sol, blank = transform(lines, "answer"), transform(lines, "blank")
        parts.append("".join(difflib.unified_diff(blank, sol, fromfile=f"a/{rel}", tofile=f"b/{rel}", n=3)))
        print(f"  {rel}  (정답 {len(sol)}줄 / 빈칸 {len(blank)}줄)")
        if apply:
            backup = root / ".marked" / lesson_id / rel
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, backup)
            p.write_text("".join(blank), encoding="utf-8")
    if apply:
        out = root / "solutions" / f"{lesson_id}.patch"
        out.parent.mkdir(exist_ok=True)
        out.write_text("".join(parts), encoding="utf-8")
        print(f"→ {out.relative_to(root)}  ({len(files)} files)  · 원본 백업 .marked/{lesson_id}/")
    else:
        print("(미리보기 — --apply 를 붙이면 빈칸으로 바꾼다)")


if __name__ == "__main__":
    main()
