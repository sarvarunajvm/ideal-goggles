import { cn } from '@/lib/utils'

describe('cn', () => {
  it('merges class names while dropping falsy values', () => {
    expect(cn('one', undefined, null, false, 'two')).toBe('one two')
  })

  it('applies tailwind merge precedence when duplicates exist', () => {
    expect(cn('p-2', 'p-4')).toBe('p-4')
    expect(cn('text-sm', 'text-lg')).toBe('text-lg')
  })

  it('supports clsx-style objects and arrays', () => {
    expect(cn(['base', { active: true, disabled: false }])).toBe('base active')
  })
})

