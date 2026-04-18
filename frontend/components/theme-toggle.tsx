'use client'

import * as React from 'react'
import { Moon, Sun } from 'lucide-react'
import { useTheme } from 'next-themes'
import { Button } from '@/components/ui/button'

export function ThemeToggle() {
  const { theme, setTheme } = useTheme()
  const [mounted, setMounted] = React.useState(false)

  // Avoid hydration mismatch by only rendering after mount
  React.useEffect(() => {
    setMounted(true)
  }, [])

  if (!mounted) {
    return (
      <Button variant="ghost" size="icon" className="w-10 h-10 rounded-full">
        <span className="sr-only">Toggle theme</span>
      </Button>
    )
  }

  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
      className="w-10 h-10 rounded-full transition-all duration-300 hover:bg-accent hover:text-accent-foreground"
    >
      {theme === 'dark' ? (
        <Sun className="h-5 w-5 transition-all text-yellow-400" />
      ) : (
        <Moon className="h-5 w-5 transition-all text-slate-900" />
      )}
      <span className="sr-only">Toggle theme</span>
    </Button>
  )
}
