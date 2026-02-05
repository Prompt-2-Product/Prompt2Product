'use client'

import Link from 'next/link'
import { Code2, LogOut, Menu, X } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Button } from '@/components/ui/button'
import { AuthModal } from '@/components/auth-modal'

export function Navigation() {
  const [user, setUser] = useState<{ name: string } | null>(null)
  const [authModalOpen, setAuthModalOpen] = useState(false)
  const [authMode, setAuthMode] = useState<'login' | 'signup'>('login')
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  useEffect(() => {
    const storedUser = localStorage.getItem('user')
    if (storedUser) {
      setUser(JSON.parse(storedUser))
    }
  }, [])

  const handleLogout = () => {
    localStorage.removeItem('user')
    setUser(null)
    window.location.href = '/'
  }



  return (
    <nav className="fixed top-0 left-0 right-0 z-50 border-b border-border bg-background/80 backdrop-blur-md">
      <div className="mx-auto max-w-7xl px-6 py-4">
        <div className="flex items-center justify-between">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
              <Code2 className="h-5 w-5" />
            </div>
            <span className="text-xl font-semibold text-foreground">Prompt2Product</span>
          </Link>

          {/* Center menu */}
          <div className="hidden items-center gap-8 md:flex">
            <Link href="/" className="text-sm text-muted-foreground hover:text-foreground transition-colors font-medium">Home</Link>
            <Link href="/about" className="text-sm text-muted-foreground hover:text-foreground transition-colors font-medium">About</Link>
            <Link href="#" className="text-sm text-muted-foreground hover:text-foreground transition-colors font-medium">Documentation</Link>
            <Link href="#" className="text-sm text-muted-foreground hover:text-foreground transition-colors font-medium">Templates</Link>
          </div>

          {/* Right side - Auth */}
          {user ? (
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2 rounded-full bg-secondary/50 px-4 py-2">
                <div className="h-6 w-6 rounded-full bg-primary flex items-center justify-center text-xs font-bold text-white">
                  {user.name.charAt(0).toUpperCase()}
                </div>
                <span className="text-sm font-medium text-foreground">{user.name}</span>
              </div>
              <Button
                onClick={handleLogout}
                variant="ghost"
                size="sm"
                className="text-muted-foreground hover:text-foreground hover:bg-secondary/50 gap-2"
              >
                <LogOut className="h-4 w-4" />
                Logout
              </Button>
            </div>
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
          />
        </div>

        {/* Mobile menu */}
        {mobileMenuOpen && (
          <div className="md:hidden border-t border-border bg-background/95 backdrop-blur-sm py-4 mt-4 space-y-2">
            <Link href="/" onClick={() => setMobileMenuOpen(false)} className="block px-4 py-2 text-foreground hover:bg-secondary/50 rounded-lg">
              Home
            </Link>
            <Link href="/about" onClick={() => setMobileMenuOpen(false)} className="block px-4 py-2 text-foreground hover:bg-secondary/50 rounded-lg">
              About
            </Link>
            <Link href="#" onClick={() => setMobileMenuOpen(false)} className="block px-4 py-2 text-muted-foreground hover:bg-secondary/50 rounded-lg">
              Documentation
            </Link>
            <Link href="#" onClick={() => setMobileMenuOpen(false)} className="block px-4 py-2 text-muted-foreground hover:bg-secondary/50 rounded-lg">
              Templates
            </Link>
          </div>
        )}
      </div>
    </nav>
  )
}
