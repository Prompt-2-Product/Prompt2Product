
'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Navigation } from '@/components/navigation'
import { Button } from '@/components/ui/button'
import { Code2, Edit3, Download, Eye, Loader, X } from 'lucide-react'

interface ProjectInfo {
  description: string
  language: string
  appType: string
  additionalInstructions: string
  projectId?: number
  runId?: number
}

export default function PreviewPage() {
  const router = useRouter()
  const [projectInfo, setProjectInfo] = useState<ProjectInfo | null>(null)
  const [showChat, setShowChat] = useState(false)
  const [isRegenerating, setIsRegenerating] = useState(false)
  const [changeMessage, setChangeMessage] = useState('')
  const [chatHistory, setChatHistory] = useState<Array<{ role: 'user' | 'system'; content: string }>>([])

  useEffect(() => {
    const stored = sessionStorage.getItem('projectInfo')
    if (stored) {
      setProjectInfo(JSON.parse(stored))
    }
  }, [])

  const handleChatSubmit = (message: string) => {
    if (message.trim()) {
      // Add to chat history
      setChatHistory(prev => [...prev, { role: 'user', content: message }])
      setChangeMessage('')
      
      // Store the changes request and navigate to generating page
      sessionStorage.setItem('changeRequest', message)
      setIsRegenerating(true)
      // Small delay to show processing state
      setTimeout(() => {
        router.push('/generating')
      }, 1000)
    }
  }

  const handleDownload = () => {
    // Mock implementation - simulate download
    if (projectInfo?.projectId && projectInfo?.runId) {
      // Create a dummy download (you can enhance this to create an actual zip file)
      const fileName = `project-${projectInfo.projectId}-${Date.now()}.zip`
      alert(`Mock download: ${fileName}\n\nIn production, this would download the generated project.`)
      console.log('Mock download triggered for project:', projectInfo.projectId, 'run:', projectInfo.runId)
    }
  }

  const handlePreview = () => {
    // Mock implementation - simulate preview
    if (projectInfo?.runId) {
      alert(`Mock preview: Opening preview for run ${projectInfo.runId}\n\nIn production, this would open the running application.`)
      console.log('Mock preview triggered for run:', projectInfo.runId)
      // Uncomment below to actually try opening (will fail without backend, but shows intent)
      // const port = 8000 + projectInfo.runId
      // window.open(`http://127.0.0.1:${port}`, '_blank')
    }
  }

  if (!projectInfo) {
    return (
      <div className="min-h-screen text-foreground relative overflow-hidden">
        <div
          className="pointer-events-none absolute inset-0 -z-10"
          aria-hidden="true"
          style={{
            background: 'linear-gradient(to bottom, rgb(0, 0, 0) 0%, rgb(0, 0, 139) 33.33%, rgb(135, 206, 250) 66.66%, rgb(255, 255, 255) 100%)',
          }}
        />
        <Navigation />
        <main className="flex items-center justify-center min-h-[calc(100vh-5rem)] pt-8 sm:pt-16 md:pt-24 pb-8 sm:pb-16">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 text-center">
            <p className="text-slate-800 dark:text-slate-900">Loading...</p>
          </div>
        </main>
      </div>
    )
  }

  return (
    <div className="min-h-screen text-foreground relative overflow-hidden page-transition">
      {/* Light blue gradient background - matching describe and generating pages */}
      <div
        className="pointer-events-none absolute inset-0 -z-10"
        aria-hidden="true"
        style={{
          background: 'linear-gradient(to bottom, rgb(0, 0, 0) 0%, rgb(0, 0, 139) 33.33%, rgb(135, 206, 250) 66.66%, rgb(255, 255, 255) 100%)',
        }}
      />
      <Navigation />

      <main className="absolute inset-x-0 top-[3rem] bottom-0 flex flex-col lg:flex-row">
        {/* Left: Chat Sidebar - Only visible when showChat is true */}
        {showChat && projectInfo && (
          <aside className="w-full lg:w-[380px] border-r border-border/50 bg-background flex flex-col flex-shrink-0 h-full">
            {/* Chat Header */}
            <div className="px-5 py-4 border-b border-border/50 flex-shrink-0 bg-background backdrop-blur-sm">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <h2 className="text-base font-semibold text-foreground mb-1">Request Changes</h2>
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-xs px-2 py-0.5 rounded-md bg-primary/10 text-primary border border-primary/20">
                      {projectInfo.language}
                    </span>
                    <span className="text-xs px-2 py-0.5 rounded-md bg-secondary/50 text-foreground border border-border/50">
                      {projectInfo.appType}
                    </span>
                  </div>
                </div>
                <button
                  onClick={() => setShowChat(false)}
                  className="p-2 hover:bg-secondary/50 rounded-lg transition-colors"
                  aria-label="Close chat"
                >
                  <X className="h-5 w-5 text-foreground" />
                </button>
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
                  <span className="text-xs font-medium text-muted-foreground">You</span>
                </div>
                <div className="ml-8 rounded-xl bg-secondary/60 border border-border/60 p-4 text-sm leading-relaxed text-foreground whitespace-pre-wrap break-words shadow-sm">
                  {projectInfo.description}
                </div>
              </div>

              {/* System Response */}
              <div className="flex flex-col gap-2.5">
                <div className="flex items-center gap-2">
                  <div className="h-6 w-6 rounded-full bg-gradient-to-r from-blue-500 to-cyan-500 flex items-center justify-center">
                    <span className="text-xs font-semibold text-white">P</span>
                  </div>
                  <span className="text-xs font-medium text-muted-foreground">Prompt2Product</span>
                </div>
                <div className="ml-8 rounded-xl bg-primary/15 border border-primary/30 p-4 text-sm leading-relaxed text-foreground shadow-sm">
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
                    <span className="text-xs font-medium text-muted-foreground">You</span>
                  </div>
                  <div className="ml-8 rounded-xl bg-secondary/60 border border-border/60 p-4 text-sm leading-relaxed text-foreground whitespace-pre-wrap break-words shadow-sm">
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
                    <span className="text-xs font-medium text-muted-foreground">Prompt2Product</span>
                  </div>
                  <div className="ml-8 rounded-xl bg-primary/15 border border-primary/30 p-4 text-sm leading-relaxed text-foreground shadow-sm">
                    <div className="flex items-center gap-2">
                      <Loader className="h-4 w-4 animate-spin text-primary" />
                      <span className="font-medium">Processing your request...</span>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Chat Input Area */}
            <div className="px-5 py-4 border-t border-border/50 flex-shrink-0 bg-background">
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
                  className="flex-1 min-h-[90px] rounded-xl bg-secondary/40 border border-border/60 px-4 py-3 text-sm text-foreground placeholder:text-muted-foreground resize-none focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent disabled:cursor-not-allowed disabled:opacity-70"
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
          </aside>
        )}

        {/* Right: Main Content */}
        <div className="flex-1 overflow-y-auto custom-scrollbar" style={{ background: 'linear-gradient(to bottom, rgb(0, 0, 0) 0%, rgb(0, 0, 139) 33.33%, rgb(135, 206, 250) 66.66%, rgb(255, 255, 255) 100%)' }}>
          <div className="p-6 lg:p-8 max-w-7xl mx-auto page-content">
            <div className="mb-6 md:mb-8 text-center">
              <h1 className="text-3xl sm:text-4xl md:text-5xl font-bold mb-2 text-white">Project Summary</h1>
              <p className="text-white text-sm md:text-base">Review your generated project</p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 md:gap-8 mb-8 md:mb-12 lg:items-stretch">
            {/* Left: Project Info Card - Matching describe page style */}
            <div className="lg:col-span-2 flex">
              <div className="rounded-2xl bg-card/90 border border-white/10 shadow-2xl backdrop-blur-sm p-5 sm:p-6 md:p-8 w-full flex flex-col">
                <h2 className="text-xl sm:text-2xl font-semibold mb-4 sm:mb-6 text-foreground">Generated Project</h2>

                <div className="space-y-4 sm:space-y-6 flex-grow">
                  <div>
                    <label className="text-xs sm:text-sm font-medium text-muted-foreground block mb-2">Project Description</label>
                    <p className="text-foreground text-sm sm:text-base leading-relaxed">{projectInfo.description}</p>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                      <label className="text-sm font-medium text-muted-foreground block mb-2">Language</label>
                      <p className="text-foreground font-medium">{projectInfo.language}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-muted-foreground block mb-2">Project Type</label>
                      <p className="text-foreground font-medium">{projectInfo.appType}</p>
                    </div>
                  </div>

                  {projectInfo.additionalInstructions && (
                    <div>
                      <label className="text-sm font-medium text-muted-foreground block mb-2">Additional Instructions</label>
                      <p className="text-foreground text-sm">{projectInfo.additionalInstructions}</p>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Right: Action Buttons - Matching describe page style */}
            <div className="flex">
              <div className="rounded-2xl bg-card/90 border border-white/10 shadow-2xl backdrop-blur-sm p-5 sm:p-6 md:p-8 w-full flex flex-col">
                <h3 className="text-xl sm:text-2xl font-semibold text-foreground mb-4 sm:mb-6">Actions</h3>
                <div className="space-y-2.5 sm:space-y-3 flex-grow flex flex-col justify-start">
                  <Button
                    onClick={() => router.push('/ide')}
                    className="w-full bg-gradient-to-r from-blue-600 via-blue-500 to-cyan-600 hover:from-blue-600 hover:via-blue-500 hover:to-cyan-600 text-white font-semibold shadow-lg hover:shadow-xl transition-all duration-300 h-12 group"
                    size="lg"
                  >
                    <Code2 className="mr-2 h-5 w-5 group-hover:rotate-12 transition-transform" />
                    View Code (Advanced)
                  </Button>

                  <Button
                    onClick={() => setShowChat(true)}
                    variant="outline"
                    className="w-full border-b border-border !bg-background backdrop-blur-md text-foreground hover:!bg-background/90 hover:border-blue-400/50 transition-all duration-300 h-12 font-medium shadow-sm hover:shadow-md group"
                    size="lg"
                  >
                    <Edit3 className="mr-2 h-4 w-4 group-hover:scale-110 transition-transform group-hover:text-blue-400" />
                    <span className="group-hover:bg-gradient-to-r group-hover:from-blue-500 group-hover:to-cyan-500 group-hover:bg-clip-text group-hover:text-transparent transition-all duration-300">
                      Request Changes
                    </span>
                  </Button>

                  <Button
                    onClick={handleDownload}
                    variant="outline"
                    className="w-full border-b border-border !bg-background backdrop-blur-md text-foreground hover:!bg-background/90 hover:border-blue-400/50 transition-all duration-300 h-12 font-medium shadow-sm hover:shadow-md group"
                    size="lg"
                  >
                    <Download className="mr-2 h-4 w-4 group-hover:translate-y-0.5 transition-transform group-hover:text-blue-400" />
                    <span className="group-hover:bg-gradient-to-r group-hover:from-blue-500 group-hover:to-cyan-500 group-hover:bg-clip-text group-hover:text-transparent transition-all duration-300">
                      Download Project
                    </span>
                  </Button>

                  <Button
                    onClick={handlePreview}
                    variant="outline"
                    className="w-full border-b border-border !bg-background backdrop-blur-md text-foreground hover:!bg-background/90 hover:border-blue-400/50 transition-all duration-300 h-12 font-medium shadow-sm hover:shadow-md group"
                    size="lg"
                  >
                    <Eye className="mr-2 h-4 w-4 group-hover:scale-110 transition-transform group-hover:text-blue-400" />
                    <span className="group-hover:bg-gradient-to-r group-hover:from-blue-500 group-hover:to-cyan-500 group-hover:bg-clip-text group-hover:text-transparent transition-all duration-300">
                      Preview Prompt
                    </span>
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
