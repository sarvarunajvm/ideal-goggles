import * as React from 'react'

type SelectContextValue = {
  value: string
  onValueChange: (v: string) => void
  open: boolean
  setOpen: (o: boolean) => void
}

const SelectContext = React.createContext<SelectContextValue | null>(null)

export function Select({ value, onValueChange, children }: { value: string; onValueChange: (v: string) => void; children: React.ReactNode }) {
  const [open, setOpen] = React.useState(false)
  return (
    <SelectContext.Provider value={{ value, onValueChange, open, setOpen }}>{children}</SelectContext.Provider>
  )
}

export function SelectValue() {
  return null
}

export function SelectTrigger({ id, children, className }: { id?: string; children?: React.ReactNode; className?: string }) {
  const ctx = React.useContext(SelectContext)
  if (!ctx) return null
  return (
    <button
      id={id}
      type="button"
      className={`flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ${className ?? ''}`}
      onClick={() => ctx.setOpen(!ctx.open)}
    >
      <span>{children}</span>
      <span className="opacity-60">▾</span>
    </button>
  )
}

export function SelectContent({ children, className }: { children: React.ReactNode; className?: string }) {
  const ctx = React.useContext(SelectContext)
  if (!ctx?.open) return null
  return (
    <div className={`z-50 mt-1 min-w-[8rem] overflow-hidden rounded-md border bg-popover text-popover-foreground shadow-md ${className ?? ''}`}>
      <div className="p-1">{children}</div>
    </div>
  )
}

export function SelectItem({ value, children, className }: { value: string; children: React.ReactNode; className?: string }) {
  const ctx = React.useContext(SelectContext)
  if (!ctx) return null
  return (
    <div
      role="option"
      className={`relative flex w-full cursor-default select-none items-center rounded-sm px-2 py-1.5 text-sm hover:bg-accent hover:text-accent-foreground ${className ?? ''}`}
      onClick={() => {
        ctx.onValueChange(value)
        ctx.setOpen(false)
      }}
    >
      {children}
    </div>
  )
}
