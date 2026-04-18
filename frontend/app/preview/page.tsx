
'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Navigation } from '@/components/navigation'
import { Button } from '@/components/ui/button'
import { Code2, Edit3, Download, Eye, Loader, X, ChevronLeft, ChevronRight, RotateCcw } from 'lucide-react'

interface ProjectInfo {
  description: string
  language: string
  appType: string
  additionalInstructions: string
  projectId?: number
  runId?: number
}

import { api } from '@/lib/api'
import { isFrontendOnly, seedDemoProjectInfoIfNeeded } from '@/lib/frontend-only'

export default function PreviewPage() {
  const router = useRouter()
  const [projectInfo, setProjectInfo] = useState<ProjectInfo | null>(null)
  const [showChat, setShowChat] = useState(false)
  const [isRegenerating, setIsRegenerating] = useState(false)
  const [changeMessage, setChangeMessage] = useState('')
  const [chatHistory, setChatHistory] = useState<Array<{ role: 'user' | 'system'; content: string }>>([])
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false)

  useEffect(() => {
    seedDemoProjectInfoIfNeeded()
    const stored = sessionStorage.getItem('projectInfo')
    if (stored) {
      setProjectInfo(JSON.parse(stored))
    }
  }, [])

  const handleChatSubmit = (message: string) => {
    if (message.trim()) {
      setChatHistory(prev => [...prev, { role: 'user', content: message }])
      setChangeMessage('')

      sessionStorage.setItem('changeRequest', message)
      sessionStorage.setItem('generationFlow', 'modify')
      setIsRegenerating(true)
      setTimeout(() => {
        router.push('/generating')
      }, 1000)
    }
  }

  const handleDownload = () => {
    if (projectInfo?.projectId && projectInfo?.runId) {
      if (isFrontendOnly) {
        window.alert('Download needs the backend. Remove NEXT_PUBLIC_FRONTEND_ONLY from frontend/.env.local to reconnect.')
        return
      }
      const url = api.projects.downloadUrl(projectInfo.projectId, projectInfo.runId)
      window.open(url, '_blank')
    } else {
      alert('Project information missing. Cannot download.')
    }
  }

  const handlePreview = () => {
    if (projectInfo?.runId) {
      if (isFrontendOnly) {
        window.alert('Live preview is served by the backend. Disable frontend-only mode to use it.')
        return
      }
      const port = 8010 + projectInfo.runId
      window.open(`http://127.0.0.1:${port}`, '_blank')
    }
  }

  const handleRequestChanges = () => {
    setShowChat(true)
  }

  if (!projectInfo) {
    return (
      <div className="page-cinematic-gradient min-h-screen text-foreground relative overflow-hidden">
        <div className="backdrop-vertical-cinematic" aria-hidden="true" />
        <div className="technical-grid technical-grid-on-cinematic" aria-hidden="true" />
        <Navigation />
        <main className="flex items-center justify-center min-h-[calc(100vh-4rem)] pt-16 pb-8 sm:pb-16">
          <div className="w-full px-6 sm:px-10 lg:px-16 xl:px-24 text-center">
            <p className="cinematic-on-canvas text-base font-medium">Loading…</p>
          </div>
        </main>
      </div>
    )
  }

  return (
    <div className="page-cinematic-gradient min-h-screen text-foreground relative overflow-hidden page-transition">
      <div className="backdrop-vertical-cinematic" aria-hidden="true" />
      <div className="technical-grid technical-grid-on-cinematic" aria-hidden="true" />
      <Navigation />

      <main className="absolute inset-x-0 top-16 bottom-0 flex">
        {/* Left: Chat Sidebar - Glass Panel */}
        {showChat && projectInfo && (
          <aside className={`h-full transition-all duration-500 ease-in-out relative border-r border-slate-200/80 dark:border-white/5 ${isSidebarCollapsed ? 'w-0' : 'w-full lg:w-[380px]'
            }`}>
            <div className={`h-full flex flex-col glass-panel glass-panel-cinematic backdrop-blur-2xl transition-opacity duration-300 ${isSidebarCollapsed ? 'opacity-0 pointer-events-none' : 'opacity-100'}`}>
              {!isSidebarCollapsed && (
                <>
                  {/* Chat Header */}
                  <div className="px-6 py-6 border-b border-slate-200/80 dark:border-white/5 shrink-0">
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <h2 className="text-sm font-bold uppercase tracking-widest text-foreground mb-3">Request Changes</h2>
                        <div className="flex items-center gap-2">
                          <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-primary/20 text-primary border border-primary/20 uppercase tracking-tighter">
                            {projectInfo.language}
                          </span>
                          <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-slate-200/80 text-foreground/85 dark:bg-black/30 dark:text-slate-200 border border-slate-300/80 dark:border-white/15 uppercase tracking-tighter">
                            {projectInfo.appType}
                          </span>
                        </div>
                      </div>
                      <div className="flex items-center gap-1">
                        <button
                          onClick={() => setIsSidebarCollapsed(true)}
                          className="p-1.5 hover:bg-secondary/50 rounded-lg transition-colors text-muted-foreground hover:text-foreground"
                          title="Collapse sidebar"
                        >
                          <ChevronLeft className="h-5 w-5" />
                        </button>
                        <button
                          onClick={() => setShowChat(false)}
                          className="p-1.5 hover:bg-secondary/50 rounded-lg transition-colors text-muted-foreground hover:text-foreground"
                          aria-label="Close chat"
                        >
                          <X className="h-5 w-5" />
                        </button>
                      </div>
                    </div>
                  </div>

                  {/* Chat Messages Area */}
                  <div className="flex-1 overflow-y-auto px-5 py-4 space-y-5 custom-scrollbar min-h-0">
                    {/* Original Project Description */}
                    <div className="flex flex-col gap-2.5">
                      <div className="flex items-center gap-2">
                        <div className="h-6 w-6 rounded-full bg-primary/20 flex items-center justify-center">
                          <span className="text-xs font-semibold text-primary">U</span>
                        </div>
                        <span className="text-xs font-medium text-foreground/75 dark:text-slate-300">You</span>
                      </div>
                      <div className="ml-8 rounded-xl bg-card/95 dark:bg-black/40 border border-border/80 dark:border-white/12 p-4 text-sm leading-relaxed text-foreground whitespace-pre-wrap break-words shadow-md">
                        {projectInfo.description}
                      </div>
                    </div>

                    {/* System Response */}
                    <div className="flex flex-col gap-2.5">
                      <div className="flex items-center gap-2">
                        <div className="h-6 w-6 rounded-full bg-gradient-to-r from-blue-500 to-cyan-500 flex items-center justify-center">
                          <span className="text-xs font-semibold text-white">P</span>
                        </div>
                        <span className="text-xs font-medium text-foreground/75 dark:text-slate-300">Prompt2Product</span>
                      </div>
                      <div className="ml-8 rounded-xl bg-primary/20 dark:bg-primary/15 border border-primary/35 dark:border-primary/40 p-4 text-sm leading-relaxed text-foreground shadow-md">
                        <p>How would you like to modify this project?</p>
                      </div>
                    </div>

                    {/* User's change request messages */}
                    {chatHistory.map((msg, index) => (
                      <div key={index} className="flex flex-col gap-2.5">
                        <div className="flex items-center gap-2">
                          <div className="h-6 w-6 rounded-full bg-primary/20 flex items-center justify-center">
                            <span className="text-xs font-semibold text-primary">U</span>
                          </div>
                          <span className="text-xs font-medium text-foreground/75 dark:text-slate-300">You</span>
                        </div>
                        <div className="ml-8 rounded-xl bg-card/95 dark:bg-black/40 border border-border/80 dark:border-white/12 p-4 text-sm leading-relaxed text-foreground whitespace-pre-wrap break-words shadow-md">
                          {msg.content}
                        </div>
                      </div>
                    ))}

                    {isRegenerating && (
                      <div className="flex flex-col gap-2.5">
                        <div className="flex items-center gap-2">
                          <div className="h-6 w-6 rounded-full bg-gradient-to-r from-blue-500 to-cyan-500 flex items-center justify-center">
                            <span className="text-xs font-semibold text-white">P</span>
                          </div>
                          <span className="text-xs font-medium text-foreground/75 dark:text-slate-300">Prompt2Product</span>
                        </div>
                        <div className="ml-8 rounded-xl bg-primary/20 dark:bg-primary/15 border border-primary/35 p-4 text-sm leading-relaxed text-foreground shadow-md">
                          <div className="flex items-center gap-2">
                            <Loader className="h-4 w-4 animate-spin text-primary" />
                            <span className="font-medium">Processing your request...</span>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Chat Input Area */}
                  <div className="px-5 py-4 border-t border-slate-200/80 dark:border-white/10 flex-shrink-0 bg-white/50 dark:bg-black/25 backdrop-blur-md">
                    <div className="flex gap-3">
                      <textarea
                        value={changeMessage}
                        onChange={(e) => setChangeMessage(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' && !e.shiftKey) {
                            e.preventDefault()
                            handleChatSubmit(changeMessage)
                          }
                        }}
                        placeholder="Describe the changes you want..."
                        disabled={isRegenerating}
                        className="flex-1 min-h-[90px] rounded-xl bg-secondary/50 dark:bg-black/35 border border-border/80 dark:border-white/12 px-4 py-3 text-sm text-foreground placeholder:text-muted-foreground resize-none focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent disabled:cursor-not-allowed disabled:opacity-70"
                        rows={3}
                      />
                      <div className="flex flex-col gap-2">
                        <Button
                          onClick={() => handleChatSubmit(changeMessage)}
                          disabled={!changeMessage.trim() || isRegenerating}
                          className="bg-gradient-to-r from-blue-500 via-blue-400 to-cyan-500 hover:from-blue-600 hover:via-blue-500 hover:to-cyan-600 text-white font-semibold shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 px-6 h-full"
                        >
                          {isRegenerating ? (
                            <Loader className="h-4 w-4 animate-spin" />
                          ) : (
                            'Send'
                          )}
                        </Button>
                      </div>
                    </div>
                  </div>
                </>
              )}
            </div>
          </aside>
        )}

        {/* Floating Expand Button for Preview Chat */}
        {showChat && isSidebarCollapsed && (
          <button
            onClick={() => setIsSidebarCollapsed(false)}
            className="fixed left-0 top-1/2 -translate-y-1/2 z-40 bg-card/95 dark:bg-black/55 border-y border-r border-border/70 dark:border-white/15 p-2 rounded-r-xl shadow-xl hover:bg-secondary/80 dark:hover:bg-black/70 transition-all group backdrop-blur-md"
            title="Expand chat"
          >
            <ChevronRight className="h-5 w-5 text-muted-foreground group-hover:text-foreground transition-colors" />
          </button>
        )}

        {/* Right: Main Content Area */}
        <div className="flex-1 h-full overflow-hidden relative">
          <div className="max-w-6xl mx-auto px-6 pt-8 lg:pt-12 pb-48 lg:pb-72 flex flex-col h-full justify-center items-stretch relative z-10 transition-all duration-500">
            {/* Cinematic Header */}
            <div className="shrink-0 text-center animate-in fade-in slide-in-from-top-4 duration-1000 relative z-20">
              <h1 className="cinematic-hero-title text-4xl sm:text-5xl md:text-6xl font-black mb-4 tracking-tighter text-foreground dark:text-white">
                Project <span className="hero-text-accent">Summary</span>
              </h1>
              <p className="cinematic-on-canvas text-sm sm:text-base font-light tracking-wide max-w-xl mx-auto">
                Review your generated project architecture and take next steps.
              </p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-8 md:mb-12 flex-1 min-h-0 py-8 lg:py-12">
              {/* Left: Project Info Card */}
              <div className="lg:col-span-2 flex h-full">
                <div className="rounded-3xl glass-panel glass-panel-cinematic-dense backdrop-blur-3xl shadow-3xl p-6 sm:p-8 md:p-10 w-full flex flex-col h-full overflow-hidden">
                  <h2 className="text-xl sm:text-2xl font-black mb-6 sm:mb-8 text-foreground dark:text-white tracking-tight flex items-center gap-3">
                    <div className="h-2 w-2 rounded-full bg-primary" />
                    GENERATED PROJECT
                  </h2>
                  <div className="space-y-4 sm:space-y-6 flex-grow">
                    <div>
                      <label className="text-xs sm:text-sm font-medium text-foreground/70 dark:text-slate-300 block mb-2">Project Description</label>
                      <p className="text-foreground text-sm sm:text-base leading-relaxed">{projectInfo.description}</p>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <div>
                        <label className="text-sm font-medium text-foreground/70 dark:text-slate-300 block mb-2">Language</label>
                        <p className="text-foreground font-medium">{projectInfo.language}</p>
                      </div>
                      <div>
                        <label className="text-sm font-medium text-foreground/70 dark:text-slate-300 block mb-2">Project Type</label>
                        <p className="text-foreground font-medium">{projectInfo.appType}</p>
                      </div>
                    </div>

                    {projectInfo.additionalInstructions && (
                      <div>
                        <label className="text-sm font-medium text-foreground/70 dark:text-slate-300 block mb-2">Additional Instructions</label>
                        <p className="text-foreground text-sm">{projectInfo.additionalInstructions}</p>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Right: Action Buttons */}
              <div className="flex h-full">
                <div className="rounded-3xl glass-panel glass-panel-cinematic-dense backdrop-blur-3xl shadow-3xl p-6 sm:p-8 md:p-10 w-full flex flex-col h-full">
                  <h3 className="text-xl sm:text-2xl font-black text-foreground dark:text-white mb-6 sm:mb-8 tracking-tight flex items-center gap-3">
                    <div className="h-2 w-2 rounded-full bg-cyan-400" />
                    ACTIONS
                  </h3>
                  <div className="space-y-4 flex-grow flex flex-col justify-start">
                    <Button
                      onClick={() => router.push('/ide')}
                      className="w-full bg-gradient-to-r from-blue-600 via-blue-500 to-cyan-600 hover:from-blue-700 hover:via-blue-600 hover:to-cyan-700 text-white font-bold shadow-[0_0_20px_rgba(37,99,235,0.3)] hover:shadow-[0_0_30px_rgba(37,99,235,0.5)] transition-all duration-500 h-14 group rounded-2xl"
                      size="lg"
                    >
                      <Code2 className="mr-3 h-5 w-5 group-hover:rotate-12 transition-transform" />
                      View Code (Advanced)
                    </Button>

                    <Button
                      onClick={handleRequestChanges}
                      variant="outline"
                      className="w-full border border-black/10 dark:border-white/12 bg-secondary/60 dark:bg-black/35 backdrop-blur-xl text-foreground dark:text-white hover:bg-secondary/90 dark:hover:bg-black/50 hover:border-blue-400/50 transition-all duration-500 h-14 font-bold shadow-md hover:shadow-lg group rounded-2xl"
                      size="lg"
                    >
                      <RotateCcw className="mr-3 h-5 w-5 group-hover:rotate-180 transition-transform duration-700 group-hover:text-blue-500" />
                      Request Changes
                    </Button>

                    <Button
                      onClick={handleDownload}
                      variant="outline"
                      className="w-full border border-black/10 dark:border-white/12 bg-secondary/60 dark:bg-black/35 backdrop-blur-xl text-foreground dark:text-white hover:bg-secondary/90 dark:hover:bg-black/50 hover:border-emerald-400/50 transition-all duration-500 h-14 font-bold shadow-md hover:shadow-lg group rounded-2xl"
                      size="lg"
                    >
                      <Download className="mr-3 h-5 w-5 group-hover:scale-110 transition-transform group-hover:text-emerald-500" />
                      Download Project
                    </Button>

                    <Button
                      onClick={handlePreview}
                      variant="outline"
                      className="w-full border border-black/10 dark:border-white/12 bg-secondary/60 dark:bg-black/35 backdrop-blur-xl text-foreground dark:text-white hover:bg-secondary/90 dark:hover:bg-black/50 hover:border-blue-400/50 transition-all duration-500 h-14 font-bold shadow-md hover:shadow-lg group rounded-2xl"
                      size="lg"
                    >
                      <Eye className="mr-3 h-5 w-5 group-hover:scale-110 transition-transform group-hover:text-blue-400" />
                      Preview Project
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
