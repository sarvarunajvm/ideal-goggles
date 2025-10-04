import { ReactNode } from 'react'
import Navigation from './Navigation'
import StatusBar from './StatusBar'

interface LayoutProps {
  children: ReactNode
}

export default function Layout({ children }: LayoutProps) {
  return (
    <div className="flex flex-col h-screen bg-background text-foreground">
      {/* Top Navigation Bar */}
      <Navigation />

      {/* Main Content Area */}
      <main className="flex-1 overflow-auto bg-gradient-to-br from-background to-background/95">{children}</main>

      {/* Footer Status Bar */}
      <StatusBar />
    </div>
  )
}
