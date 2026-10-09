import { expect, test } from 'claude-code/testing'

import { isGhWrite } from '../hooks/gh'

test('gh 조회는 쓰기가 아니다', () => {
  expect(isGhWrite('gh pr list')).toBe(false)
  expect(isGhWrite('gh api repos/octo/hello/pulls')).toBe(false)
  expect(isGhWrite('ls -al')).toBe(false)
})

test('gh api 의 쓰기 메서드 · 필드와 PR · 이슈 쓰기는 쓰기다', () => {
  expect(isGhWrite('gh api -X POST repos/octo/hello/issues')).toBe(true)
  expect(isGhWrite('gh api repos/octo/hello/issues -f title=bug')).toBe(true)
  expect(isGhWrite('gh pr comment 12 --body "LGTM"')).toBe(true)
  expect(isGhWrite('gh issue create --title bug')).toBe(true)
})
