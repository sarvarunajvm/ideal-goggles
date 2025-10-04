import { cva } from 'class-variance-authority'

export const badgeVariants = cva(
  'inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2',
  {
    variants: {
      variant: {
        default:
          'border-transparent [background:var(--gradient-gold)] text-black [box-shadow:var(--shadow-gold)] hover:scale-105 hover:[box-shadow:var(--shadow-gold-lg)]',
        secondary:
          'border-transparent [background:var(--gradient-purple)] text-white [box-shadow:var(--shadow-purple)] hover:scale-105 hover:[box-shadow:0_20px_40px_rgba(var(--purple-rgb),0.5)]',
        destructive:
          'border-transparent [background:var(--gradient-red)] text-white [box-shadow:var(--shadow-red)] hover:scale-105 hover:[box-shadow:0_20px_40px_rgba(var(--red-rgb),0.5)]',
        outline:
          'text-[var(--neon-cyan)] border-[var(--neon-cyan)]/50 [box-shadow:0_5px_15px_rgba(var(--cyan-rgb),0.3)] hover:[box-shadow:0_10px_25px_rgba(var(--cyan-rgb),0.5)] hover:bg-[var(--neon-cyan)]/10 hover:border-[var(--neon-cyan)]',
        success:
          'border-transparent [background:var(--gradient-green)] text-black [box-shadow:var(--shadow-green)] hover:scale-105 hover:[box-shadow:0_20px_40px_rgba(var(--green-rgb),0.5)]',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  }
)
