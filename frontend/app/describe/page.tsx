'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { Navigation } from '@/components/navigation'
import { Button } from '@/components/ui/button'
import { Plus, SlidersHorizontal } from 'lucide-react'

const APP_TYPES = [
  'Web App',
  'API Backend',
  'CLI Tool',
  'Data Analysis Script',
  'ML Pipeline',
  'Automation Script',
  'Scraper',
  'Chatbot',
  'Mobile App UI',
  'Desktop App',
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
  if (lowerText.includes('api') || lowerText.includes('backend') || lowerText.includes('server')) {
    return 'API Backend'
  }
  if (lowerText.includes('cli') || lowerText.includes('command line')) {
    return 'CLI Tool'
  }
  if (lowerText.includes('data') || lowerText.includes('analysis')) {
    return 'Data Analysis Script'
  }
  if (lowerText.includes('ml') || lowerText.includes('machine learning') || lowerText.includes('model')) {
    return 'ML Pipeline'
  }
  if (lowerText.includes('automation') || lowerText.includes('task')) {
    return 'Automation Script'
  }
  if (lowerText.includes('scrape') || lowerText.includes('crawler')) {
    return 'Scraper'
  }
  if (lowerText.includes('chat') || lowerText.includes('bot')) {
    return 'Chatbot'
  }
  if (lowerText.includes('web') || lowerText.includes('app') || lowerText.includes('site')) {
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

  return (
    <div className="min-h-screen text-foreground relative overflow-hidden">
      {/* Background gradient: mix of dark, blue, light blue, and subtle white glow */}
      <div
        className="pointer-events-none absolute inset-0 -z-10"
        aria-hidden="true"
        style={{
          backgroundImage:
            'radial-gradient(circle at top, rgba(15,23,42,1) 0%, rgba(2,6,23,1) 40%), ' +
            'radial-gradient(circle at 20% 80%, rgba(59,130,246,0.35) 0%, transparent 55%), ' +
            'radial-gradient(circle at 80% 20%, rgba(125,211,252,0.35) 0%, transparent 55%), ' +
            'radial-gradient(circle at center, rgba(255,255,255,0.04) 0%, transparent 60%)',
        }}
      />
      <Navigation />

      <main className="pt-24 pb-20">
        <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
          {/* Title */}
          <div className="mb-8 md:mb-12 text-center">
            <h1 className="text-3xl md:text-5xl font-bold text-foreground mb-3">
              Describe Your Project
            </h1>
            <p className="text-sm sm:text-base md:text-lg text-muted-foreground max-w-2xl mx-auto">
              Tell Prompt2Product what you want to build – we&apos;ll handle the stack, structure, and boilerplate.
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-[minmax(0,3fr)_minmax(260px,1.2fr)] gap-6 items-start">
            {/* Main prompt card */}
            <section className="rounded-2xl bg-card/90 border border-white/10 shadow-2xl backdrop-blur-sm px-4 sm:px-6 py-4 sm:py-5 flex flex-col gap-4">
              <div className="text-left">
                <label className="block text-xs sm:text-sm font-medium text-foreground mb-2">
                  What do you want to build?
                </label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Describe your app, API, or tool in natural language..."
                  className="w-full min-h-[140px] sm:min-h-[160px] rounded-xl bg-black/30 border border-border/60 px-3 sm:px-4 py-3 sm:py-4 text-sm sm:text-base text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent resize-vertical"
                />
              </div>

              <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 pt-1">
                <button
                  type="button"
                  onClick={() => setOptionsOpen((open) => !open)}
                  className="inline-flex items-center justify-center gap-2 rounded-full border border-border/70 bg-black/40 px-3 py-2 text-xs sm:text-sm text-muted-foreground hover:text-foreground hover:border-primary/60 hover:bg-black/60 transition-colors"
                >
                  <Plus className="w-3 h-3 sm:w-4 sm:h-4" />
                  <span>Project options</span>
                </button>

                <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 sm:gap-4">
                  <div className="text-[11px] sm:text-xs text-muted-foreground text-left sm:text-right">
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
              </div>
            </section>

            {/* Side options panel, controlled by "+" button */}
            <aside className="rounded-2xl bg-card/90 border border-border/80 shadow-xl backdrop-blur-sm p-5 sm:p-6">
              <div className="flex items-center justify-between mb-5">
                <h3 className="text-sm sm:text-base font-semibold text-foreground">Project Options</h3>
                <button
                  type="button"
                  onClick={() => setOptionsOpen((open) => !open)}
                  className="inline-flex items-center justify-center rounded-full border border-border/70 bg-black/30 p-1.5 text-muted-foreground hover:text-foreground hover:border-primary/60 hover:bg-black/60 transition-colors"
                  aria-label="Toggle project options"
                >
                  <SlidersHorizontal className="w-3.5 h-3.5" />
                </button>
              </div>

              <div className="space-y-4">
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
