'use client'

import { useEffect, useRef, useState } from 'react'
import { useRouter } from 'next/navigation'
import { Navigation } from '@/components/navigation'
import { Check, Loader, ChevronLeft, ChevronRight, CornerDownRight, History, MessageSquare, X } from 'lucide-react'
import { api } from '@/lib/api'
import { HistoryView } from '@/components/history-view'

interface ProjectInfo {
  language: string
  appType: string
  description: string
}

export default function GeneratingPage() {
  const router = useRouter()
  const [status, setStatus] = useState<'pending' | 'running' | 'success' | 'failed'>('pending')
  const [progress, setProgress] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const [logs, setLogs] = useState<string[]>([
    '[INFO] Initializing project generation...',
  ])
  const [projectInfo, setProjectInfo] = useState<ProjectInfo | null>(null)
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false)
  const [currentStep, setCurrentStep] = useState(1)
  const [isModificationFlow, setIsModificationFlow] = useState(false)
  const [activeTab, setActiveTab] = useState<'chat' | 'history'>('chat')

  const flattenFiles = (nodes: any[]): any[] =>
    nodes.flatMap((n: any) => n.type === 'folder' ? flattenFiles(n.children || []) : [n])

  const handleSelectHistoryProject = async (projectId: number) => {
    try {
      const runData = await api.projects.getLatestRun(projectId)
      const runId = runData.run_id

      let language = 'Python'
      let appType = 'Web App'
      try {
        const files = await api.projects.listFiles(projectId, runId)
        const names = flattenFiles(files).map((f: any) => f.name as string)
        if (names.some((n: string) => n.endsWith('.ts') || n.endsWith('.tsx'))) language = 'TypeScript'
        else if (names.some((n: string) => n.endsWith('.js') || n.endsWith('.jsx'))) language = 'JavaScript'
      } catch (e) {}

      let description = `Project #${projectId}`
      try {
        const fileData = await api.projects.getFile(projectId, runId, 'pipeline_output.json')
        if (fileData?.content && typeof fileData.content === 'string') {
          const meta = JSON.parse(fileData.content)
          if (meta?.user_prompt) description = meta.user_prompt
        }
      } catch (e) {}

      sessionStorage.setItem('projectInfo', JSON.stringify({ projectId, runId, description, language, appType, additionalInstructions: '' }))
      router.push('/ide')
    } catch (err) {
      console.error('Failed to open historical project:', err)
    }
  }

  useEffect(() => {
    // 1. Get Project Info
    const stored = sessionStorage.getItem('projectInfo')
    if (!stored) {
      router.push('/describe')
      return
    }
    const info = JSON.parse(stored)
    setProjectInfo(info)

    // Check if we are in modification flow
    const flowMode = sessionStorage.getItem('generationFlow')
    const changeRequest = (sessionStorage.getItem('changeRequest') || '').trim()
    const isModify = flowMode === 'modify' && changeRequest.length > 0
    setIsModificationFlow(isModify)

    // 2. Start Generation Process
    const startGeneration = async () => {
      setStatus('running')
      try {
        if (isModify) {
          setLogs(prev => [...prev, '[INFO] Change request accepted. Applying modifications...'])
          await api.submitChangeRequest(changeRequest, (log) => {
            setLogs(prev => [...prev, log])
          })
        } else {
          await api.generateProject(info, (log) => {
            setLogs(prev => [...prev, log])
            
            // Sniff for port number in logs
            const portMatch = log.match(/port\s+(\d+)/i) || log.match(/localhost:(\d+)/i)
            if (portMatch && portMatch[1]) {
              const port = portMatch[1]
              const currentInfo = JSON.parse(sessionStorage.getItem('projectInfo') || '{}')
              sessionStorage.setItem('projectInfo', JSON.stringify({ ...currentInfo, previewPort: port }))
            }
          })
        }
        
        setStatus('success')
        setProgress(100)
        
        // Finalize
        if (isModify) {
          sessionStorage.removeItem('changeRequest')
          sessionStorage.removeItem('generationFlow')
        }
        
        // Short delay before redirecting to preview
        setTimeout(() => router.push('/preview'), 1500)
        
      } catch (err) {
        console.error('[FRONTEND] Generation failed:', err)
        setStatus('failed')
        setError(err instanceof Error ? err.message : 'An unexpected error occurred.')
      }
    }

    startGeneration()

    // 3. Simulated progress if status is running
    const progressInterval = setInterval(() => {
      setProgress(prev => {
        if (prev < 90) return prev + Math.random() * 2
        return prev
      })
    }, 2000)

    return () => clearInterval(progressInterval)
  }, [router, isModificationFlow])

  // Map progress to steps
  useEffect(() => {
    if (progress < 30) setCurrentStep(1)
    else if (progress < 70) setCurrentStep(2)
    else setCurrentStep(3)
  }, [progress])

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
              <div className="flex items-center gap-4 mb-4">
                <button 
                  onClick={() => setActiveTab('chat')}
                  className={`flex items-center gap-2 pb-2 transition-all relative ${
                    activeTab === 'chat' ? 'text-primary' : 'text-muted-foreground hover:text-foreground'
                  }`}
                >
                  <MessageSquare className="h-4 w-4" />
                  <span className="text-xs font-bold uppercase tracking-widest">Active Chat</span>
                  {activeTab === 'chat' && <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary rounded-full" />}
                </button>
                <button 
                  onClick={() => setActiveTab('history')}
                  className={`flex items-center gap-2 pb-2 transition-all relative ${
                    activeTab === 'history' ? 'text-primary' : 'text-muted-foreground hover:text-foreground'
                  }`}
                >
                  <History className="h-4 w-4" />
                  <span className="text-xs font-bold uppercase tracking-widest">History</span>
                  {activeTab === 'history' && <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary rounded-full" />}
                </button>
              </div>

              {activeTab === 'chat' && projectInfo && (
                <div className="flex items-center gap-2 animate-in fade-in slide-in-from-left-2 duration-300">
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-primary/20 text-primary border border-primary/20 uppercase tracking-tighter">
                    {projectInfo.language}
                  </span>
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-secondary/50 text-muted-foreground border border-border/50 uppercase tracking-tighter">
                    {projectInfo.appType}
                  </span>
                </div>
              )}
            </div>

            {/* Content Area */}
            <div className="flex-1 overflow-y-auto px-6 py-6 space-y-6 custom-scrollbar relative">
              {activeTab === 'history' ? (
                <HistoryView onSelectProject={handleSelectHistoryProject} />
              ) : (
                <>
                  {projectInfo && (
                    <div className="flex flex-col gap-3">
                      <div className="flex items-center gap-2">
                        <div className="h-6 w-6 rounded-full bg-primary/20 flex items-center justify-center border border-primary/30">
                          <span className="text-[10px] font-bold text-primary">U</span>
                        </div>
                        <span className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">You</span>
                      </div>
                      <div className="flex gap-3">
                        <CornerDownRight className="h-4 w-4 mt-1 text-muted-foreground/40 shrink-0" />
                        <div className="flex-1 rounded-2xl glass-panel bg-white/5 p-4 text-sm text-foreground/90 leading-relaxed font-light shadow-sm">
                          {projectInfo.description}
                        </div>
                      </div>
                    </div>
                  )}

                  <div className="flex flex-col gap-3">
                    <div className="flex items-center gap-2">
                        <div className="h-4 w-4 rounded-full bg-primary flex items-center justify-center ring-2 ring-primary/20">
                          <span className="text-[10px] font-bold text-primary-foreground">P</span>
                        </div>
                      <span className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">Prompt2Product</span>
                    </div>
                    <div className="flex gap-3">
                      <CornerDownRight className="h-4 w-4 mt-1 text-muted-foreground/40 shrink-0" />
                      <div className={`flex-1 rounded-2xl glass-panel p-4 text-sm font-light leading-relaxed shadow-lg ${
                        status === 'failed' ? 'bg-red-500/10 border-red-500/20 text-red-600 dark:text-red-200' : 'bg-primary/5 border-primary/20 text-foreground'
                      }`}>
                        {status === 'failed' ? (
                          <div className="space-y-3">
                            <div className="flex items-center gap-2 font-bold text-red-600 dark:text-red-400">
                              <div className="h-5 w-5 rounded-full bg-red-500/20 flex items-center justify-center">
                                <X className="h-3 w-3" />
                              </div>
                              <span className="uppercase tracking-tighter text-xs">Generation Failed</span>
                            </div>
                            <p className="text-[11px] leading-snug opacity-90">{error || 'The engine encountered a critical logic error.'}</p>
                            <button 
                              onClick={() => router.push('/describe')}
                              className="w-full py-2 bg-red-500/10 hover:bg-red-500/20 border border-red-500/30 text-red-600 dark:text-red-200 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all"
                            >
                              RESTART FORGE
                            </button>
                          </div>
                        ) : (
                          <div className="space-y-3">
                            <div className="flex items-center gap-3">
                              {status === 'success' ? (
                                <div className="h-4 w-4 rounded-full bg-emerald-500/20 flex items-center justify-center">
                                  <Check className="h-2.5 w-2.5 text-emerald-500" />
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
                </>
              )}
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

          <button
            onClick={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
            className="absolute -right-3 top-1/2 -translate-y-1/2 h-10 w-6 bg-primary text-primary-foreground rounded-r-lg shadow-xl hover:bg-primary/90 transition-all z-50 flex items-center justify-center group border border-primary/20"
          >
            {isSidebarCollapsed ? (
              <ChevronRight className="h-4 w-4 text-primary-foreground group-hover:translate-x-0.5 transition-transform" />
            ) : (
              <ChevronLeft className="h-4 w-4 text-primary-foreground group-hover:-translate-x-0.5 transition-transform" />
            )}
          </button>
        </aside>

        <div className="flex-1 h-full overflow-hidden relative">
          <div className="max-w-[1440px] mx-auto px-6 lg:px-12 h-full flex flex-col justify-center gap-10 lg:gap-14 relative z-10 py-12 lg:py-16">
            <div className="flex flex-col items-center gap-10 md:gap-16 shrink-0">
              <div className="text-center animate-in fade-in slide-in-from-top-4 duration-1000 relative z-20 mt-2">
                <h1 className="text-3xl sm:text-4xl md:text-6xl font-black mb-3 tracking-tighter text-foreground dark:text-white uppercase">
                  {status === 'failed'
                    ? (isModificationFlow ? <>Core <span className="text-red-500">Error</span></> : <>Generation <span className="text-red-500">Failed</span></>)
                    : (isModificationFlow ? <>Applying <span className="hero-text-accent">Your Changes</span></> : <>Generating <span className="hero-text-accent">Your Project</span></>)}
                </h1>
                <p className="text-xs sm:text-sm text-muted-foreground font-light tracking-widest uppercase opacity-70">
                  {status === 'failed' 
                    ? 'The engine encountered a critical logic error.'
                    : 'Synthesizing components, establishing framework, and validating logic layers.'}
                </p>
              </div>

              {status !== 'failed' && (
                <div className="relative max-w-5xl mx-auto w-full py-2">
                <div className="grid grid-cols-1 sm:grid-cols-3 items-start gap-8 sm:gap-0 relative z-10">
                  {steps.map((step, index) => {
                    const isActive = step.number === currentStep
                    const isCompleted = step.number < currentStep
                    const isPending = step.number > currentStep

                    return (
                      <div key={step.number} className="flex flex-col items-center gap-5 group flex-1">
                        <div className="relative">
                          <div className={`h-14 w-14 rounded-full flex items-center justify-center transition-all duration-700 z-10 relative overflow-hidden ${
                            isCompleted 
                              ? 'bg-primary shadow-[0_0_20px_rgba(37,99,235,0.4)] border-primary' 
                              : isActive 
                                ? 'glass-panel bg-primary/20 border-primary shadow-[0_0_25px_rgba(37,99,235,0.2)]' 
                                : 'glass-panel bg-white/5 border-white/10'
                          }`}>
                            {isCompleted ? (
                              <Check className="h-6 w-6 text-primary-foreground" />
                            ) : isActive ? (
                              <Loader className="h-6 w-6 animate-spin text-primary" />
                            ) : (
                              <span className="text-xs font-black text-muted-foreground/50 tracking-tighter">{step.number}</span>
                            )}
                          </div>
                          {isActive && (
                            <div className="absolute inset-0 -m-3 rounded-full border border-primary/20 animate-ping opacity-20" />
                          )}
                        </div>
                        <div className="text-center">
                          <p className={`text-[10px] sm:text-xs font-bold uppercase tracking-widest transition-colors duration-500 ${
                            isPending ? 'text-muted-foreground/30' : isActive ? 'text-primary' : 'text-foreground'
                          }`}>
                            {step.label}
                          </p>
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>
              )}
            </div>

            {status === 'failed' && (
              <div className="flex flex-col sm:flex-row justify-center gap-3 relative z-30 mb-8 py-4">
                <button 
                  onClick={() => router.push('/describe')}
                  className="px-6 py-2 bg-red-500/20 text-red-600 dark:text-red-400 font-bold uppercase tracking-widest text-[10px] rounded-lg border border-red-500/30 hover:bg-red-500/30 transition-all"
                >
                  REPROMPT
                </button>
                <button 
                  onClick={() => window.location.reload()}
                  className="px-6 py-2 bg-secondary/50 dark:bg-white/5 text-foreground/70 dark:text-white/70 font-bold uppercase tracking-widest text-[10px] rounded-lg border border-border/50 hover:bg-secondary/70 dark:hover:bg-white/10 transition-all font-mono"
                >
                  RETRY_CONNECTION
                </button>
              </div>
            )}

            <div className="shrink-0 space-y-6 lg:space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-1000 delay-500">
              <div className="max-w-4xl mx-auto w-full">
                <div className="rounded-3xl glass-panel overflow-hidden bg-background/40 dark:bg-background/30 backdrop-blur-3xl shadow-2xl border border-black/10 dark:border-white/10">
                  <div className="bg-black/[0.03] dark:bg-white/5 px-6 py-4 border-b border-black/5 dark:border-white/5 flex justify-between items-center">
                    <div className="flex items-center gap-3">
                      <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse shadow-[0_0_8px_rgba(34,197,94,0.5)]" />
                      <p className="text-[10px] font-black uppercase tracking-widest text-muted-foreground/80">REALTIME PRODUCTION FEED</p>
                    </div>
                    {status === 'failed' && <span className="text-[10px] bg-red-500/20 text-red-600 dark:text-red-500 px-2 py-0.5 rounded font-black uppercase tracking-wider">CRITICAL_ERROR</span>}
                  </div>
                  <div className="p-6 h-48 sm:h-56 lg:h-64 overflow-y-auto font-mono text-sm leading-relaxed space-y-3 custom-scrollbar-dark scroll-smooth">
                    {logs.map((log, index) => {
                      const isError = log.includes('[ERROR]') || log.includes('[fatal]')
                      const isInfo = log.includes('[INFO]')
                      const isSuccess = log.includes('[SUCCESS]') || log.includes('successfully')
                      
                      return (
                        <div key={index} className="opacity-0 animate-in fade-in duration-500 fill-mode-forwards flex gap-3 text-foreground/90">
                          <span className="opacity-50 shrink-0 select-none">[{new Date().toLocaleTimeString([], {hour12: false})}]</span>
                          <div className="flex flex-wrap gap-x-2">
                             {isError && <span className="text-red-500 font-bold shrink-0">[ERROR]</span>}
                             {isInfo && <span className="text-blue-500 dark:text-blue-400 font-bold shrink-0">[INFO]</span>}
                             {isSuccess && <span className="text-emerald-500 font-bold shrink-0">[SUCCESS]</span>}
                             <span className="break-all">{log.replace(/\[(INFO|ERROR|SUCCESS|fatal|warn)\]/g, '').trim()}</span>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </div>
              </div>

              {status !== 'failed' && (
                <div className="max-w-3xl mx-auto w-full space-y-3">
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
