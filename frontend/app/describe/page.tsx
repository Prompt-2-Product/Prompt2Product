'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { Navigation } from '@/components/navigation'
import { Button } from '@/components/ui/button'
import { SlidersHorizontal } from 'lucide-react'
import { api } from '@/lib/api'

const APP_TYPES = [
  'Web App',
  'Mobile App',
  'Desktop App',
]

const SIMPLE_PROMPTS = [
  'Create a simple todo list app',
  'Build a basic calculator',
  'Make a weather app',
  'Create a note-taking app',
  'Build a simple blog',
  'Make a contact form',
  'Create a timer app',
  'Build a quiz app',
  'Make a password generator',
  'Create a color picker tool',
]

const detectLanguage = (text: string): string => {
  const lowerText = text.toLowerCase()
  if (lowerText.includes('javascript') || lowerText.includes('react') || lowerText.includes('nextjs') || lowerText.includes('node')) {
    return 'JavaScript'
  }
  if (lowerText.includes('typescript') || lowerText.includes('ts')) {
    return 'TypeScript'
  }
  return 'Python'
}

const detectAppType = (text: string): string => {
  const lowerText = text.toLowerCase()
  if (lowerText.includes('mobile') || lowerText.includes('ios') || lowerText.includes('android') || lowerText.includes('phone') || lowerText.includes('tablet')) {
    return 'Mobile App'
  }
  if (lowerText.includes('desktop') || lowerText.includes('windows') || lowerText.includes('macos') || lowerText.includes('linux app')) {
    return 'Desktop App'
  }
  return 'Web App'
}

export default function DescribePage() {
  const router = useRouter()
  const [description, setDescription] = useState('')
  const [language, setLanguage] = useState('Python')
  const [appType, setAppType] = useState('Web App')
  const [additionalInstructions, setAdditionalInstructions] = useState('')
  const [autoDetect, setAutoDetect] = useState(true)
  const [optionsOpen, setOptionsOpen] = useState(false)
  const [currentPromptIndex, setCurrentPromptIndex] = useState(0)

  // Rotate through example prompts
  useEffect(() => {
    if (description.trim()) return // Don't rotate if user is typing

    const interval = setInterval(() => {
      setCurrentPromptIndex((prev) => (prev + 1) % SIMPLE_PROMPTS.length)
    }, 3000) // Change every 3 seconds

    return () => clearInterval(interval)
  }, [description])

  // Keep language & app type in sync when auto-detect is enabled
  useEffect(() => {
    if (!autoDetect) return
    if (!description.trim()) return

    const detectedLang = detectLanguage(description)
    const detectedType = detectAppType(description)
    setLanguage(detectedLang)
    setAppType(detectedType)
  }, [description, autoDetect])

  const handleGenerateProject = async () => {
    if (description.trim()) {
      try {
        // Ensure a fresh generation never accidentally enters modify flow.
        sessionStorage.removeItem('changeRequest')
        sessionStorage.removeItem('generationFlow')

        // Decide final language/appType based on auto-detect setting
        let finalLanguage = language
        let finalAppType = appType

        if (autoDetect) {
          finalLanguage = detectLanguage(description)
          finalAppType = detectAppType(description)
          setLanguage(finalLanguage)
          setAppType(finalAppType)
        }

        // 1. Create the project
        const project = await api.projects.create(description.slice(0, 30) || 'New Project')

        // 2. Start the run
        const run = await api.projects.startRun(project.id, description)

        // Store project info for the generating page
        sessionStorage.setItem('projectInfo', JSON.stringify({
          description,
          language: finalLanguage,
          appType: finalAppType,
          additionalInstructions,
          projectId: project.id,
          runId: run.run_id
        }))

        router.push('/generating')
      } catch (error) {
        console.error('Failed to generate project:', error)
        alert('Failed to connect to backend. Please make sure the backend is running.')
      }
    }
  }

  const handlePromptClick = (prompt: string) => {
    setDescription(prompt)
  }

  return (
    <div className="h-screen text-foreground relative overflow-hidden page-transition">
      {/* Cinematic Background Layer - RETAINED */}
      <div className="mesh-gradient" />
      <div className="technical-grid" />

      <Navigation />

      <main className="flex items-center justify-center h-[calc(100vh-4rem)] mt-16 overflow-hidden px-6 sm:px-10 lg:px-16 xl:px-24">
        <div className="w-full page-content">
          {/* Header - RESTORED SIZE */}
          <div className="mb-10 md:mb-12 text-center animate-in fade-in duration-1000">
            <h1 className="text-3xl sm:text-4xl md:text-5xl font-black mb-3 tracking-tighter text-foreground dark:text-white text-balance">
              Describe Your <span className="hero-text-accent">Project</span>
            </h1>
            <p className="text-sm sm:text-base md:text-lg text-muted-foreground max-w-2xl mx-auto font-light leading-relaxed">
              Tell Prompt2Product what you want to build, we&apos;ll handle the stack and structure.
            </p>
          </div>

          {/* Grid Layout - RESTORED PROPORTIONS */}
          <div className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-6 items-stretch">
            {/* Main prompt card - GLASS PANEL RETAINED */}
            <section className="rounded-2xl glass-panel bg-card/90 input-focal-glow px-4 sm:px-6 py-4 sm:py-5 flex flex-col gap-5 h-full relative overflow-hidden">
              <div className="text-center relative z-10">
                <label className="block text-xs sm:text-sm font-medium text-foreground mb-3">
                  What do you want to build?
                </label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder={description.trim() ? "Describe your app, API, or tool..." : SIMPLE_PROMPTS[currentPromptIndex]}
                  className="w-full min-h-[140px] sm:min-h-[160px] rounded-xl bg-secondary/30 border border-border/60 px-4 py-4 text-sm sm:text-base text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent resize-none text-center transition-all"
                />
              </div>

              {/* Suggestions - CENTERED */}
              {!description.trim() && (
                <div className="flex flex-wrap gap-2 justify-center relative z-10">
                  {SIMPLE_PROMPTS.slice(0, 4).map((prompt, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => handlePromptClick(prompt)}
                      className="text-xs sm:text-sm px-3 py-1.5 rounded-full bg-secondary/50 border border-border/50 text-muted-foreground hover:text-foreground hover:border-primary/60 hover:bg-secondary/80 transition-all shadow-sm"
                    >
                      {prompt}
                    </button>
                  ))}
                </div>
              )}

              {/* Action Area - CENTERED RESTORED */}
              <div className="flex flex-col items-center justify-center gap-4 pt-2 relative z-10">
                <div className="text-[11px] sm:text-xs text-muted-foreground text-center">
                  {autoDetect
                    ? 'Auto-detecting language & app type from your description'
                    : 'Using custom settings'}
                </div>
                <Button
                  onClick={handleGenerateProject}
                  disabled={!description.trim()}
                  size="lg"
                  className="btn-glow bg-primary hover:bg-primary/85 text-primary-foreground disabled:opacity-50 disabled:cursor-not-allowed font-semibold shadow-lg hover:shadow-xl px-10"
                >
                  Generate Project
                </Button>
              </div>
            </section>

            {/* Sidebar - RESTORED WIDTH & CONTENT */}
            <aside className="rounded-2xl glass-panel bg-card/90 p-5 sm:p-6 flex flex-col h-full relative overflow-hidden">
              <div className="flex items-center justify-between mb-6 relative z-10">
                <h3 className="text-sm sm:text-base font-semibold text-foreground">Project Options</h3>
                <button
                  type="button"
                  onClick={() => setOptionsOpen((open) => !open)}
                  className="lg:hidden inline-flex items-center justify-center rounded-full border border-border/70 bg-secondary/50 p-1.5 text-muted-foreground hover:text-foreground transition-colors"
                  aria-label="Toggle options"
                >
                  <SlidersHorizontal className="w-3.5 h-3.5" />
                </button>
              </div>

              <div className={`space-y-4 relative z-10 ${optionsOpen ? 'block' : 'hidden lg:block'}`}>
                {/* Auto-detect toggle */}
                <div className="flex items-start gap-3 rounded-xl bg-secondary/40 border border-border/60 px-3 py-3">
                  <div className="flex-1 min-w-0 text-xs sm:text-sm">
                    <p className="font-medium text-foreground leading-snug">Auto-detect settings</p>
                    <p className="text-[11px] text-muted-foreground leading-tight mt-1">
                      Let AI choose language & type.
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => setAutoDetect((v) => !v)}
                    className={`relative inline-flex h-6 w-10 flex-shrink-0 items-center rounded-full border transition-all ${autoDetect ? 'bg-primary border-primary' : 'bg-muted border-border'
                      }`}
                    role="switch"
                    aria-checked={autoDetect}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white shadow-md transition-transform ${autoDetect ? 'translate-x-5' : 'translate-x-1'
                        }`}
                    />
                  </button>
                </div>

                {/* Parameters - Standard size restored */}
                <div className="space-y-4">
                  <div className="space-y-1.5">
                    <label className="block text-[10px] font-bold text-muted-foreground/70 dark:text-muted-foreground uppercase tracking-widest">Language</label>
                    <select
                      value={language}
                      onChange={(e) => setLanguage(e.target.value)}
                      disabled={autoDetect}
                      className="w-full rounded-lg bg-secondary/50 dark:bg-white/5 border border-black/5 dark:border-white/10 px-3 py-2 text-foreground dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary disabled:opacity-50 transition-all appearance-none cursor-pointer"
                    >
                      <option className="bg-background text-foreground">Python</option>
                      <option className="bg-background text-foreground">JavaScript</option>
                      <option className="bg-background text-foreground">TypeScript</option>
                    </select>
                  </div>

                  <div className="space-y-1.5">
                    <label className="block text-[10px] font-bold text-muted-foreground/70 dark:text-muted-foreground uppercase tracking-widest">App Type</label>
                    <select
                      value={appType}
                      onChange={(e) => setAppType(e.target.value)}
                      disabled={autoDetect}
                      className="w-full rounded-lg bg-secondary/50 dark:bg-white/5 border border-black/5 dark:border-white/10 px-3 py-2 text-foreground dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary disabled:opacity-50 transition-all appearance-none cursor-pointer"
                    >
                      {APP_TYPES.map((type) => (
                        <option key={type} className="bg-background text-foreground">{type}</option>
                      ))}
                    </select>
                  </div>

                  <div className="space-y-1.5">
                    <label className="block text-[10px] font-bold text-muted-foreground/70 dark:text-muted-foreground uppercase tracking-widest">Additional Instructions</label>
                    <input
                      type="text"
                      value={additionalInstructions}
                      onChange={(e) => setAdditionalInstructions(e.target.value)}
                      placeholder="Specific requirements..."
                      className="w-full rounded-lg bg-secondary/50 dark:bg-white/5 border border-black/5 dark:border-white/10 px-3 py-2 text-foreground dark:text-white placeholder-muted-foreground/50 text-sm focus:outline-none focus:ring-2 focus:ring-primary transition-all"
                    />
                  </div>
                </div>
              </div>
            </aside>
          </div>
        </div>
      </main>
    </div>
  )
}
