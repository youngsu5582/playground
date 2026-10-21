/** gh 로 GitHub 에 쓰는 명령인가: gh api 의 쓰기 메서드 · 필드, 또는 PR · 이슈에 쓰는 하위 명령 */
export const isGhWrite = (command: string): boolean => {
  if (/\bgh\s+api\b/.test(command)) {
    return /(-X|--method)[\s=]*(POST|PUT|PATCH|DELETE)\b/i.test(command) || /\s(-f|-F|--field|--raw-field|--input)\s/.test(command)
  }
  return /\bgh\s+(pr|issue)\s+(create|comment|edit|close|merge|review)\b/.test(command)
}
