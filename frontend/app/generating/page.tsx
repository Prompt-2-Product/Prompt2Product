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
    <div className="h-screen text-foreground relative overflow-hidden page-transition">
      {/* Cinematic Background Layer */}
      <div className="mesh-gradient" />
      <div className="technical-grid" />
      
      <Navigation />

      <main className="absolute inset-x-0 top-16 bottom-0 flex">
        {/* Cinematic Sidebar - Glass Panel */}
        <aside 
          className={`h-full transition-all duration-500 ease-in-out relative border-r border-white/5 ${
            isSidebarCollapsed ? 'w-0' : 'w-full lg:w-[360px]'
          }`}
        >
          <div className={`h-full flex flex-col glass-panel bg-background/20 backdrop-blur-2xl transition-opacity duration-300 ${isSidebarCollapsed ? 'opacity-0 pointer-events-none' : 'opacity-100'}`}>
            {/* Sidebar Header */}
            <div className="px-6 py-6 border-b border-white/5 shrink-0">
              <h2 className="text-sm font-bold uppercase tracking-widest text-foreground mb-3">Project Chat</h2>
              {projectInfo && (
                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-primary/20 text-primary border border-primary/20 uppercase tracking-tighter">
                    {projectInfo.language}
                  </span>
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-secondary/50 text-muted-foreground border border-border/50 uppercase tracking-tighter">
                    {projectInfo.appType}
                  </span>
                </div>
              )}
            </div>

            {/* Chat Body - Glass Bubbles */}
            <div className="flex-1 overflow-y-auto px-6 py-6 space-y-6 custom-scrollbar">
              {projectInfo && (
                <div className="flex flex-col gap-3">
                  <div className="flex items-center gap-2">
                    <div className="h-6 w-6 rounded-full bg-primary/20 flex items-center justify-center border border-primary/30">
                      <span className="text-[10px] font-bold text-primary">U</span>
                    </div>
                    <span className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">You</span>
                  </div>
                  <div className="ml-8 rounded-2xl glass-panel bg-white/5 p-4 text-sm text-foreground/90 leading-relaxed font-light shadow-sm">
                    {projectInfo.description}
                  </div>
                </div>
              )}

              <div className="flex flex-col gap-3">
                <div className="flex items-center gap-2">
                  <div className="h-6 w-6 rounded-full bg-primary flex items-center justify-center shadow-lg shadow-primary/20">
                    <span className="text-[10px] font-bold text-white">P</span>
                  </div>
                  <span className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">Prompt2Product</span>
                </div>
                <div className={`ml-8 rounded-2xl glass-panel p-4 text-sm font-light leading-relaxed shadow-lg ${
                  status === 'failed' ? 'bg-red-500/10 border-red-500/30 text-red-200' : 'bg-primary/5 border-primary/20 text-foreground'
                }`}>
                  {status === 'failed' ? (
                    <div className="space-y-3">
                      <div className="flex items-center gap-2 font-bold text-red-400">
                        <X className="h-4 w-4" />
                        <span className="uppercase tracking-tighter">Generation Failed</span>
                      </div>
                      <p className="text-xs opacity-80">{error || 'Unexpected error detected.'}</p>
                      <button 
                        onClick={() => router.push('/describe')}
                        className="w-full py-2 bg-red-500/20 hover:bg-red-500/30 border border-red-500/40 text-red-200 rounded-lg text-xs font-bold transition-all"
                      >
                        RESTART FORGE
                      </button>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      <div className="flex items-center gap-3">
                        {status === 'success' ? (
                          <div className="h-4 w-4 rounded-full bg-green-500 flex items-center justify-center">
                            <Check className="h-2.5 w-2.5 text-white" />
                          </div>
                        ) : (
                          <Loader className="h-4 w-4 animate-spin text-primary" />
                        )}
                        <span className="font-bold tracking-tight">
                          {status === 'success'
                            ? (isModificationFlow ? 'MODIFICATION COMPLETE' : 'BUILD SUCCESSFUL')
                            : (isModificationFlow ? 'APPLYING PATCHES...' : 'IGNITING THE CORE...')}
                        </span>
                      </div>
                      <p className="text-xs text-muted-foreground">
                        {status === 'pending'
                          ? 'Waiting for initialization...'
                          : (isModificationFlow
                            ? 'Applying logic changes and regenerating project structure.'
                            : 'This may take a minute. Our AI is currently sculpting your codebase.')}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Sidebar Footer */}
            <div className="px-6 py-4 border-t border-white/5 bg-background/20 backdrop-blur-3xl">
              <textarea
                disabled
                placeholder={status === 'failed' ? "Core extinguished." : "System processing..."}
                className="w-full min-h-[90px] rounded-xl bg-black/20 border border-white/5 px-4 py-3 text-sm text-muted-foreground font-light resize-none focus:outline-none disabled:cursor-not-allowed opacity-50 italic"
                rows={3}
              />
            </div>
          </div>

          {/* New Fold Button - Border Bar Placement */}
          <button
            onClick={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
            className={`absolute z-50 transition-all duration-500 ease-in-out hover:scale-110 flex items-center justify-center rounded-full bg-primary border border-primary/40 shadow-xl group ${
              isSidebarCollapsed 
                ? 'left-8 top-1/2 -translate-y-1/2 w-10 h-10' 
                : '-right-4 top-1/2 -translate-y-1/2 w-8 h-18'
            }`}
            title={isSidebarCollapsed ? "Show Chat" : "Hide Chat"}
          >
            {isSidebarCollapsed ? (
              <ChevronRight className="h-5 w-5 text-white group-hover:translate-x-0.5 transition-transform" />
            ) : (
              <ChevronLeft className="h-5 w-5 text-white group-hover:-translate-x-0.5 transition-transform" />
            )}
          </button>
        </aside>

        {/* Main Production Area */}
        <div className="flex-1 h-full overflow-hidden relative">
          <div className="max-w-4xl mx-auto px-6 pt-10 lg:pt-16 pb-32 lg:pb-48 flex flex-col h-full justify-between items-stretch relative z-10">
            {/* Cinematic Header */}
            <div className="shrink-0 text-center animate-in fade-in slide-in-from-top-4 duration-1000 relative z-20">
              <h1 className="text-4xl sm:text-5xl md:text-6xl font-black mb-4 tracking-tighter text-white">
                {status === 'failed'
                  ? (isModificationFlow ? <>Core <span className="text-red-500">Error</span></> : <>Forge <span className="text-red-500">Failed</span></>)
                  : (isModificationFlow ? <>Applying Your <span className="hero-text-accent">Changes</span></> : <>Generating Your <span className="hero-text-accent">Project</span></>)}
              </h1>
              <p className="text-sm sm:text-base text-muted-foreground font-light tracking-wide max-w-xl mx-auto">
                {status === 'failed' 
                  ? 'The engine encountered a critical error during construction.'
                  : 'Synthesizing components, establishing framework, and validating logic layers.'}
              </p>
            </div>

            {/* Cinematic Stepper */}
            {status !== 'failed' && (
              <div className="relative max-w-3xl mx-auto w-full py-2">
                <div className="flex flex-col sm:flex-row items-center justify-between gap-12 relative z-10">
                  {steps.map((step, index) => {
                    const isActive = step.number === currentStep
                    const isCompleted = step.number < currentStep
                    const isPending = step.number > currentStep

                    return (
                      <div key={step.number} className="flex flex-col items-center gap-5 group flex-1">
                        <div className="relative">
                          {/* Inner Circle */}
                          <div className={`h-14 w-14 rounded-full flex items-center justify-center transition-all duration-700 z-10 relative overflow-hidden ${
                            isCompleted 
                              ? 'bg-primary shadow-[0_0_20px_rgba(37,99,235,0.4)] border-primary' 
                              : isActive 
                                ? 'glass-panel bg-primary/20 border-primary shadow-[0_0_30px_rgba(37,99,235,0.2)]' 
                                : 'glass-panel bg-white/5 border-white/10'
                          }`}>
                            {isCompleted ? (
                              <Check className="h-6 w-6 text-white" />
                            ) : isActive ? (
                              <Loader className="h-6 w-6 animate-spin text-primary" />
                            ) : (
                              <span className="text-sm font-bold opacity-30">{step.number}</span>
                            )}
                          </div>
                          {/* Outer Glow Ring for Active */}
                          {isActive && (
                            <div className="absolute inset-0 -m-2 rounded-full border border-primary/20 animate-ping opacity-20" />
                          )}
                        </div>
                        <div className="text-center">
                          <p className={`text-[10px] sm:text-xs font-bold uppercase tracking-widest transition-colors duration-500 ${
                            isPending ? 'text-muted-foreground/30' : isActive ? 'text-primary' : 'text-foreground'
                          }`}>
                            {step.label}
                          </p>
                        </div>
                        {/* Stepper connecting lines removed as per user request */}
                      </div>
                    )
                  })}
                </div>
              </div>
            )}

            {/* Error State - Cinematic Panel */}
            {status === 'failed' && (
              <div className="max-w-2xl mx-auto mb-16 rounded-3xl glass-panel p-10 text-center relative overflow-hidden group">
                <div className="absolute -top-12 -right-12 h-40 w-40 bg-red-500/10 rounded-full blur-3xl" />
                <div className="h-20 w-20 bg-red-500/20 rounded-2xl flex items-center justify-center mx-auto mb-8 border border-red-500/30">
                  <X className="h-10 w-10 text-red-500" />
                </div>
                <h3 className="text-2xl font-black mb-4 tracking-tight">SYNTHESIS INTERRUPTED</h3>
                <p className="text-muted-foreground text-sm font-light leading-relaxed mb-8 max-w-md mx-auto">
                  The LLM construction engine timed out or reached a dead-end. This can happen with very complex prompts or unstable API tunnels.
                </p>
                <div className="flex flex-col sm:flex-row justify-center gap-4">
                  <button 
                    onClick={() => router.push('/describe')}
                    className="px-8 py-3 bg-primary text-white font-bold rounded-xl hover:bg-primary/90 transition-all shadow-xl shadow-primary/20"
                  >
                    MODIFY PLAN
                  </button>
                  <button 
                    onClick={() => window.location.reload()}
                    className="px-8 py-3 glass-panel bg-white/5 text-white font-bold rounded-xl hover:bg-white/10 transition-all"
                  >
                    RE-IGNITE CORE
                  </button>
                </div>
              </div>
            )}

            {/* Bottom Dashboard: Feed + Progress */}
            <div className="shrink-0 space-y-6 lg:space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-1000 delay-500">
              {/* Production Log - THE HUB */}
              <div className="max-w-2xl mx-auto w-full">
                <div className="rounded-3xl glass-panel overflow-hidden bg-background/30 backdrop-blur-3xl shadow-3xl">
                  <div className="bg-white/5 px-6 py-4 border-b border-white/5 flex justify-between items-center">
                    <div className="flex items-center gap-3">
                      <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
                      <p className="text-[10px] font-black uppercase tracking-widest text-muted-foreground">REALTIME PRODUCTION FEED</p>
                    </div>
                    {status === 'failed' && <span className="text-[10px] bg-red-500/20 text-red-500 px-2 py-0.5 rounded font-black uppercase tracking-wider">CRITICAL_ERROR</span>}
                  </div>
                  <div className="p-6 h-48 sm:h-56 lg:h-64 overflow-y-auto font-mono text-[11px] sm:text-xs space-y-2 custom-scrollbar-dark scroll-smooth">
                    {logs.map((log, index) => (
                      <div key={index} className={`opacity-0 animate-in fade-in duration-500 fill-mode-forwards ${log.includes('[ERROR]') || log.includes('[fatal]') ? 'text-red-400' : 'text-primary/80'}`}>
                        <span className="opacity-30 mr-3">[{new Date().toLocaleTimeString([], {hour12: false})}]</span>
                        {log}
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Progress Visualization */}
              {status !== 'failed' && (
                <div className="max-w-xl mx-auto w-full space-y-3">
                  <div className="flex justify-between items-end">
                    <div className="text-left">
                      <p className="text-[10px] font-black uppercase tracking-widest text-muted-foreground mb-0.5">Total Integrity</p>
                      <p className="text-[11px] font-bold text-foreground/80">Synthesis in progress...</p>
                    </div>
                    <span className="text-xl font-black text-primary tracking-tighter">{Math.min(Math.round(progress), 100)}%</span>
                  </div>
                  <div className="h-1 w-full rounded-full bg-white/5 border border-white/5 overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-blue-600 via-blue-400 to-cyan-400 shadow-[0_0_20px_rgba(37,99,235,0.5)] transition-all duration-1000 ease-out"
                      style={{ width: `${Math.min(progress, 100)}%` }}
                    ></div>
                  </div>
                </div>
              )}
            </div>
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
