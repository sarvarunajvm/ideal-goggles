Design Tokens (Frontend)

- Primary: `--color-primary` = Amber 400 (`#facc15`)
- Primary Foreground: `--color-primary-foreground`
- Accent: `--color-accent` warmed to complement amber
- Background/Foreground: `--color-background`, `--color-foreground`
- Usage Guidelines:
  - Prefer `bg-primary`, `text-primary`, `text-primary-foreground` over literal blues
  - Use `bg-primary/10` for light tints; `hover:bg-primary/90` for hover states
  - For badges, use warmed hues with dark-mode variants: `dark:bg-…/30`, `dark:text-…/300`
  - Focus rings: `focus:ring-primary` and selection outlines: `ring-primary`
  - Add `transition-colors` to interactive components for subtle feedback

