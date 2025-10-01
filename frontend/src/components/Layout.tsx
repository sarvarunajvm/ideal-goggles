import { ReactNode } from 'react'
import Navigation from './Navigation'
import StatusBar from './StatusBar'

interface LayoutProps {
  children: ReactNode
}

export default function Layout({ children }: LayoutProps) {
  return (
    <div className="flex flex-col h-screen bg-background">
      {/* Top Navigation Bar */}
      <Navigation />

      {/* Main Content Area */}
      <main className="flex-1 overflow-auto">{children}</main>

      {/* Footer Status Bar */}
      <StatusBar />
    </div>
  )
}
