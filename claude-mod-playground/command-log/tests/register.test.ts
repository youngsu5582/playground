import { expect, mock, test } from 'claude-code/testing'

const PANE_PROPS = { title: '명령 기록', isFocused: false, bodyColumns: 80, placement: 'dock' as const, scroll: { offset: 0, bodyRows: 40 }, view: {} }

test('gh 쓰기는 묻고, 조회는 원래 판정대로 둔다', async ($, on) => {
  on('tool.check', () => ({ decision: 'allow' as const })) // 엔진의 원래 판정 자리
  const write = await $.tool.check({ tool: 'Bash', input: { command: 'gh pr comment 12 --body hi' } })
  expect(write.decision).toBe('ask')
  const read = await $.tool.check({ tool: 'Bash', input: { command: 'gh pr list' } })
  expect(read.decision).toBe('allow')
})

test('askGhWrite 를 끄면 gh 쓰기도 묻지 않는다', { options: { askGhWrite: false } }, async ($, on) => {
  on('tool.check', () => ({ decision: 'allow' as const }))
  const write = await $.tool.check({ tool: 'Bash', input: { command: 'gh pr comment 12 --body hi' } })
  expect(write.decision).toBe('allow')
})

test('Bash 실행을 기록해 상태줄과 패널에 보인다', async ($, on) => {
  mock.clock(on, { now: Date.parse('2026-10-08T00:00:00Z') })
  const statuses: Array<string | undefined> = []
  on('ui.status', (_, e) => {
    statuses.push(e.text)
    return { value: undefined }
  })
  on('tool.check', () => ({ decision: 'allow' as const }))
  on('tool.call', (_, e) => (e.command === 'false' ? { result: 'exit 1' as never, isError: true } : { result: 'ok' as never }) as never)

  await $.tool.call({ tool: 'Bash', command: 'ls' })
  await $.tool.call({ tool: 'Bash', command: 'false' })
  expect(statuses.at(-1)).toBe('명령 2 · 실패 1')

  for (const surface of ['terminal', 'desktop'] as const) {
    const pane = await $.ui.mount({ plugin: 'command-log', surface, component: 'Pane', requestId: 'command-log', props: PANE_PROPS, viewport: { columns: 80, rows: 40 } })
    expect(await pane.find({ type: 'Text', text: /✓ ls/ })).toBeDefined()
    expect(await pane.find({ type: 'Text', text: /✕ false/ })).toBeDefined()
    await pane.unmount()
  }
})

test('/command-log 는 패널을 열고, off 는 닫는다', async ($, on) => {
  const opened: string[] = []
  const closed: string[] = []
  on('ui.open', (_, e) => {
    opened.push(e.id)
    return { value: undefined as never }
  })
  on('ui.close', (_, e) => {
    closed.push(e.id)
    return { value: undefined as never }
  })
  const typed = (args: string) => ({ command: 'command-log', args, origin: { kind: 'composer' as const }, presentation: { isFullscreen: false, columns: 120 } })

  expect((await $.command.run(typed(''))).text).toContain('열었다')
  expect((await $.command.run(typed('off'))).text).toContain('닫았다')
  expect(opened).toEqual(['command-log'])
  expect(closed).toEqual(['command-log'])
})
