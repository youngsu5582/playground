# TESTING

자동 테스트는 `claude plugin test ./command-log` (6개). 아래는 세션에서 직접 돌려 보고 관찰하는 것이다.

| T-ID | 무엇을 | 어떻게 | 기대 |
|---|---|---|---|
| T1 | 커맨드 등록 (`session.start`) | 세션을 열고 `/` 목록을 본다 | `/command-log` 가 보인다 |
| T2 | 패널 열고 닫기 (`command.run`) | `/command-log` → `/command-log off` | 패널이 열리고 닫힌다 |
| T3 | 실행 기록 (`tool.call`) | Claude 에게 `ls` 와 `false` 를 시킨다 | 패널에 `✓ ls` · `✕ false`, 상태줄 `명령 2 · 실패 1` |
| T4 | 걸린 시간에 무엇이 들어가나 | PreToolUse 셸 훅이 있는 repo 와 없는 폴더에서 같은 `ls` 의 ms 를 비교한다 | 관찰. 훅이 있는 쪽이 길면 훅 시간이 `next(e)` 안에 포함된 것이다 |
| T5 | gh 쓰기는 묻는다 (`tool.check`) | `gh pr comment 1 --repo octo/does-not-exist --body test` 를 시킨다 | 권한 프롬프트에 `gh 로 GitHub 에 쓰는 명령이다` 가 보인다. 실행하면 패널에 `✕` |
| T6 | 권한 모드에 따라 `ask` 가 어떻게 되나 | T5 를 default 모드와 bypass 모드에서 각각 | 관찰. bypass 에서 프롬프트가 뜨는지 |
| T7 | 핫 리로드 | `--plugin-dir` 세션 중 `register.tsx` 의 패널 문구를 고친다 | 다음 턴부터 바뀐 문구. 쌓인 기록(`$.state`)은 남는다 |

## 결과 기록

```
### T? — YYYY-MM-DD
- 실행:
- 관찰:
- 결론:
```

### T3 — 2026-10-09
- 실행: 다른 repo 를 탐구하는 세션에서 Claude 가 `ls` · `git status` · `git log` 를 실행
- 관찰: 패널에 6건이 `✓` 로 쌓였다. 첫 `ls -la` 가 2913ms
- 결론: 기록은 동작한다. 2913ms 는 T4 로 원인 확인 필요
