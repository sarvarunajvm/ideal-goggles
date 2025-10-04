import * as React from 'react'

type DialogContextValue = {
  open: boolean
  onOpenChange?: (open: boolean) => void
}

const DialogContext = React.createContext<DialogContextValue | null>(null)

export function Dialog({ open, onOpenChange, children }: { open: boolean; onOpenChange?: (open: boolean) => void; children: React.ReactNode }) {
  return <DialogContext.Provider value={{ open, onOpenChange }}>{children}</DialogContext.Provider>
}

export function DialogContent({ className, children, onInteractOutside, onEscapeKeyDown }: { className?: string; children: React.ReactNode; onInteractOutside?: (e: React.MouseEvent<HTMLDivElement>) => void; onEscapeKeyDown?: (e: KeyboardEvent) => void }) {
  const ctx = React.useContext(DialogContext)
  const overlayRef = React.useRef<HTMLDivElement | null>(null)
  React.useEffect(() => {
    if (!ctx?.open) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        if (onEscapeKeyDown) {
          onEscapeKeyDown(e)
          if (e.defaultPrevented) return
        }
        ctx.onOpenChange?.(false)
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [ctx?.open, onEscapeKeyDown, ctx?.onOpenChange])

  if (!ctx?.open) return null

  const handleOverlayClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (onInteractOutside) {
      onInteractOutside(e)
      if (e.defaultPrevented) return
    }
    ctx.onOpenChange?.(false)
  }

  return (
    <>
      <div ref={overlayRef} className="fixed inset-0 z-40 bg-black/80 backdrop-blur-md" onClick={handleOverlayClick} />
      <div className={`fixed left-1/2 top-1/2 z-50 w-full max-w-lg -translate-x-1/2 -translate-y-1/2 rounded-lg bg-card border border-primary/20 p-6 shadow-2xl shadow-primary/20 outline-none ${className ?? ''}`}>{children}</div>
    </>
  )
}

export function DialogHeader({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={`space-y-1.5 ${className ?? ''}`} {...props} />
}

export function DialogFooter({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={`mt-6 flex w-full items-center justify-end gap-2 ${className ?? ''}`} {...props} />
}

export function DialogTitle({ className, ...props }: React.HTMLAttributes<HTMLHeadingElement>) {
  return <h2 className={`text-lg font-semibold leading-none tracking-tight ${className ?? ''}`} {...props} />
}

export function DialogDescription({ className, ...props }: React.HTMLAttributes<HTMLParagraphElement>) {
  return <p className={`text-sm text-muted-foreground ${className ?? ''}`} {...props} />
}
