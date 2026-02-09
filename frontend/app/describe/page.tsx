'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { Navigation } from '@/components/navigation'
import { Button } from '@/components/ui/button'
import { SlidersHorizontal } from 'lucide-react'

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
  // Default to Web App for web-related terms or if no specific platform is mentioned
  if (lowerText.includes('web') || lowerText.includes('app') || lowerText.includes('site') || lowerText.includes('browser')) {
    return 'Web App'
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
      // Decide final language/appType based on auto-detect setting
      let finalLanguage = language
      let finalAppType = appType

      if (autoDetect) {
        finalLanguage = detectLanguage(description)
        finalAppType = detectAppType(description)
        setLanguage(finalLanguage)
        setAppType(finalAppType)
      }

      // Mock implementation - no backend calls
      // Generate dummy project and run IDs
      const mockProjectId = Math.floor(Math.random() * 1000) + 1
      const mockRunId = Math.floor(Math.random() * 10000) + 1

      // Store project info for the generating page
      sessionStorage.setItem('projectInfo', JSON.stringify({
        description,
        language: finalLanguage,
        appType: finalAppType,
        additionalInstructions,
        projectId: mockProjectId,
        runId: mockRunId
      }))
      
      // Small delay to simulate API call
      await new Promise(resolve => setTimeout(resolve, 300))
      router.push('/generating')
    }
  }

  const handlePromptClick = (prompt: string) => {
    setDescription(prompt)
  }

  return (
<<<<<<< Updated upstream
    <div className="min-h-screen text-foreground relative overflow-hidden">
      {/* Overview gradient background - light pastel blue to cyan-blue */}
=======
    <div className="min-h-screen text-foreground relative overflow-hidden page-transition">
      {/* Multi-color vertical gradient background */}
>>>>>>> Stashed changes
      <div
        className="pointer-events-none absolute inset-0 -z-10"
        aria-hidden="true"
        style={{
          background: 'linear-gradient(to bottom, rgb(0, 0, 0) 0%, rgb(30, 58, 138) 33%, rgb(59, 130, 246) 66%, rgb(255, 255, 255) 100%)',
        }}
      />
      <Navigation />

      <main className="flex items-center justify-center min-h-[calc(100vh-5rem)] pt-8 sm:pt-16 md:pt-24 pb-8 sm:pb-16">
        <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8 w-full">
          {/* Title - Centered */}
          <div className="mb-12 md:mb-14 text-center">
            <h1 className="text-3xl sm:text-4xl md:text-5xl font-bold text-white mb-3">
              Describe Your Project
            </h1>
<<<<<<< Updated upstream
            <p className="text-sm sm:text-base md:text-lg text-slate-700 dark:text-slate-800 max-w-2xl mx-auto">
              Tell Prompt2Product what you want to build – we&apos;ll handle the stack, structure, and boilerplate.
=======
            <p className="text-sm sm:text-base md:text-lg text-white max-w-2xl mx-auto">
              Tell Prompt2Product what you want to build – we&apos;ll handle the stack and structure.
>>>>>>> Stashed changes
            </p>
          </div>

          {/* Chatbox and options side by side */}
          <div className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-6 items-stretch">
            {/* Main prompt card - Centered */}
            <section className="rounded-2xl bg-card/90 border border-white/10 shadow-2xl backdrop-blur-sm px-4 sm:px-6 py-4 sm:py-5 flex flex-col gap-4 h-full">
              <div className="text-center">
                <label className="block text-xs sm:text-sm font-medium text-foreground mb-2">
                  What do you want to build?
                </label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder={description.trim() ? "Describe your app, API, or tool in natural language..." : SIMPLE_PROMPTS[currentPromptIndex]}
                  className="w-full min-h-[120px] sm:min-h-[140px] rounded-xl bg-black/30 border border-border/60 px-3 sm:px-4 py-3 sm:py-4 text-sm sm:text-base text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent resize-vertical text-center"
                />
              </div>

              {/* Example prompts - Simple showcase */}
              {!description.trim() && (
                <div className="flex flex-wrap gap-2 justify-center">
                  {SIMPLE_PROMPTS.slice(0, 4).map((prompt, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => handlePromptClick(prompt)}
                      className="text-xs sm:text-sm px-3 py-1.5 rounded-full bg-secondary/50 border border-border/50 text-muted-foreground hover:text-foreground hover:border-primary/60 hover:bg-secondary/80 transition-colors"
                    >
                      {prompt}
                    </button>
                  ))}
                </div>
              )}

              <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-1">
                <div className="text-[11px] sm:text-xs text-muted-foreground text-center">
                  {autoDetect
                    ? 'Auto-detecting language & app type from your description'
                    : 'Using your custom language & app type settings'}
                </div>
                <Button
                  onClick={handleGenerateProject}
                  disabled={!description.trim()}
                  size="lg"
                  className="btn-glow bg-primary hover:bg-primary/85 text-primary-foreground disabled:opacity-50 disabled:cursor-not-allowed font-semibold shadow-lg hover:shadow-xl px-6 sm:px-8"
                >
                  Generate Project
                </Button>
              </div>
            </section>

            {/* Side options panel - Always visible on right */}
            <aside className="rounded-2xl bg-card/90 border border-white/10 shadow-2xl backdrop-blur-sm p-5 sm:p-6 flex flex-col h-full">
              <div className="flex items-center justify-between mb-5">
                <h3 className="text-sm sm:text-base font-semibold text-foreground">Project Options</h3>
                <button
                  type="button"
                  onClick={() => setOptionsOpen((open) => !open)}
                  className="lg:hidden inline-flex items-center justify-center rounded-full border border-border/70 bg-black/30 p-1.5 text-muted-foreground hover:text-foreground hover:border-primary/60 hover:bg-black/60 transition-colors"
                  aria-label="Toggle project options"
                >
                  <SlidersHorizontal className="w-3.5 h-3.5" />
                </button>
              </div>

              <div className={`space-y-4 ${optionsOpen ? 'block' : 'hidden lg:block'}`}>
                {/* Auto-detect toggle */}
                <div className="flex items-center justify-between rounded-lg bg-black/30 border border-border/70 px-3 py-2.5">
                  <div className="text-xs sm:text-sm">
                    <p className="font-medium text-foreground">Auto-detect settings</p>
                    <p className="text-[11px] sm:text-xs text-muted-foreground">
                      Let Prompt2Product choose language & app type from your description.
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => setAutoDetect((v) => !v)}
                    className={`relative inline-flex h-6 w-10 items-center rounded-full border transition-colors ${
                      autoDetect ? 'bg-primary/80 border-primary' : 'bg-black/40 border-border'
                    }`}
                    role="switch"
                    aria-checked={autoDetect}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform ${
                        autoDetect ? 'translate-x-4' : 'translate-x-1'
                      }`}
                    />
                  </button>
                </div>

                {/* Language Dropdown */}
                <div className="space-y-1.5">
                  <label className="block text-xs font-medium text-muted-foreground">Language</label>
                  <select
                    value={language}
                    onChange={(e) => setLanguage(e.target.value)}
                    disabled={autoDetect}
                    className="w-full rounded-lg bg-secondary border border-border px-3 py-2 text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary disabled:opacity-60 disabled:cursor-not-allowed"
                  >
                    <option>Python</option>
                    <option>JavaScript</option>
                    <option>TypeScript</option>
                  </select>
                </div>

                {/* App Type Dropdown */}
                <div className="space-y-1.5">
                  <label className="block text-xs font-medium text-muted-foreground">App Type</label>
                  <select
                    value={appType}
                    onChange={(e) => setAppType(e.target.value)}
                    disabled={autoDetect}
                    className="w-full rounded-lg bg-secondary border border-border px-3 py-2 text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary disabled:opacity-60 disabled:cursor-not-allowed"
                  >
                    {APP_TYPES.map((type) => (
                      <option key={type}>{type}</option>
                    ))}
                  </select>
                </div>

                {/* Additional Instructions */}
                <div className="space-y-1.5">
                  <label className="block text-xs font-medium text-muted-foreground">Additional Instructions</label>
                  <input
                    type="text"
                    value={additionalInstructions}
                    onChange={(e) => setAdditionalInstructions(e.target.value)}
                    placeholder="Any specific requirements..."
                    className="w-full rounded-lg bg-secondary border border-border px-3 py-2 text-foreground placeholder-muted-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                  />
                </div>
              </div>
            </aside>
          </div>
        </div>
      </main>
    </div>
  )
}
