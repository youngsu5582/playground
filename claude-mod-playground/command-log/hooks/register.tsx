import { atom, read, update } from 'claude-code'
import type { Register } from 'claude-code'

import type { CommandRecord } from '../types'
import { isGhWrite } from './gh'

const PANE = 'command-log'
const MAX_RECORDS = 20
const records = atom({ plugin: 'command-log', key: 'records' } as const, [])

export const register: Register = (on, options) => {
  const isAskGhWrite = options.askGhWrite !== false

  // ① 세션이 열리면 /command-log 커맨드를 등록한다
  on('session.start', async ($, e, next) => {
    await $.command.register({
      name: 'command-log',
      description: 'Claude 가 실행한 Bash 명령을 패널로 본다. off 를 붙이면 닫는다',
      argumentHint: '[off]',
    })
    return next(e)
  })

  // ② /command-log 를 치면 패널을 열고 닫는다. 내 커맨드라 next 없이 직접 답한다
  on('command.run', { command: 'command-log' }, async ($, e) => {
    if (e.args.trim() === 'off') {
      await $.ui.close({ id: PANE })
      return { text: '명령 기록 패널을 닫았다.' }
    }
    await $.ui.open({ id: PANE, title: '명령 기록', focus: true })
    return { text: '명령 기록 패널을 열었다. 닫으려면 /command-log off' }
  })

  // ③ Bash 실행 앞뒤에 끼어, 걸린 시간과 성공 여부를 남긴다
  on('tool.call', { tool: 'Bash' }, async ($, e, next) => {
    const startedAt = await $.clock.now() // 실행 전
    const ran = await next(e) // 다음 차례로 넘긴다 (권한 → 실행)
    const ms = (await $.clock.now()) - startedAt // 실행 후
    const isOk = ran.deny === undefined && ran.isError !== true
    await update($, records, list => [...list, { command: e.command, isOk, ms }].slice(-MAX_RECORDS))
    $.ui.status(statusOf(await read($, records)))
    return ran // 결과는 반드시 돌려준다
  }).catch(($, e, next) => next(e)) // 기록하다 실패해도 명령은 그대로 진행한다

  // ④ gh 로 GitHub 에 쓰는 명령은 실행 전에 묻는다
  on('tool.check', { tool: 'Bash' }, async ($, e, next) => {
    const command = (e.input as { command?: string }).command ?? ''
    if (isAskGhWrite && isGhWrite(command)) {
      return { decision: 'ask', reason: 'gh 로 GitHub 에 쓰는 명령이다' }
    }
    return next(e) // 그 밖에는 원래 판정대로
  }).catch(() => ({ decision: 'ask' })) // 판정하다 실패하면 묻는 쪽으로

  // ⑤ 패널을 그린다. records 가 바뀌면 다시 불린다
  on('ui.render', { component: 'Pane', requestId: PANE }, async ($, e) => {
    const { Box, Text } = $.ui.resolve(e)
    const list = await read($, records)
    return (
      <Box flexDirection="column">
        {list.length === 0 && <Text dimColor>아직 실행한 명령이 없다.</Text>}
        {list.map((one, index) => (
          <Text key={`record-${index}`} color={one.isOk ? undefined : 'error'} wrap="truncate-end">
            {one.isOk ? '✓' : '✕'} {one.command} · {one.ms}ms
          </Text>
        ))}
      </Box>
    )
  })
}

/** 상태줄: `명령 12` 또는 `명령 12 · 실패 1` */
const statusOf = (list: CommandRecord[]): string => {
  const failed = list.filter(one => !one.isOk).length
  return failed > 0 ? `명령 ${list.length} · 실패 ${failed}` : `명령 ${list.length}`
}
