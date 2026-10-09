/** 실행한 Bash 명령 하나 */
export type CommandRecord = {
  command: string
  isOk: boolean
  /** 실행에 걸린 시간 */
  ms: number
}

declare module 'claude-code' {
  interface PluginState {
    'command-log': { records: CommandRecord[] }
  }
}
