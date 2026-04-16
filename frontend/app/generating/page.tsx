'use client'

import { useEffect, useRef, useState } from 'react'
import { useRouter } from 'next/navigation'
import { Navigation } from '@/components/navigation'
import { Check, Loader, ChevronLeft, ChevronRight } from 'lucide-react'
import { api } from '@/lib/api'

export default function GeneratingPage() {
  const router = useRouter()
  const hasInitializedRef = useRef(false)
  const [currentStep, setCurrentStep] = useState(1)
  const [progress, setProgress] = useState(0)
  const [status, setStatus] = useState<'pending' | 'running' | 'success' | 'failed'>('pending')
  const [error, setError] = useState<string | null>(null)
  const [logs, setLogs] = useState<string[]>([
    '[INFO] Initializing project generation...',
  ])
  const [projectInfo, setProjectInfo] = useState<{ description: string; language: string; appType: string } | null>(null)
  const [isModificationFlow, setIsModificationFlow] = useState(false)
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false)

  useEffect(() => {
    if (hasInitializedRef.current) return
    hasInitializedRef.current = true

    const stored = sessionStorage.getItem('projectInfo')
    if (!stored) {
      router.push('/describe')
      return
    }

    const { projectId, runId, description, language, appType } = JSON.parse(stored)
    const flowMode = sessionStorage.getItem('generationFlow')
    const changeRequest = (sessionStorage.getItem('changeRequest') || '').trim()
    const isModify = flowMode === 'modify' && changeRequest.length > 0
    setIsModificationFlow(isModify)
    console.log(`[GENERATING] Start polling for Project: ${projectId}, Run: ${runId}`)

    if (!projectId || !runId) {
      router.push('/describe')
      return
    }

    setProjectInfo({ description, language, appType })

    const startModificationIfNeeded = async (): Promise<boolean> => {
      if (!isModify) return true
      try {
        // Consume mode so page refresh does not retrigger modify.
        sessionStorage.removeItem('generationFlow')
        console.log(`[FRONTEND][MODIFY] Submitting modify request for run ${runId}`)
        setLogs(prev => [...prev, `[INFO] Submitting change request: ${changeRequest}`])
        await api.projects.modify(projectId, runId, changeRequest)
        setLogs(prev => [...prev, '[INFO] Change request accepted. Applying modifications...'])
        return true
      } catch (err) {
        console.error('[FRONTEND][MODIFY] Failed to submit change request', err)
        setStatus('failed')
        setError(err instanceof Error ? err.message : 'Failed to start modification flow')
        return false
      }
    }

    let intervalId: NodeJS.Timeout
    let retryCount = 0

    const poll = async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        
        // Fetch Status
        const statusRes = await fetch(`${apiUrl}/runs/${runId}`)
        if (statusRes.ok) {
          retryCount = 0 
          const run = await statusRes.json()
          setStatus(run.status)

          if (run.status === 'success') {
            if (isModify) {
              sessionStorage.removeItem('changeRequest')
              sessionStorage.removeItem('generationFlow')
            }
            setProgress(100)
            setCurrentStep(3)
            setTimeout(() => router.push('/preview'), 1500)
            clearInterval(intervalId)
            return
          } else if (run.status === 'failed') {
            setError('The generation process encountered an error.')
            clearInterval(intervalId)
            return
          }
        }

        // Fetch Logs
        const logsRes = await fetch(`${apiUrl}/runs/${runId}/logs`)
        if (logsRes.ok) {
          const logEvents = await logsRes.json()
          const logStrings = logEvents.map((e: any) => `[${e.level}] ${e.message}`)
          setLogs(logStrings)

          // Auto-detect failure from logs if status hasn't updated yet
          const fatalLog = logEvents.find((e: any) => e.level === 'ERROR' || e.stage === 'fatal')
          if (fatalLog) {
              setStatus('failed')
              setError(fatalLog.message)
              clearInterval(intervalId)
              return
          }

          // derive step from logs
          const lastLog = logEvents[logEvents.length - 1]
          if (lastLog) {
            if (lastLog.stage === 'enhance') {
              setProgress(10)
            } else if (lastLog.stage === 'spec') {
              setCurrentStep(1)
              setProgress(30)
            } else if (['codegen', 'enrich', 'validate'].includes(lastLog.stage)) {
              setCurrentStep(2)
              setProgress(60)
            } else if (['sandbox', 'deps', 'run', 'repair'].includes(lastLog.stage)) {
              setCurrentStep(3)
              setProgress(90)
            }
          }
        }
      } catch (err) {
        retryCount++
        console.error(`[GENERATING] Polling error (attempt ${retryCount}):`, err)
      }
    }

    startModificationIfNeeded().then((ok) => {
      if (!ok) return
      intervalId = setInterval(poll, 3000)
      poll()
    })

    return () => clearInterval(intervalId)
  }, [router])

  const steps = [
    { number: 1, label: 'Understanding Prompt' },
    { number: 2, label: 'Generating Skeleton' },
    { number: 3, label: 'Validating & Starting' },
  ]

  return (
    <div className="min-h-screen text-foreground relative overflow-hidden page-transition">
      <div
        className="pointer-events-none absolute inset-0 -z-10"
        aria-hidden="true"
        style={{
          background: 'linear-gradient(to bottom, rgb(0, 0, 0) 0%, rgb(0, 0, 139) 33.33%, rgb(135, 206, 250) 66.66%, rgb(255, 255, 255) 100%)',
        }}
      />
      <Navigation />

      <main className="absolute inset-x-0 top-[3.5rem] bottom-0 flex flex-col lg:flex-row">
        <aside className={`${isSidebarCollapsed ? 'w-0 lg:w-0 border-r-0' : 'w-full lg:w-[380px] border-r'} border-border/50 bg-background flex flex-col flex-shrink-0 h-full transition-all duration-300 relative overflow-visible`}>
          {!isSidebarCollapsed && (
            <>
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
                  <button
                    onClick={() => setIsSidebarCollapsed(true)}
                    className="p-1.5 hover:bg-secondary/50 rounded-lg transition-colors text-muted-foreground hover:text-foreground"
                    title="Collapse sidebar"
                  >
                    <ChevronLeft className="h-5 w-5" />
                  </button>
                </div>
              </div>

              <div className="flex-1 overflow-y-auto px-5 py-4 space-y-5 custom-scrollbar min-h-0">
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

            <div className="flex flex-col gap-2.5">
              <div className="flex items-center gap-2">
                <div className="h-6 w-6 rounded-full bg-gradient-to-r from-blue-500 to-cyan-500 flex items-center justify-center">
                  <span className="text-xs font-semibold text-white">P</span>
                </div>
                <span className="text-xs font-medium text-muted-foreground">Prompt2Product</span>
              </div>
              <div className={`ml-8 rounded-xl border p-4 text-sm leading-relaxed shadow-sm ${status === 'failed' ? 'bg-red-500/10 border-red-500/50 text-red-700' : 'bg-primary/15 border-primary/30 text-foreground'}`}>
                {status === 'failed' ? (
                  <>
                    <div className="flex items-center gap-2 mb-2 font-bold text-red-600">
                      <X className="h-4 w-4" />
                      <span>Generation Failed</span>
                    </div>
                    <p className="text-xs mb-3">{error || 'An unexpected error occurred during generation.'}</p>
                    <button 
                      onClick={() => router.push('/describe')}
                      className="px-3 py-1.5 bg-red-600 text-white rounded-lg text-xs font-semibold hover:bg-red-700 transition-colors"
                    >
                      Try Again
                    </button>
                  </>
                ) : (
                  <>
                    <div className="flex items-center gap-2 mb-2 text-foreground">
                      {status === 'success' ? <Check className="h-4 w-4 text-green-500" /> : <Loader className="h-4 w-4 animate-spin text-primary" />}
                    <span className="font-medium">
                      {status === 'success'
                        ? (isModificationFlow ? 'Modification Complete!' : 'Generation Complete!')
                        : (isModificationFlow ? 'Applying your requested changes...' : 'Generating your project...')}
                    </span>
                    </div>
                    <p className="text-muted-foreground text-xs">
                      {status === 'pending'
                        ? 'Initializing...'
                        : (isModificationFlow
                          ? 'Applying patch, validating, and restarting preview.'
                          : 'This may take a few moments. Please wait while we build your project.')}
                    </p>
                  </>
                )}
              </div>
            </div>
          </div>

          <div className="px-5 py-4 border-t border-border/50 flex-shrink-0 bg-background backdrop-blur-sm">
            <div className="relative">
              <textarea
                disabled
                placeholder={status === 'failed' ? "Generation failed." : "Generation in progress..."}
                className="w-full min-h-[90px] rounded-xl bg-secondary/40 border border-border/60 px-4 py-3 text-sm text-muted-foreground resize-none focus:outline-none disabled:cursor-not-allowed disabled:opacity-70 placeholder:text-muted-foreground/60"
                rows={3}
              />
            </div>
          </div>
        </>
      )}
    </aside>

        {/* Floating Expand Button */}
        {isSidebarCollapsed && (
          <button
            onClick={() => setIsSidebarCollapsed(false)}
            className="fixed left-0 top-1/2 -translate-y-1/2 z-40 bg-background border-y border-r border-border/50 p-2 rounded-r-xl shadow-xl hover:bg-secondary/50 transition-all group"
            title="Expand sidebar"
          >
            <ChevronRight className="h-5 w-5 text-muted-foreground group-hover:text-foreground transition-colors" />
          </button>
        )}

        <div className="flex-1 overflow-y-auto custom-scrollbar" style={{ background: 'linear-gradient(to bottom, rgb(0, 0, 0) 0%, rgb(0, 0, 139) 33.33%, rgb(135, 206, 250) 66.66%, rgb(255, 255, 255) 100%)' }}>
          <div className="max-w-4xl mx-auto p-6 lg:p-8 pt-12 lg:pt-16">
            <div className="mb-8 md:mb-12 text-center text-white">
                <h1 className="text-3xl sm:text-4xl md:text-5xl font-bold">
                {status === 'failed'
                  ? (isModificationFlow ? 'Modification Error' : 'Generation Error')
                  : (isModificationFlow ? 'Applying Your Changes' : 'Generating Your Project')}
              </h1>
            </div>

            {status === 'failed' ? (
              <div className="max-w-2xl mx-auto mb-12 p-6 rounded-2xl bg-white/10 backdrop-blur-xl border border-red-500/30 text-center">
                <div className="h-16 w-16 bg-red-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                  <X className="h-8 w-8 text-red-500" />
                </div>
                <h3 className="text-xl font-bold text-white mb-2">Something went wrong</h3>
                <p className="text-slate-200 text-sm mb-6 leading-relaxed">
                  The LLM failed to respond. This is often caused by an unstable connection to Ollama (SSH tunnel timeout) or the model taking too long to generate.
                </p>
                <div className="flex justify-center gap-4">
                  <button 
                    onClick={() => router.push('/describe')}
                    className="px-6 py-2.5 bg-blue-600 text-white rounded-xl font-semibold hover:bg-blue-700 transition-all shadow-lg shadow-blue-500/25"
                  >
                    Modify Prompt
                  </button>
                  <button 
                    onClick={() => window.location.reload()}
                    className="px-6 py-2.5 bg-white/10 text-white border border-white/20 rounded-xl font-semibold hover:bg-white/20 transition-all"
                  >
                    Retry Connection
                  </button>
                </div>
              </div>
            ) : (
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
                        <p className={`mt-3 text-sm font-medium text-center ${step.number <= currentStep ? 'text-white' : 'text-slate-400'}`}>
                          {step.label}
                        </p>
                      </div>
                      {index < steps.length - 1 && (
                        <div
                          className={`hidden sm:block w-16 h-1 mx-4 transition-all ${step.number < currentStep ? 'bg-gradient-to-r from-blue-500 to-cyan-500' : 'bg-slate-200/80'}`}
                        ></div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="mb-8 max-w-3xl mx-auto">
              <div className="rounded-xl bg-background backdrop-blur-md border border-border shadow-lg overflow-hidden">
                <div className="bg-background px-4 py-3 border-b border-border flex justify-between items-center">
                  <p className="text-xs sm:text-sm font-medium text-foreground">Generation Log</p>
                  {status === 'failed' && <span className="text-[10px] bg-red-500/20 text-red-500 px-2 py-0.5 rounded font-bold uppercase tracking-wider">Failed</span>}
                </div>
                <div className="bg-background/60 p-3 sm:p-4 h-56 sm:h-64 overflow-y-auto font-mono text-xs sm:text-sm space-y-1 custom-scrollbar">
                  {logs.map((log, index) => (
                    <div key={index} className={log.includes('[ERROR]') || log.includes('[fatal]') ? 'text-red-400' : 'text-green-400'}>
                      {log}
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {status !== 'failed' && (
              <div className="space-y-2 max-w-2xl mx-auto">
                <div className="flex justify-between text-xs text-white">
                  <span>Progress</span>
                  <span>{Math.min(Math.round(progress), 100)}%</span>
                </div>
                <div className="w-full h-2 rounded-full bg-white/10 overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-blue-500 to-cyan-500 transition-all duration-500"
                    style={{ width: `${Math.min(progress, 100)}%` }}
                  ></div>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}

function X(props: any) {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M18 6 6 18" />
      <path d="m6 6 12 12" />
    </svg>
  )
}
