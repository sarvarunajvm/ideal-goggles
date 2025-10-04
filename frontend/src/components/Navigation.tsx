import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { useToast } from '@/components/ui/use-toast'
import { Search, Settings, Users, Camera, Menu, X, Activity, BookOpen, Package, ExternalLink } from 'lucide-react'
import { useDeveloperModeStore } from '../stores/developerModeStore'
import { getApiBaseUrl } from '../services/apiClient'

export default function Navigation() {
  const location = useLocation()
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
  const { isDeveloperMode, setDeveloperMode } = useDeveloperModeStore()
  const { toast } = useToast()
  const [clickCount, setClickCount] = useState(0)
  const [showCodePrompt, setShowCodePrompt] = useState(false)
  const [codeInput, setCodeInput] = useState('')

  const navItems = [
    { path: '/', label: 'Search', icon: Search },
    { path: '/people', label: 'People', icon: Users },
    { path: '/stats', label: 'Stats', icon: Activity },
    { path: '/settings', label: 'Settings', icon: Settings },
  ]

  // Add developer items when in developer mode
  const developerItems = isDeveloperMode ? [
    { path: '/dependencies', label: 'Dependencies', icon: Package },
  ] : []

  const allNavItems = [...navItems, ...developerItems]

  const handleIconClick = () => {
    const newCount = clickCount + 1
    setClickCount(newCount)

    if (newCount === 6) {
      setShowCodePrompt(true)
      setClickCount(0)
    }

    // Reset click count after 2 seconds
    setTimeout(() => setClickCount(0), 2000)
  }

  const handleCodeSubmit = () => {
    if (codeInput === '1996') {
      setDeveloperMode(true)
      setShowCodePrompt(false)
      setCodeInput('')
      toast({
        title: 'Developer Mode Enabled',
        description: 'Advanced features are now available',
      })
    } else {
      toast({
        title: 'Invalid Code',
        description: 'The code you entered is incorrect',
        variant: 'destructive',
      })
      setCodeInput('')
    }
  }

  return (
    <>
      {/* Developer Mode Code Dialog */}
      <Dialog open={showCodePrompt} onOpenChange={() => {}}>
        <DialogContent
          onInteractOutside={(e: Event) => e.preventDefault()}
          onEscapeKeyDown={(e: KeyboardEvent) => e.preventDefault()}
          className="sm:max-w-md"
        >
          <DialogHeader>
            <DialogTitle>Developer Mode</DialogTitle>
            <DialogDescription>
              Enter the access code to enable developer features
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <Input
              type="password"
              placeholder="Enter code"
              value={codeInput}
              onChange={(e) => setCodeInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  handleCodeSubmit()
                }
              }}
              autoFocus
              className="text-center text-lg tracking-widest"
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => {
              setShowCodePrompt(false)
              setCodeInput('')
            }}>
              Cancel
            </Button>
            <Button onClick={handleCodeSubmit}>
              Submit
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <nav className="bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 border-b border-border sticky top-0 z-50">
        <div className="px-4 sm:px-6">
          <div className="flex items-center justify-between h-14">
            {/* Logo and Brand */}
            <div className="flex items-center space-x-3">
              <div
                className="flex items-center justify-center w-8 h-8 bg-primary rounded-lg shadow-lg gradient-gold cursor-pointer transition-transform hover:scale-110"
                onClick={handleIconClick}
                title="Click 6 times for developer mode"
              >
                <Camera className="w-5 h-5 text-primary-foreground" />
              </div>
              <h1 className="text-lg font-semibold hidden sm:block text-primary">
                Ideal Goggles
              </h1>
            </div>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-1">
            {allNavItems.map(item => {
              const isActive = location.pathname === item.path
              const IconComponent = item.icon
              return (
                <Button
                  key={item.path}
                  variant="ghost"
                  size="sm"
                  asChild
                  className={`transition-all duration-200 ${
                    isActive
                      ? 'border-b-2 border-primary text-primary font-semibold shadow-lg shadow-primary/20 rounded-b-none bg-primary/5'
                      : 'hover:text-primary hover:bg-primary/5'
                  }`}
                >
                  <Link to={item.path} className="flex items-center space-x-2">
                    <IconComponent className="w-4 h-4" />
                    <span>{item.label}</span>
                  </Link>
                </Button>
              )
            })}
            {/* API Docs Link in Developer Mode */}
            {isDeveloperMode && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => window.open(`${getApiBaseUrl()}/docs`, '_blank')}
                className="transition-all duration-200 hover:text-primary hover:bg-primary/5"
                title="Open API Documentation"
              >
                <BookOpen className="w-4 h-4 mr-2" />
                <span>API Docs</span>
                <ExternalLink className="w-3 h-3 ml-1" />
              </Button>
            )}
          </div>

          {/* Mobile Menu Button */}
          <Button
            variant="ghost"
            size="icon"
            className="md:hidden"
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
          >
            {isMobileMenuOpen ? (
              <X className="w-5 h-5" />
            ) : (
              <Menu className="w-5 h-5" />
            )}
          </Button>
        </div>

        {/* Mobile Menu Dropdown */}
        {isMobileMenuOpen && (
          <div className="md:hidden pb-3 border-t border-border mt-2">
            <div className="flex flex-col space-y-1 pt-2">
              {allNavItems.map(item => {
                const isActive = location.pathname === item.path
                const IconComponent = item.icon
                return (
                  <Button
                    key={item.path}
                    variant="ghost"
                    size="sm"
                    asChild
                    className={`w-full justify-start transition-all duration-200 ${
                      isActive
                        ? 'border-l-4 border-primary text-primary font-semibold bg-primary/10 rounded-l-none'
                        : 'hover:text-primary hover:bg-primary/5'
                    }`}
                    onClick={() => setIsMobileMenuOpen(false)}
                  >
                    <Link
                      to={item.path}
                      className="flex items-center space-x-2"
                    >
                      <IconComponent className="w-4 h-4" />
                      <span>{item.label}</span>
                    </Link>
                  </Button>
                )
              })}
              {/* API Docs Link in Mobile Menu - Developer Mode */}
              {isDeveloperMode && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    window.open(`${getApiBaseUrl()}/docs`, '_blank')
                    setIsMobileMenuOpen(false)
                  }}
                  className="w-full justify-start transition-all duration-200 hover:text-primary hover:bg-primary/5"
                >
                  <BookOpen className="w-4 h-4 mr-2" />
                  <span>API Docs</span>
                  <ExternalLink className="w-3 h-3 ml-1" />
                </Button>
              )}
            </div>
          </div>
        )}
      </div>
    </nav>
    </>
  )
}
