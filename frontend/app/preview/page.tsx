'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Navigation } from '@/components/navigation'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'

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
  const [showRequestChanges, setShowRequestChanges] = useState(false)
  const [changes, setChanges] = useState('')
  const [isRegenerating, setIsRegenerating] = useState(false) // Declare the isRegenerating variable

  useEffect(() => {
    const stored = sessionStorage.getItem('projectInfo')
    if (stored) {
      setProjectInfo(JSON.parse(stored))
    }
  }, [])

  const handleRequestChanges = () => {
    if (changes.trim()) {
      // Store the changes request and navigate to generating page
      sessionStorage.setItem('changeRequest', changes)
      router.push('/generating')
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
<<<<<<< Updated upstream
      <div className="min-h-screen bg-background text-foreground">
=======
      <div className="min-h-screen text-foreground relative overflow-hidden">
        <div
          className="pointer-events-none absolute inset-0 -z-10"
          aria-hidden="true"
          style={{
            background: 'linear-gradient(to bottom, rgb(0, 0, 0) 0%, rgb(30, 58, 138) 33%, rgb(59, 130, 246) 66%, rgb(255, 255, 255) 100%)',
          }}
        />
>>>>>>> Stashed changes
        <Navigation />
        <main className="pt-24">
          <div className="mx-auto max-w-7xl px-6 text-center">
            <p>Loading...</p>
          </div>
        </main>
      </div>
    )
  }

  return (
<<<<<<< Updated upstream
    <div className="min-h-screen bg-background text-foreground">
=======
    <div className="min-h-screen text-foreground relative overflow-hidden page-transition">
      {/* Multi-color vertical gradient background */}
      <div
        className="pointer-events-none absolute inset-0 -z-10"
        aria-hidden="true"
        style={{
          background: 'linear-gradient(to bottom, rgb(0, 0, 0) 0%, rgb(30, 58, 138) 33%, rgb(59, 130, 246) 66%, rgb(255, 255, 255) 100%)',
        }}
      />
>>>>>>> Stashed changes
      <Navigation />

      <main className="pt-24 pb-20">
        <div className="mx-auto max-w-7xl px-6">
          <div className="mb-6 md:mb-8">
            <h1 className="text-3xl md:text-4xl font-bold mb-2">Project Summary</h1>
            <p className="text-muted-foreground text-sm md:text-base">Review your generated project</p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 md:gap-8 mb-8 md:mb-12">
            {/* Left: Project Info Card */}
            <div className="lg:col-span-2">
              <div className="rounded-xl bg-card border border-border p-8">
                <h2 className="text-2xl font-semibold mb-6">Generated Project</h2>

<<<<<<< Updated upstream
                <div className="space-y-6">
                  <div>
                    <label className="text-sm font-medium text-muted-foreground block mb-2">Project Description</label>
                    <p className="text-foreground text-base leading-relaxed">{projectInfo.description}</p>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="text-sm font-medium text-muted-foreground block mb-2">Language</label>
                      <p className="text-foreground font-medium">{projectInfo.language}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-muted-foreground block mb-2">Project Type</label>
                      <p className="text-foreground font-medium">{projectInfo.appType}</p>
=======
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
        <div className="flex-1 overflow-y-auto custom-scrollbar flex items-center justify-center" style={{ background: 'linear-gradient(to bottom, rgb(0, 0, 0) 0%, rgb(30, 58, 138) 33%, rgb(59, 130, 246) 66%, rgb(255, 255, 255) 100%)' }}>
          <div className={`p-6 lg:p-8 w-full ${!showChat ? 'max-w-7xl mx-auto page-content' : 'mx-auto'} flex flex-col items-center justify-center`}>
            <div className="mb-6 md:mb-8 text-center">
              <h1 className="text-3xl sm:text-4xl md:text-5xl font-bold mb-2 text-white">Project Summary</h1>
              <p className="text-white text-sm md:text-base">Review your generated project</p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 md:gap-8 mb-8 md:mb-12 lg:items-stretch w-full">
            {/* Left: Project Info Card - Matching describe page style */}
            <div className="lg:col-span-2 flex">
              <div className="rounded-2xl bg-card/90 border border-white/10 shadow-2xl backdrop-blur-sm p-5 sm:p-6 md:p-8 w-full flex flex-col">
                <h2 className="text-xl sm:text-2xl font-semibold mb-4 sm:mb-6 text-foreground">Generated Project</h2>

                <div className="space-y-4 sm:space-y-6 flex-grow">
                  <div>
                    <label className="text-xs sm:text-sm font-medium text-muted-foreground block mb-2">Installation Steps</label>
                    <div className="space-y-3 text-foreground text-sm sm:text-base leading-relaxed">
                      <p><strong>1. Download:</strong> Click &quot;Download Project&quot; to get the ZIP file.</p>
                      <p><strong>2. Extract:</strong> Extract the ZIP file to your desired location.</p>
                      <p><strong>3. Install:</strong> Navigate to the project directory and run <code className="px-1.5 py-0.5 rounded bg-secondary/50 text-primary font-mono text-xs">pip install -r requirements.txt</code> or <code className="px-1.5 py-0.5 rounded bg-secondary/50 text-primary font-mono text-xs">npm install</code></p>
                      <p><strong>4. Run:</strong> Execute <code className="px-1.5 py-0.5 rounded bg-secondary/50 text-primary font-mono text-xs">python main.py</code> or <code className="px-1.5 py-0.5 rounded bg-secondary/50 text-primary font-mono text-xs">npm start</code> to start the application.</p>
                      <p><strong>5. Access:</strong> Open <code className="px-1.5 py-0.5 rounded bg-secondary/50 text-primary font-mono text-xs">http://localhost:8000</code> in your browser.</p>
>>>>>>> Stashed changes
                    </div>
                  </div>
                </div>
              </div>
            </div>

<<<<<<< Updated upstream
            {/* Right: Action Buttons */}
            <div className="space-y-4">
              <Button
                onClick={() => router.push('/ide')}
                className="btn-glow w-full bg-primary hover:bg-primary/85 text-primary-foreground font-semibold shadow-lg hover:shadow-xl"
                size="lg"
              >
                View Code (Advanced)
              </Button>
=======
            {/* Right: Action Buttons - Matching describe page style */}
            <div className="flex">
              <div className="rounded-2xl bg-card/90 border border-white/10 shadow-2xl backdrop-blur-sm p-5 sm:p-6 md:p-8 w-full flex flex-col">
                <h3 className="text-xl sm:text-2xl font-semibold text-foreground mb-4 sm:mb-6">Actions</h3>
                <div className="space-y-2.5 sm:space-y-3 flex-grow flex flex-col justify-start">
                  <Button
                    onClick={() => router.push('/ide')}
                    className="w-full bg-gradient-to-r from-blue-600 via-blue-500 to-cyan-600 hover:from-blue-700 hover:via-blue-600 hover:to-cyan-700 text-white font-semibold shadow-lg hover:shadow-xl transition-all duration-300 h-12 group"
                    size="lg"
                  >
                    <Code2 className="mr-2 h-5 w-5 group-hover:rotate-12 transition-transform" />
                    View Code (Advanced)
                  </Button>
>>>>>>> Stashed changes

              <Button
                onClick={() => setShowRequestChanges(!showRequestChanges)}
                variant="outline"
                className="btn-glow w-full border-border/50 text-foreground hover:bg-secondary/40 hover:border-primary/50"
                size="lg"
              >
                Request Changes
              </Button>

              <Button
                onClick={handleDownload}
                variant="outline"
                className="btn-glow w-full border-border/50 text-foreground hover:bg-secondary/40 bg-transparent hover:border-primary/50"
                size="lg"
              >
                Download Project
              </Button>

              <Button
                onClick={handlePreview}
                variant="outline"
                className="btn-glow w-full border-border/50 text-foreground hover:bg-secondary/40 bg-transparent hover:border-primary/50"
                size="lg"
              >
                Preview App
              </Button>
            </div>
          </div>

          {/* Request Changes Section */}
          {showRequestChanges && (
            <div className="rounded-xl bg-card border border-border p-8 mb-8">
              <h3 className="text-xl font-semibold mb-4">Request Changes</h3>
              <p className="text-muted-foreground text-sm mb-4">
                Describe what you'd like to change about the generated project
              </p>

              <div className="space-y-4">
                <Textarea
                  value={changes}
                  onChange={(e) => setChanges(e.target.value)}
                  placeholder="E.g., Add authentication, change the color scheme, add more features..."
                  className="min-h-32 bg-secondary border-border"
                />

                <div className="flex gap-3">
                  <Button
                    onClick={handleRequestChanges}
                    disabled={!changes.trim()}
                    className="btn-glow bg-primary hover:bg-primary/85 text-primary-foreground font-semibold shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Apply Changes
                  </Button>
                  <Button
                    onClick={() => {
                      setShowRequestChanges(false)
                      setChanges('')
                    }}
                    variant="outline"
                    className="btn-glow border-border/50 text-foreground hover:bg-secondary/40 hover:border-primary/50"
                  >
                    Cancel
                  </Button>
                </div>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
