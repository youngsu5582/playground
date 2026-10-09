# claude-mod-playground

Claude Code Mod(함수 훅 플러그인)를 직접 띄워, 이벤트에 끼어드는 동작을 관찰하는 playground.

**완료 기준**: `command-log` 를 띄워 Bash 명령이 패널에 쌓이고, gh 쓰기 명령에서 권한 프롬프트가 뜨는 것을 직접 본다.

## 사전 준비

- Claude Code 2.1.294 이상. Mod 는 early access 라 API 가 예고 없이 바뀔 수 있다.
- gh CLI. T5 는 없는 저장소로 시험하므로 로그인은 필요 없다.

## 실행

```bash
claude --plugin-dir ./command-log
```

세션에서 `/command-log` 를 치면 패널이 열린다. 닫기는 `/command-log off`.
`--plugin-dir` 로 연 동안에는 파일을 고칠 때마다 다시 읽는다.

설치해서 쓰려면 이 폴더를 marketplace 로 쓴다. 세션 프롬프트에 입력한다.

```
/plugin install command-log --marketplace <이 폴더의 절대 경로>
```

테스트는 [TESTING.md](TESTING.md).

## 비용

0. 로컬에서만 돈다.

## 정리

- `--plugin-dir` 로 띄웠다면 세션을 닫으면 끝이다.
- 설치했다면 `/plugin` 메뉴에서 `command-log` 를 지운다.

## 구조

```
claude-mod-playground/
├── .claude-plugin/marketplace.json   # 이 폴더를 설치 목록으로 만든다
├── command-log/                      # mod 본체
│   ├── .claude-plugin/plugin.json    # 이름 · 설명 · 사용자 설정(askGhWrite)
│   ├── hooks/hooks.json              # 어느 코드 파일을 읽을지
│   ├── hooks/register.tsx            # 훅 등록 (session.start · command.run · tool.call · tool.check · ui.render)
│   ├── hooks/gh.ts                   # gh 쓰기 판정
│   ├── types/index.d.ts              # 상태(records) 타입
│   └── tests/                        # claude plugin test
├── README.md
└── TESTING.md
```
