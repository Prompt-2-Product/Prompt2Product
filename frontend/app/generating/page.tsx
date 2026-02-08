'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { Navigation } from '@/components/navigation'
import { Check, Loader } from 'lucide-react'

export default function GeneratingPage() {
  const router = useRouter()
  const [currentStep, setCurrentStep] = useState(1)
  const [progress, setProgress] = useState(0)
  const [logs, setLogs] = useState<string[]>([
    '[INFO] Initializing project generation...',
  ])
  const [projectInfo, setProjectInfo] = useState<{ description: string; language: string; appType: string } | null>(null)

  useEffect(() => {
    const stored = sessionStorage.getItem('projectInfo')
    if (!stored) {
      // If no project info, redirect to describe page
      router.push('/describe')
      return
    }

    const parsed = JSON.parse(stored)
    const { projectId, runId, description, language, appType } = parsed
    if (!projectId || !runId) {
      router.push('/describe')
      return
    }

    // Store project info for display
    setProjectInfo({ description, language, appType })

    // Mock implementation - simulate generation progress
    const mockLogs = [
      '[INFO] Starting project generation...',
      '[INFO] Analyzing prompt and extracting requirements...',
      '[INFO] Building project specification...',
      '[INFO] Generating code structure...',
      '[INFO] Creating main application files...',
      '[INFO] Setting up dependencies...',
      '[INFO] Writing configuration files...',
      '[INFO] Validating generated code...',
      '[INFO] Running tests...',
      '[INFO] Project generation completed successfully!',
    ]

    let logIndex = 0
    let progressValue = 0
    let stepValue = 1

    const simulateProgress = () => {
      // Add logs progressively
      if (logIndex < mockLogs.length) {
        setLogs(prev => [...prev, mockLogs[logIndex]])
        logIndex++
      }

      // Update progress and steps - faster increments
      if (progressValue < 30) {
        progressValue += 8
        stepValue = 1
      } else if (progressValue < 60) {
        progressValue += 8
        stepValue = 2
      } else if (progressValue < 90) {
        progressValue += 8
        stepValue = 3
      } else if (progressValue < 100) {
        progressValue += 5
        stepValue = 3
      } else {
        // Complete
        setProgress(100)
        setCurrentStep(3)
        setTimeout(() => router.push('/preview'), 1000)
        return
      }

      setProgress(progressValue)
      setCurrentStep(stepValue)
    }

    // Start simulation - faster progress
    const intervalId = setInterval(simulateProgress, 800)

    return () => clearInterval(intervalId)
  }, [router])

  const steps = [
    { number: 1, label: 'Understanding Prompt' },
    { number: 2, label: 'Generating Skeleton' },
    { number: 3, label: 'Validating' },
  ]

  return (
    <div className="min-h-screen text-foreground relative overflow-hidden page-transition">
      {/* Light blue gradient background - matching describe page */}
      <div
        className="pointer-events-none absolute inset-0 -z-10"
        aria-hidden="true"
        style={{
          background: 'linear-gradient(135deg, rgb(147, 197, 253) 0%, rgb(165, 243, 252) 50%, rgb(191, 219, 254) 100%)',
        }}
      />
      <Navigation />

      <main className="absolute inset-x-0 top-[3rem] bottom-0 flex flex-col lg:flex-row">
        {/* Left: Chat Interface - Fixed Size */}
        <aside className="w-full lg:w-[380px] border-r border-border/50 bg-background flex flex-col flex-shrink-0 h-full">
          {/* Chat Header - Enhanced */}
          <div className="px-5 py-4 border-b border-border/50 flex-shrink-0 bg-background backdrop-blur-sm">
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <h2 className="text-base font-semibold text-foreground mb-1">Project Chat</h2>
                {projectInfo && (
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-xs px-2 py-0.5 rounded-md bg-primary/10 text-primary border border-primary/20">
                      {projectInfo.language}
                    </span>
                    <span className="text-xs px-2 py-0.5 rounded-md bg-secondary/50 text-foreground border border-border/50">
                      {projectInfo.appType}
                    </span>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Chat Messages Area - Enhanced with better spacing */}
          <div className="flex-1 overflow-y-auto px-5 py-4 space-y-5 custom-scrollbar min-h-0">
            {/* User Message - Improved styling */}
            {projectInfo && (
              <div className="flex flex-col gap-2.5">
                <div className="flex items-center gap-2">
                  <div className="h-6 w-6 rounded-full bg-primary/20 flex items-center justify-center">
                    <span className="text-xs font-semibold text-primary">U</span>
                  </div>
                  <span className="text-xs font-medium text-muted-foreground">You</span>
                </div>
                <div className="ml-8 rounded-xl bg-secondary/60 border border-border/60 p-4 text-sm leading-relaxed text-foreground whitespace-pre-wrap break-words shadow-sm">
                  {projectInfo.description}
                </div>
              </div>
            )}

            {/* System Response - Enhanced styling */}
            <div className="flex flex-col gap-2.5">
              <div className="flex items-center gap-2">
                <div className="h-6 w-6 rounded-full bg-gradient-to-r from-blue-500 to-cyan-500 flex items-center justify-center">
                  <span className="text-xs font-semibold text-white">P</span>
                </div>
                <span className="text-xs font-medium text-muted-foreground">Prompt2Product</span>
              </div>
              <div className="ml-8 rounded-xl bg-primary/15 border border-primary/30 p-4 text-sm leading-relaxed text-foreground shadow-sm">
                <div className="flex items-center gap-2 mb-2">
                  <Loader className="h-4 w-4 animate-spin text-primary" />
                  <span className="font-medium">Generating your project...</span>
                </div>
                <p className="text-muted-foreground text-xs">This may take a few moments. Please wait while we build your project.</p>
              </div>
            </div>
          </div>

          {/* Chat Input Area - Enhanced */}
          <div className="px-5 py-4 border-t border-border/50 flex-shrink-0 bg-background backdrop-blur-sm">
            <div className="relative">
              <textarea
                disabled
                placeholder="Generation in progress... Please wait."
                className="w-full min-h-[90px] rounded-xl bg-secondary/40 border border-border/60 px-4 py-3 text-sm text-muted-foreground resize-none focus:outline-none disabled:cursor-not-allowed disabled:opacity-70 placeholder:text-muted-foreground/60"
                rows={3}
              />
              <div className="absolute bottom-3 right-3 flex items-center gap-1.5 text-xs text-muted-foreground/60">
                <Loader className="h-3 w-3 animate-spin" />
                <span>Processing...</span>
              </div>
            </div>
          </div>
        </aside>

        {/* Right: Generating Content - Fixed Layout */}
        <div className="flex-1 overflow-y-auto custom-scrollbar" style={{ background: 'linear-gradient(135deg, rgb(147, 197, 253) 0%, rgb(165, 243, 252) 50%, rgb(191, 219, 254) 100%)' }}>
          <div className="max-w-4xl mx-auto p-6 lg:p-8 pt-12 lg:pt-16">
              {/* Title - Centered */}
              <div className="mb-8 md:mb-12 text-center">
                <h1 className="text-3xl sm:text-4xl md:text-5xl font-bold text-slate-800 dark:text-slate-900">Generating Your Project</h1>
              </div>

              {/* Stepper - Equal Spacing */}
              <div className="mb-8 md:mb-12">
                <div className="flex flex-col sm:flex-row sm:items-center items-start sm:justify-center gap-8 sm:gap-12">
                  {steps.map((step, index) => (
                    <div key={step.number} className="flex items-center">
                      <div className="flex flex-col items-center">
                        <div
                          className={`flex h-12 w-12 items-center justify-center rounded-full font-semibold transition-all ${step.number < currentStep
                            ? 'bg-gradient-to-r from-blue-500 to-cyan-500 text-white'
                            : step.number === currentStep
                              ? 'bg-gradient-to-r from-blue-500 to-cyan-500 text-white'
                              : 'bg-slate-200/80 text-slate-500'
                            }`}
                        >
                          {step.number < currentStep ? (
                            <Check className="h-6 w-6" />
                          ) : step.number === currentStep ? (
                            <Loader className="h-6 w-6 animate-spin" />
                          ) : (
                            step.number
                          )}
                        </div>
                        <p className={`mt-3 text-sm font-medium text-center ${step.number <= currentStep ? 'text-slate-800 dark:text-slate-900' : 'text-slate-500'
                          }`}>
                          {step.label}
                        </p>
                      </div>
                      {index < steps.length - 1 && (
                        <div
                          className={`hidden sm:block w-16 h-1 mx-4 transition-all ${step.number < currentStep ? 'bg-gradient-to-r from-blue-500 to-cyan-500' : 'bg-slate-200/80'
                            }`}
                        ></div>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Logs Panel - Centered */}
              <div className="mb-8 max-w-3xl mx-auto">
                <div className="rounded-xl bg-background backdrop-blur-md border-b border-border shadow-lg overflow-hidden">
                  <div className="bg-background px-4 py-3 border-b border-border">
                    <p className="text-xs sm:text-sm font-medium text-foreground text-center">Generation Log</p>
                  </div>
                  <div className="bg-background/60 p-3 sm:p-4 h-56 sm:h-64 overflow-y-auto font-mono text-xs sm:text-sm space-y-1 custom-scrollbar">
                    {logs.map((log, index) => (
                      <div key={index} className="text-green-400">
                        {log}
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Progress Bar - Centered */}
              <div className="space-y-2 max-w-2xl mx-auto">
                <div className="flex justify-between text-xs text-slate-700 dark:text-slate-800">
                  <span>Progress</span>
                  <span>{Math.min(Math.round(progress), 100)}%</span>
                </div>
                <div className="w-full h-2 rounded-full bg-slate-200/80 overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-blue-500 to-cyan-500 transition-all duration-500"
                    style={{ width: `${Math.min(progress, 100)}%` }}
                  ></div>
                </div>
              </div>
          </div>
        </div>
      </main>
    </div>
  )
}
