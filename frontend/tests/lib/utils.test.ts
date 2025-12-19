import { cn } from '../../src/lib/utils';

describe('lib/utils', () => {
  describe('cn', () => {
    it('merges class names correctly', () => {
      expect(cn('class1', 'class2')).toBe('class1 class2');
    });

    it('handles conditional classes', () => {
      expect(cn('class1', true && 'class2', false && 'class3')).toBe('class1 class2');
    });

    it('merges tailwind classes using tailwind-merge', () => {
      // p-4 should override p-2
      expect(cn('p-2', 'p-4')).toBe('p-4');
      // text-red-500 should override text-blue-500
      expect(cn('text-blue-500', 'text-red-500')).toBe('text-red-500');
    });

    it('handles array inputs', () => {
      expect(cn(['class1', 'class2'])).toBe('class1 class2');
    });

    it('handles object inputs', () => {
      expect(cn({ class1: true, class2: false, class3: true })).toBe('class1 class3');
    });

    it('handles mixed inputs', () => {
      expect(cn('class1', ['class2', { class3: true }])).toBe('class1 class2 class3');
    });

    it('handles empty inputs', () => {
      expect(cn()).toBe('');
      expect(cn(null, undefined, false)).toBe('');
    });
  });
});

