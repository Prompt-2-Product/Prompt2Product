'use client'

import React from "react"

import { useState } from 'react'
import { X, Mail, Github } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface AuthModalProps {
  isOpen: boolean
  onClose: () => void
  mode: 'login' | 'signup'
  onToggleMode?: (mode: 'login' | 'signup') => void
}

export function AuthModal({ isOpen, onClose, mode, onToggleMode }: AuthModalProps) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [name, setName] = useState('')

  // Add blur effect to body when modal is open
  React.useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden'
      const main = document.querySelector('main')
      if (main) {
        main.style.filter = 'blur(4px)'
        main.style.pointerEvents = 'none'
      }
    } else {
      document.body.style.overflow = 'unset'
      const main = document.querySelector('main')
      if (main) {
        main.style.filter = 'blur(0px)'
        main.style.pointerEvents = 'auto'
      }
    }
    return () => {
      document.body.style.overflow = 'unset'
      const main = document.querySelector('main')
      if (main) {
        main.style.filter = 'blur(0px)'
        main.style.pointerEvents = 'auto'
      }
    }
  }, [isOpen])

  if (!isOpen) return null

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    const completeAuth = (userData: { name: string; email?: string }) => {
      // Persist user
      localStorage.setItem('user', JSON.stringify(userData))

      // Check if we have a post-auth redirect path
      const redirectPath = sessionStorage.getItem('postAuthRedirect')
      if (redirectPath) {
        sessionStorage.removeItem('postAuthRedirect')
        window.location.href = redirectPath
        return
      }

      // Default: close modal and refresh to update UI
      onClose()
      window.location.reload()
    }

    if (mode === 'signup' && name && email && password) {
      completeAuth({ name, email })
    } else if (mode === 'login' && email && password) {
      completeAuth({ name: email.split('@')[0] })
    }
  }

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/85 backdrop-blur-xl z-40 transition-opacity duration-300"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Modal Container - Fixed positioning with proper centering */}
      {/* Modal Container - Fixed positioning with proper centering */}
<div 
  className="fixed inset-0 z-50 overflow-y-auto flex min-h-screen py-8 px-4 justify-center" 
  role="dialog" 
  aria-modal="true"
>
  <div
    className="my-auto w-full max-w-md bg-card border border-border/60 rounded-3xl shadow-2xl relative animate-in fade-in zoom-in-95 duration-300 flex-shrink-0 max-h-[calc(100vh-4rem)] flex flex-col"
    onClick={(e) => e.stopPropagation()}
  >
          {/* Close Button */}
          <button
            onClick={onClose}
            className="absolute top-6 right-6 p-2 hover:bg-secondary/70 rounded-lg transition-colors z-10"
            aria-label="Close"
          >
            <X className="w-6 h-6 text-muted-foreground hover:text-foreground transition-colors" />
          </button>

          {/* Content Container */}
          <div className="p-7 sm:p-9 overflow-y-auto flex-1">
            {/* Title */}
            <h2 className="text-xl sm:text-2xl font-bold text-foreground mb-1">
              {mode === 'login' ? 'Welcome Back' : 'Create Account'}
            </h2>
            <p className="text-xs sm:text-sm text-muted-foreground mb-5">
              {mode === 'login'
                ? 'Sign in to your account to continue'
                : 'Start building with Prompt2Product'}
            </p>

            {/* Auth Provider Buttons */}
            <div className="space-y-2 mb-5">
            <button className="w-full flex items-center justify-center gap-3 px-3 py-2.5 bg-secondary/60 hover:bg-secondary/80 active:bg-secondary rounded-lg text-foreground text-xs sm:text-sm font-medium transition-all duration-200 border border-border/40 hover:border-border/60">
              <svg
                className="w-4 h-4 flex-shrink-0"
                viewBox="0 0 24 24"
                fill="currentColor"
              >
                <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
                <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
              </svg>
              <span>Google</span>
            </button>

            <button className="w-full flex items-center justify-center gap-3 px-4 py-3 bg-secondary/60 hover:bg-secondary/80 active:bg-secondary rounded-xl text-foreground text-sm font-medium transition-all duration-200 border border-border/40 hover:border-border/60">
              <svg
                className="w-4 h-4 flex-shrink-0"
                fill="currentColor"
                viewBox="0 0 24 24"
              >
                <path d="M17.05 13.5c-.91 0-1.74.46-2.24 1.14.02-.09.05-.17.05-.27 0-.55-.45-1-1-1s-1 .45-1 1c0 .1.02.19.05.27-.5-.68-1.33-1.14-2.24-1.14-1.66 0-3 1.34-3 3s1.34 3 3 3c.91 0 1.74-.46 2.24-1.14-.02.09-.05.17-.05.27 0 .55.45 1 1 1s1-.45 1-1c0-.1-.02-.19-.05-.27.5.68 1.33 1.14 2.24 1.14 1.66 0 3-1.34 3-3s-1.34-3-3-3z" />
              </svg>
              <span>Apple</span>
            </button>

            <button className="w-full flex items-center justify-center gap-3 px-4 py-3 bg-secondary/60 hover:bg-secondary/80 active:bg-secondary rounded-xl text-foreground text-sm font-medium transition-all duration-200 border border-border/40 hover:border-border/60">
              <Mail className="w-4 h-4 flex-shrink-0" />
              <span>Email</span>
            </button>
          </div>

            {/* Divider */}
            <div className="flex items-center gap-2 mb-5">
              <div className="flex-1 h-px bg-border/40" />
              <span className="text-xs font-medium text-muted-foreground">OR</span>
              <div className="flex-1 h-px bg-border/40" />
            </div>

            {/* Form */}
            <form onSubmit={handleSubmit} className="space-y-3">
              {mode === 'signup' && (
                <div>
                  <label className="block text-xs font-semibold text-foreground mb-1.5 uppercase tracking-wide">
                    Full Name
                  </label>
                  <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="John Doe"
                    className="w-full px-3 py-2 bg-secondary/50 border border-border/40 rounded-lg text-xs sm:text-sm text-foreground placeholder-muted-foreground/60 focus:outline-none focus:border-primary/60 focus:ring-2 focus:ring-primary/20 transition-all duration-200"
                  />
                </div>
              )}

              <div>
                <label className="block text-xs font-semibold text-foreground mb-1.5 uppercase tracking-wide">
                  Email
                </label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  className="w-full px-3 py-2 bg-secondary/50 border border-border/40 rounded-lg text-xs sm:text-sm text-foreground placeholder-muted-foreground/60 focus:outline-none focus:border-primary/60 focus:ring-2 focus:ring-primary/20 transition-all duration-200"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-foreground mb-1.5 uppercase tracking-wide">
                  Password
                </label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full px-3 py-2 bg-secondary/50 border border-border/40 rounded-lg text-xs sm:text-sm text-foreground placeholder-muted-foreground/60 focus:outline-none focus:border-primary/60 focus:ring-2 focus:ring-primary/20 transition-all duration-200"
                />
              </div>

              <Button
                type="submit"
                className="btn-glow w-full bg-primary hover:bg-primary/85 active:bg-primary text-primary-foreground font-semibold py-2 rounded-lg mt-1 transition-all duration-200 text-sm"
              >
                {mode === 'login' ? 'Sign In' : 'Sign Up'}
              </Button>
            </form>

            {/* Toggle Auth Mode */}
            <div className="mt-4 text-center text-xs text-muted-foreground">
              {mode === 'login' ? "Don't have an account? " : 'Already have an account? '}
              <button
                onClick={() => {
                  const nextMode = mode === 'login' ? 'signup' : 'login'
                  if (onToggleMode) {
                    onToggleMode(nextMode)
                  }
                }}
                className="text-primary hover:text-primary/80 font-semibold transition-colors"
              >
                {mode === 'login' ? 'Sign Up' : 'Log In'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </>
  )
}
