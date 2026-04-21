'use client'

import { useState, useEffect, Suspense } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { Navigation } from '@/components/navigation'
import { Button } from '@/components/ui/button'
import { Code2, Edit3, Download, Eye, Loader, X, ChevronLeft, ChevronRight, RotateCcw, Check, CornerDownRight, History, MessageSquare } from 'lucide-react'
import { HistoryView } from '@/components/history-view'
import { api } from '@/lib/api'

interface ProjectInfo {
  description: string
  language: string
  appType: string
  additionalInstructions: string
  projectId?: number
  runId?: number
  previewPort?: string
}

function PreviewContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [projectInfo, setProjectInfo] = useState<ProjectInfo | null>(null)
  const [showChat, setShowChat] = useState(true)
  const [isRegenerating, setIsRegenerating] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [changeMessage, setChangeMessage] = useState('')
  const [chatHistory, setChatHistory] = useState<Array<{ role: 'user' | 'system'; content: string }>>([])
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false)
  const [activeTab, setActiveTab] = useState<'chat' | 'history'>('chat')

  useEffect(() => {
    const fetchHistoricalProject = async (pid: string) => {
      setIsLoading(true)
      try {
        const projectId = parseInt(pid)
        // 1. Get latest run
        const runData = await api.projects.getLatestRun(projectId)
        const runId = runData.run_id

        // 2. Try to get pipeline_output.json for metadata
        try {
          const fileData = await api.projects.getFile(projectId, runId, 'pipeline_output.json')
          const metadata = typeof fileData.content === 'string' ? JSON.parse(fileData.content) : fileData
          
          const info: ProjectInfo = {
            projectId,
            runId,
            description: metadata.user_prompt || 'No description available',
            language: metadata.result?.language || 'Unknown',
            appType: metadata.result?.app_type || metadata.result?.type || 'App',
            additionalInstructions: '',
          }
          setProjectInfo(info)
          sessionStorage.setItem('projectInfo', JSON.stringify(info))
        } catch (e) {
          console.error("Failed to fetch full metadata, using fallback", e)
          setProjectInfo({
            projectId,
            runId,
            description: 'Historical Project #' + projectId,
            language: 'Unknown',
            appType: 'App',
            additionalInstructions: ''
          })
        }
      } catch (err) {
        console.error("Failed to load historical project:", err)
      } finally {
        setIsLoading(false)
      }
    }

    const projectId = searchParams.get('projectId')
    if (projectId) {
      fetchHistoricalProject(projectId)
    } else {
      const stored = sessionStorage.getItem('projectInfo')
      if (stored) {
        setProjectInfo(JSON.parse(stored))
      }
      setIsLoading(false)
    }
  }, [searchParams])

  // Helper: flatten nested file tree to get all file names
  const flattenFiles = (nodes: any[]): any[] => {
    return nodes.flatMap((n: any) => n.type === 'folder' ? flattenFiles(n.children || []) : [n])
  }

  const handleSelectHistoryProject = async (projectId: number) => {
    setIsLoading(true)
    try {
      // 1. Get latest run ID for this project
      const runData = await api.projects.getLatestRun(projectId)
      const runId = runData.run_id

      // 2. Detect language from actual files
      let language = 'Python'
      let appType = 'Web App'
      try {
        const files = await api.projects.listFiles(projectId, runId)
        const allFiles = flattenFiles(files).map((f: any) => f.name as string)
        if (allFiles.some((n: string) => n.endsWith('.ts') || n.endsWith('.tsx'))) {
          language = 'TypeScript'
        } else if (allFiles.some((n: string) => n.endsWith('.js') || n.endsWith('.jsx'))) {
          language = 'JavaScript'
        }
      } catch (e) { /* use Python default */ }

      // 3. Try to get user prompt from pipeline_output.json
      let description = `Project #${projectId}`
      try {
        const fileData = await api.projects.getFile(projectId, runId, 'pipeline_output.json')
        if (fileData?.content && typeof fileData.content === 'string') {
          const meta = JSON.parse(fileData.content)
          if (meta?.user_prompt) description = meta.user_prompt
        }
      } catch (e) { /* use fallback */ }

      // 4. Populate sessionStorage (same format as describe/page.tsx)
      const info = { projectId, runId, description, language, appType, additionalInstructions: '' }
      sessionStorage.setItem('projectInfo', JSON.stringify(info))

      // 5. Navigate to IDE to see all files
      router.push('/ide')
    } catch (err) {
      console.error('Failed to open historical project:', err)
      setIsLoading(false)
    }
  }

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
      const url = api.projects.downloadUrl(projectInfo.projectId, projectInfo.runId)
      window.open(url, '_blank')
    } else {
      alert('Project information missing. Cannot download.')
    }
  }

  const handlePreview = () => {
    if (projectInfo?.projectId && projectInfo?.runId) {
      // Use dynamic port if available, otherwise default to 8002
      const port = (projectInfo as any).previewPort || '8002'
      window.open(`http://34.180.63.91:${port}`, '_blank')
    }
  }

  return (
    <div className="h-screen text-foreground relative overflow-hidden page-transition">
      {/* Background Layers */}
      <div className="mesh-gradient" />
      <div className="technical-grid" />
      
      <Navigation />

      <main className="absolute inset-x-0 top-16 bottom-0 flex">
        {/* Left: Chat Sidebar - Glass Panel */}
        {showChat && (
          <aside 
            className={`h-full transition-all duration-500 ease-in-out relative border-r border-white/5 ${
              isSidebarCollapsed ? 'w-0' : 'w-full lg:w-[380px]'
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

                   {/* Status Indicator */}
                   <div className="flex flex-col gap-3">
                     <div className="flex items-center gap-2">
                       <div className="h-4 w-4 rounded-full bg-primary flex items-center justify-center ring-2 ring-primary/20">
                         <span className="text-[10px] font-bold text-primary-foreground">P</span>
                       </div>
                       <span className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">Prompt2Product</span>
                     </div>
                     <div className="flex gap-3">
                       <CornerDownRight className="h-4 w-4 mt-1 text-muted-foreground/40 shrink-0" />
                       <div className="flex-1 rounded-2xl glass-panel bg-primary/5 border border-primary/20 p-4 text-sm font-light leading-relaxed shadow-lg text-foreground">
                         <div className="space-y-3">
                           <div className="flex items-center gap-3">
                             <div className="h-4 w-4 rounded-full bg-emerald-500/20 flex items-center justify-center">
                               <Check className="h-2.5 w-2.5 text-emerald-500" />
                             </div>
                             <span className="font-bold tracking-tight">BUILD SUCCESSFUL</span>
                           </div>
                           <p className="text-xs text-muted-foreground leading-snug">
                             The application has been sculpted and validated. You can now preview, download, or request further modifications.
                           </p>
                         </div>
                       </div>
                     </div>
                   </div>

                   {/* Chat History for Modifications */}
                   {chatHistory.map((msg, index) => (
                     <div key={index} className="flex flex-col gap-3">
                       <div className="flex items-center gap-2">
                         <div className="h-6 w-6 rounded-full bg-primary/20 flex items-center justify-center border border-primary/30">
                           <span className="text-[10px] font-bold text-primary">U</span>
                         </div>
                         <span className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">You</span>
                       </div>
                       <div className="flex gap-3">
                         <CornerDownRight className="h-4 w-4 mt-1 text-muted-foreground/40 shrink-0" />
                         <div className="flex-1 rounded-2xl glass-panel bg-white/5 p-4 text-sm text-foreground/90 leading-relaxed font-light shadow-sm whitespace-pre-wrap break-words">
                           {msg.content}
                         </div>
                       </div>
                     </div>
                   ))}

                   {isRegenerating && (
                     <div className="flex flex-col gap-3">
                       <div className="flex items-center gap-2">
                         <div className="h-4 w-4 rounded-full bg-primary flex items-center justify-center ring-2 ring-primary/20">
                           <span className="text-[10px] font-bold text-primary-foreground">P</span>
                         </div>
                         <span className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">Prompt2Product</span>
                       </div>
                       <div className="flex gap-3">
                         <CornerDownRight className="h-4 w-4 mt-1 text-muted-foreground/40 shrink-0" />
                         <div className="flex-1 rounded-2xl glass-panel bg-primary/10 border border-primary/20 p-4 text-sm font-light leading-relaxed shadow-sm">
                           <div className="flex items-center gap-2">
                             <Loader className="h-4 w-4 animate-spin text-primary" />
                             <span className="font-medium text-xs">Awaiting re-generation...</span>
                           </div>
                         </div>
                       </div>
                     </div>
                   )}
                   </>
                 )}
               </div>

               {/* Chat Input Area */}
               <div className={`px-6 py-4 border-t border-white/5 bg-background/20 backdrop-blur-3xl shrink-0 transition-opacity duration-300 ${
                 activeTab === 'history' ? 'opacity-0 pointer-events-none grayscale' : 'opacity-100'
               }`}>
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
                   className="w-full min-h-[90px] rounded-xl bg-black/20 border border-white/5 px-4 py-3 text-sm text-foreground font-light resize-none focus:outline-none focus:ring-1 focus:ring-primary/50 disabled:cursor-not-allowed opacity-90 transition-all font-sans"
                   rows={3}
                 />
                 <div className="mt-3 flex justify-end">
                   <Button
                     onClick={() => handleChatSubmit(changeMessage)}
                     disabled={!changeMessage.trim() || isRegenerating}
                     size="sm"
                     className="bg-primary/10 hover:bg-primary/20 border border-primary/30 text-primary text-[10px] font-black uppercase tracking-widest px-4 py-1.5 h-auto transition-all"
                   >
                     SEND
                   </Button>
                 </div>
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
        )}

        {/* Right: Main Content Area */}
        <div className="flex-1 h-full overflow-y-auto relative custom-scrollbar-dark">
          {/* Loading overlay for history project switching */}
          {isLoading && (
            <div className="absolute inset-0 z-50 flex items-center justify-center bg-background/50 backdrop-blur-sm">
              <div className="flex flex-col items-center gap-4">
                <Loader className="h-8 w-8 animate-spin text-primary" />
                <p className="text-xs font-bold uppercase tracking-widest text-muted-foreground">Loading Project...</p>
              </div>
            </div>
          )}
          <div className="max-w-[1440px] mx-auto px-6 lg:px-12 py-12 lg:py-16 flex flex-col min-h-full justify-center gap-12 lg:gap-16 relative z-10">
            {/* Cinematic Header */}
            <div className="shrink-0 text-center animate-in fade-in slide-in-from-top-4 duration-1000 relative z-20">
              <h1 className="text-4xl sm:text-5xl md:text-6xl font-black mb-4 tracking-tighter text-foreground dark:text-white">
                Project <span className="hero-text-accent">Summary</span>
              </h1>
              <p className="max-w-xl mx-auto text-sm text-muted-foreground font-light tracking-widest uppercase opacity-70">
                Review your generated project architecture and take next steps.
              </p>
            </div>

            {/* Content Body */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-12 relative z-10">
              {/* Left Column: Details */}
              <div className="lg:col-span-7 group animate-in fade-in slide-in-from-left-4 duration-1000 delay-300">
                <div className="rounded-[40px] glass-panel p-10 sm:p-14 bg-white/5 border border-white/10 shadow-2xl relative overflow-hidden h-full flex flex-col justify-center">
                  <div className="flex items-center gap-3 mb-8">
                    <div className="h-2 w-2 rounded-full bg-primary" />
                    <h2 className="text-xl sm:text-2xl font-black tracking-tight uppercase">Generated Project</h2>
                  </div>

                  <div className="space-y-12">
                    <div>
                      <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-muted-foreground mb-3">User Prompt</p>
                      <p className="text-base sm:text-lg text-foreground/80 leading-relaxed font-light">
                        {projectInfo?.description}
                      </p>
                    </div>

                    <div className="grid grid-cols-2 gap-8">
                      <div>
                        <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-muted-foreground mb-2">Language</p>
                        <p className="text-lg font-bold text-foreground">{projectInfo?.language}</p>
                      </div>
                      <div>
                        <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-muted-foreground mb-2">Project Type</p>
                        <p className="text-lg font-bold text-foreground">{projectInfo?.appType}</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Right Column: Actions */}
              <div className="lg:col-span-5 group animate-in fade-in slide-in-from-right-4 duration-1000 delay-500">
                <div className="rounded-[40px] glass-panel p-10 sm:p-14 bg-white/5 border border-white/10 shadow-2xl h-full flex flex-col justify-center">
                  <div className="flex items-center gap-3 mb-8">
                    <div className="h-2 w-2 rounded-full bg-primary" />
                    <h2 className="text-xl sm:text-2xl font-black tracking-tight uppercase">Actions</h2>
                  </div>

                  <div className="flex flex-col gap-5 sm:gap-6 px-6 sm:px-8">
                    <Button 
                      onClick={() => router.push('/ide')}
                      className="w-full h-16 bg-gradient-to-r from-blue-600 to-cyan-500 hover:scale-[1.02] active:scale-[0.98] transition-all text-white border-none rounded-3xl shadow-[0_20px_40px_rgba(37,99,235,0.3)] group text-sm font-black uppercase tracking-widest px-4"
                    >
                      <div className="flex items-center justify-center gap-3">
                        <Code2 className="h-4 w-4 sm:h-5 sm:w-5 transition-transform group-hover:scale-110" />
                        <span className="whitespace-nowrap">View Code (Advanced)</span>
                      </div>
                    </Button>
                    
                    <Button 
                      onClick={handleDownload}
                      className="w-full h-16 rounded-3xl bg-[#f8f9fa] border border-black/5 hover:bg-white text-[#212529] text-[10px] sm:text-xs font-bold tracking-widest uppercase transition-all shadow-lg hover:scale-[1.02] active:scale-[0.98] px-4"
                    >
                       <div className="flex items-center justify-center gap-3">
                        <Download className="h-4 w-4 sm:h-5 sm:w-5" />
                        <span className="whitespace-nowrap">Download Project</span>
                      </div>
                    </Button>

                    <Button 
                      onClick={handlePreview}
                      className="w-full h-16 rounded-3xl bg-[#f8f9fa]/90 border border-black/5 hover:bg-white text-[#212529]/80 text-[10px] sm:text-xs font-bold tracking-widest uppercase transition-all shadow-md hover:scale-[1.02] active:scale-[0.98] px-4"
                    >
                       <div className="flex items-center justify-center gap-3">
                        <Eye className="h-4 w-4 sm:h-5 sm:w-5" />
                        <span className="whitespace-nowrap">Preview Project</span>
                      </div>
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

export default function PreviewPage() {
  return (
    <Suspense fallback={
      <div className="h-screen flex items-center justify-center">
        <Loader className="h-8 w-8 animate-spin text-primary" />
      </div>
    }>
      <PreviewContent />
    </Suspense>
  )
}
