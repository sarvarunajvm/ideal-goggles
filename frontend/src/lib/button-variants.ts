import { cva } from 'class-variance-authority'

export const buttonVariants = cva(
  'inline-flex items-center justify-center whitespace-nowrap rounded-lg text-sm font-medium ring-offset-background transition-all duration-200 ease-out focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50',
  {
    variants: {
      variant: {
        default: '[background:var(--gradient-gold)] text-black font-semibold shadow-md shadow-primary/30 hover:shadow-lg hover:shadow-primary/40 hover:scale-[1.02]',
        destructive:
          '[background:var(--gradient-red)] text-white font-semibold shadow-lg shadow-red-500/60 hover:shadow-xl hover:shadow-red-500/80 hover:scale-[1.02] border border-red-400/30 hover:border-red-300/50',
        outline:
          'border-2 border-primary/50 bg-transparent text-primary hover:bg-primary/10 hover:border-primary hover:shadow-md hover:shadow-primary/20',
        secondary:
          'bg-muted text-foreground hover:bg-muted/80 border border-border/50 hover:border-primary/30 shadow-sm hover:shadow-md hover:shadow-primary/10',
        ghost: 'hover:bg-primary/10 hover:text-primary hover:shadow-sm hover:shadow-primary/10',
        link: 'text-primary underline-offset-4 hover:underline transition-colors hover:text-primary/90',
      },
      size: {
        default: 'h-10 px-4 py-2',
        sm: 'h-9 rounded-md px-3',
        lg: 'h-11 rounded-md px-8',
        icon: 'h-10 w-10',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  }
)
