'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Code2, LogOut, Menu, X, ChevronDown } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Button } from '@/components/ui/button'
import { ThemeToggle } from '@/components/theme-toggle'
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
  const isIdePage = pathname === '/ide'
  const isMinimalNav = isDescribePage || isGeneratingPage || isPreviewPage || isIdePage

  const navLinks = [
    { href: '/', label: 'Home' },
    { href: '/overview', label: 'Overview' },
  ]

  useEffect(() => {
    if (typeof window === 'undefined') return

    const storedUser = window.localStorage.getItem('user')
    if (storedUser) {
      setUser(JSON.parse(storedUser))
    }

    const handler = (event: Event) => {
      const detail = (event as CustomEvent<{ mode?: 'login' | 'signup'; postAuthRedirect?: string }>).detail || {}
      if (detail.mode) setAuthMode(detail.mode)
      if (detail.postAuthRedirect) {
        window.sessionStorage.setItem('postAuthRedirect', detail.postAuthRedirect)
      }
      setAuthModalOpen(true)
    }

    window.addEventListener('open-auth-modal', handler as EventListener)
    return () => window.removeEventListener('open-auth-modal', handler as EventListener)
  }, [])

  const handleLogout = () => {
    localStorage.removeItem('user')
    setUser(null)
    window.location.href = '/'
  }

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 h-16 border-b border-border bg-background/95 backdrop-blur-md">
      <div className="h-full w-full px-4 sm:px-6">
        <div className="flex h-full items-center justify-between gap-8">

          {/* ── Left: Logo ── */}
          <Link href="/" className="flex shrink-0 items-center gap-2.5 group">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground shadow-sm group-hover:shadow-primary/40 transition-shadow">
              <Code2 className="h-4 w-4" />
            </div>
            <span className="text-base font-semibold tracking-tight text-foreground">
              Prompt2Product
            </span>
          </Link>

          {/* ── Center: Nav links (full pages only) ── */}
          {!isMinimalNav && (
            <div className="hidden md:flex items-center gap-1">
              {navLinks.map(({ href, label }) => {
                const active = pathname === href
                return (
                  <Link
                    key={href}
                    href={href}
                    className={`relative px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${
                      active
                        ? 'text-foreground bg-secondary/60'
                        : 'text-muted-foreground hover:text-foreground hover:bg-secondary/40'
                    }`}
                  >
                    {label}
                    {active && (
                      <span className="absolute bottom-0 left-1/2 -translate-x-1/2 h-0.5 w-4 rounded-full bg-primary" />
                    )}
                  </Link>
                )
              })}
            </div>
          )}

          {/* ── Right: Controls ── */}
          <div className="flex shrink-0 items-center gap-2">
            <ThemeToggle />

            {/* Divider */}
            <div className="hidden sm:block h-5 w-px bg-border mx-1" />

            {user ? (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <button className="flex items-center gap-2 rounded-full bg-secondary/50 px-3 py-1.5 hover:bg-secondary/70 transition-colors outline-none border border-border/50">
                    <div className="h-5 w-5 rounded-full bg-primary flex items-center justify-center text-[10px] font-bold text-white">
                      {user.name.charAt(0).toUpperCase()}
                    </div>
                    <span className="text-sm font-medium text-foreground hidden sm:inline">{user.name}</span>
                    <ChevronDown className="h-3 w-3 text-muted-foreground" />
                  </button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-44">
                  <DropdownMenuItem onClick={handleLogout} variant="destructive" className="cursor-pointer gap-2">
                    <LogOut className="h-4 w-4" />
                    Sign out
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            ) : (
              <div className="flex items-center gap-1.5">
                <Button
                  onClick={() => { setAuthMode('login'); setAuthModalOpen(true) }}
                  variant="ghost"
                  size="sm"
                  className="h-8 px-4 text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-secondary/50"
                >
                  Sign In
                </Button>
                <Button
                  onClick={() => { setAuthMode('signup'); setAuthModalOpen(true) }}
                  size="sm"
                  className="h-8 px-4 text-sm font-medium bg-primary text-primary-foreground hover:bg-primary/90 shadow-sm"
                >
                  Sign Up
                </Button>
              </div>
            )}

            {/* Mobile hamburger */}
            {!isMinimalNav && (
              <button
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="md:hidden ml-1 p-1.5 text-muted-foreground hover:text-foreground hover:bg-secondary/50 rounded-md transition-colors"
                aria-label="Toggle menu"
              >
                {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Mobile dropdown */}
      {mobileMenuOpen && !isMinimalNav && (
        <div className="md:hidden border-t border-border bg-background/98 backdrop-blur-sm px-6 py-3 space-y-1">
          {navLinks.map(({ href, label }) => (
            <Link
              key={href}
              href={href}
              onClick={() => setMobileMenuOpen(false)}
              className="block px-3 py-2 rounded-md text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-secondary/50 transition-colors"
            >
              {label}
            </Link>
          ))}
        </div>
      )}

      <AuthModal
        isOpen={authModalOpen}
        onClose={() => setAuthModalOpen(false)}
        mode={authMode}
        onToggleMode={(mode) => setAuthMode(mode)}
      />
    </nav>
  )
}
