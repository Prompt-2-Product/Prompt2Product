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

  useEffect(() => {
    const stored = sessionStorage.getItem('projectInfo')
    if (!stored) {
      // If no project info, redirect to describe page
      router.push('/describe')
      return
    }

    const { projectId, runId } = JSON.parse(stored)
    if (!projectId || !runId) {
      router.push('/describe')
      return
    }

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

      // Update progress and steps
      if (progressValue < 30) {
        progressValue += 5
        stepValue = 1
      } else if (progressValue < 60) {
        progressValue += 5
        stepValue = 2
      } else if (progressValue < 90) {
        progressValue += 5
        stepValue = 3
      } else if (progressValue < 100) {
        progressValue += 2
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

    // Start simulation
    const intervalId = setInterval(simulateProgress, 800)

    return () => clearInterval(intervalId)
  }, [router])

  const steps = [
    { number: 1, label: 'Understanding Prompt' },
    { number: 2, label: 'Generating Skeleton' },
    { number: 3, label: 'Validating' },
  ]

  return (
    <div className="min-h-screen bg-background text-foreground">
      <Navigation />

      <main className="pt-24 pb-20">
        <div className="mx-auto max-w-5xl px-6">
          {/* Title */}
          <div className="mb-8 md:mb-12 text-center">
            <h1 className="text-3xl md:text-4xl font-bold text-foreground">Generating Your Project</h1>
          </div>

          {/* Stepper */}
          <div className="mb-8 md:mb-12">
            <div className="flex flex-col sm:flex-row sm:items-center items-start sm:justify-between gap-4 sm:gap-0">
              {steps.map((step, index) => (
                <div key={step.number} className="flex flex-1 items-center">
                  <div className="flex flex-col items-center flex-1">
                    <div
                      className={`flex h-10 w-10 items-center justify-center rounded-full font-semibold transition-all ${step.number < currentStep
                        ? 'bg-primary text-primary-foreground'
                        : step.number === currentStep
                          ? 'bg-primary text-primary-foreground'
                          : 'bg-secondary text-muted-foreground'
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
                    <p className={`mt-2 text-sm font-medium ${step.number <= currentStep ? 'text-foreground' : 'text-muted-foreground'
                      }`}>
                      {step.label}
                    </p>
                  </div>
                  {index < steps.length - 1 && (
                    <div
                      className={`h-1 flex-1 mx-2 transition-all ${step.number < currentStep ? 'bg-primary' : 'bg-secondary'
                        }`}
                    ></div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Logs Panel */}
          <div className="mb-8">
            <div className="rounded-xl bg-card border border-border overflow-hidden">
              <div className="bg-secondary px-4 py-3 border-b border-border">
                <p className="text-xs sm:text-sm font-medium text-foreground">Generation Log</p>
              </div>
              <div className="bg-background p-3 sm:p-4 h-56 sm:h-64 overflow-y-auto font-mono text-xs sm:text-sm space-y-1">
                {logs.map((log, index) => (
                  <div key={index} className="text-green-400">
                    {log}
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Progress Bar */}
          <div className="space-y-2">
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>Progress</span>
              <span>{Math.min(Math.round(progress), 100)}%</span>
            </div>
            <div className="w-full h-2 rounded-full bg-secondary overflow-hidden">
              <div
                className="h-full bg-primary transition-all duration-500"
                style={{ width: `${Math.min(progress, 100)}%` }}
              ></div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
