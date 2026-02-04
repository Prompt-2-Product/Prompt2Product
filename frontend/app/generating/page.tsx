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
    '[INFO] Starting project generation...',
    '[INFO] Analyzing prompt: "Turn Natural Language Into Executable Code"',
    '[INFO] Extracting requirements and specifications',
    '[INFO] Building project skeleton',
  ])

  useEffect(() => {
    const stored = sessionStorage.getItem('projectInfo')
    if (!stored) return

    const { projectId, runId } = JSON.parse(stored)
    if (!projectId || !runId) return

    let intervalId: NodeJS.Timeout

    const poll = async () => {
      try {
        // Fetch Status
        const statusRes = await fetch(`http://127.0.0.1:8000/runs/${runId}`)
        if (statusRes.ok) {
          const run = await statusRes.json()
          if (run.status === 'success') {
            setProgress(100)
            setCurrentStep(3)
            setTimeout(() => router.push('/preview'), 1000)
            return
          } else if (run.status === 'failed') {
            // Handle failure
            alert('Generation failed. Check logs.')
            clearInterval(intervalId)
          }
        }

        // Fetch Logs
        const logsRes = await fetch(`http://127.0.0.1:8000/runs/${runId}/logs`)
        if (logsRes.ok) {
          const logEvents = await logsRes.json()
          const logStrings = logEvents.map((e: any) => `[${e.level}] ${e.message}`)
          setLogs(logStrings)

          // derive step from logs
          const lastLog = logEvents[logEvents.length - 1]
          if (lastLog) {
            if (lastLog.stage === 'spec') {
              setCurrentStep(1)
              setProgress(30)
            } else if (lastLog.stage === 'codegen') {
              setCurrentStep(2)
              setProgress(60)
            } else if (['sandbox', 'deps', 'run', 'repair'].includes(lastLog.stage)) {
              setCurrentStep(3)
              setProgress(90)
            }
          }
        }
      } catch (err) {
        console.error(err)
      }
    }

    intervalId = setInterval(poll, 2000)
    poll() // initial call

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
