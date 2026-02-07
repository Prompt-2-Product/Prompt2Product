'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Code2, LogOut, Menu, X, ChevronDown } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Button } from '@/components/ui/button'
import { AuthModal } from '@/components/auth-modal'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'

export function Navigation() {
  const pathname = usePathname()
  const [user, setUser] = useState<{ name: string } | null>(null)
  const [authModalOpen, setAuthModalOpen] = useState(false)
  const [authMode, setAuthMode] = useState<'login' | 'signup'>('login')
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const isDescribePage = pathname === '/describe'
  const isGeneratingPage = pathname === '/generating'
  const isPreviewPage = pathname === '/preview'
  const isMinimalNav = isDescribePage || isGeneratingPage || isPreviewPage

  useEffect(() => {
    if (typeof window === 'undefined') return

    const storedUser = window.localStorage.getItem('user')
    if (storedUser) {
      setUser(JSON.parse(storedUser))
    } else if (window.location.pathname === '/') {
      // Show sign-in dialog on first visit to the landing page if not logged in
      setAuthMode('login')
      setAuthModalOpen(true)
    }

    const handler = (event: Event) => {
      const detail = (event as CustomEvent<{ mode?: 'login' | 'signup'; postAuthRedirect?: string }>).detail || {}
      if (detail.mode) {
        setAuthMode(detail.mode)
      }
      if (detail.postAuthRedirect) {
        window.sessionStorage.setItem('postAuthRedirect', detail.postAuthRedirect)
      }
      setAuthModalOpen(true)
    }

    window.addEventListener('open-auth-modal', handler as EventListener)

    return () => {
      window.removeEventListener('open-auth-modal', handler as EventListener)
    }
  }, [])

  const handleLogout = () => {
    localStorage.removeItem('user')
    setUser(null)
    window.location.href = '/'
  }



  return (
    <nav className={`fixed top-0 left-0 right-0 z-50 border-b border-border ${isMinimalNav ? 'bg-background/80 backdrop-blur-md' : 'bg-background/80 backdrop-blur-md'}`}>
      <div className={`mx-auto max-w-7xl ${isMinimalNav ? 'px-4 py-2' : 'px-6 py-4'}`}>
        <div className="flex items-center justify-between">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2 sm:gap-3">
            <div className={`flex items-center justify-center rounded-lg bg-primary text-primary-foreground ${isMinimalNav ? 'h-7 w-7' : 'h-8 w-8'}`}>
              <Code2 className={isMinimalNav ? 'h-4 w-4' : 'h-5 w-5'} />
            </div>
            <span className={`font-semibold text-foreground ${isMinimalNav ? 'text-base' : 'text-xl'}`}>Prompt2Product</span>
          </Link>

          {/* Center menu - Hidden on describe and generating pages */}
          {!isMinimalNav && (
            <div className="hidden items-center gap-8 md:flex">
              <Link href="/" className="text-sm text-muted-foreground hover:text-foreground transition-colors font-medium">Home</Link>
              <Link href="/overview" className="text-sm text-muted-foreground hover:text-foreground transition-colors font-medium">Overview</Link>
            </div>
          )}

          {/* Right side - Auth */}
          {user ? (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <button className="flex items-center gap-2 rounded-full bg-secondary/50 px-3 sm:px-4 py-1.5 sm:py-2 hover:bg-secondary/70 transition-colors outline-none">
                  <div className="h-6 w-6 rounded-full bg-primary flex items-center justify-center text-xs font-bold text-white">
                    {user.name.charAt(0).toUpperCase()}
                  </div>
                  <span className="text-sm font-medium text-foreground hidden sm:inline">{user.name}</span>
                  <ChevronDown className="h-3 w-3 text-muted-foreground hidden sm:block" />
                </button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-48">
                <DropdownMenuItem onClick={handleLogout} variant="destructive" className="cursor-pointer">
                  <LogOut className="h-4 w-4" />
                  Logout
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          ) : (
            <div className="flex items-center gap-3">
              <Button
                onClick={() => {
                  setAuthMode('login')
                  setAuthModalOpen(true)
                }}
                variant="ghost"
                size="sm"
                className="btn-glow text-foreground hover:bg-secondary/50 font-medium"
              >
                Sign In
              </Button>
              <Button
                onClick={() => {
                  setAuthMode('signup')
                  setAuthModalOpen(true)
                }}
                variant="ghost"
                size="sm"
                className="btn-glow text-foreground hover:bg-secondary/50 font-medium"
              >
                Sign Up
              </Button>
            </div>
          )}

          {/* Mobile menu button */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden p-2 text-foreground hover:bg-secondary/50 rounded-lg"
          >
            {mobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
          </button>

          <AuthModal
            isOpen={authModalOpen}
            onClose={() => setAuthModalOpen(false)}
            mode={authMode}
            onToggleMode={(mode) => setAuthMode(mode)}
          />
        </div>

        {/* Mobile menu - Hidden on describe and generating pages */}
        {mobileMenuOpen && !isMinimalNav && (
          <div className="md:hidden border-t border-border bg-background/95 backdrop-blur-sm py-4 mt-4 space-y-2">
            <Link href="/" onClick={() => setMobileMenuOpen(false)} className="block px-4 py-2 text-foreground hover:bg-secondary/50 rounded-lg">
              Home
            </Link>
            <Link href="/overview" onClick={() => setMobileMenuOpen(false)} className="block px-4 py-2 text-foreground hover:bg-secondary/50 rounded-lg">
              Overview
            </Link>
          </div>
        )}
      </div>
    </nav>
  )
}
