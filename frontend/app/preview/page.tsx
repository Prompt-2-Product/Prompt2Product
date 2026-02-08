
'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Navigation } from '@/components/navigation'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Code2, Edit3, Download, Eye, Sparkles } from 'lucide-react'

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
      <div className="min-h-screen text-foreground relative overflow-hidden">
        <div
          className="pointer-events-none absolute inset-0 -z-10"
          aria-hidden="true"
          style={{
            background: 'linear-gradient(135deg, rgb(147, 197, 253) 0%, rgb(165, 243, 252) 50%, rgb(191, 219, 254) 100%)',
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
    <div className="min-h-screen text-foreground relative overflow-hidden">
      {/* Light blue gradient background - matching describe and generating pages */}
      <div
        className="pointer-events-none absolute inset-0 -z-10"
        aria-hidden="true"
        style={{
          background: 'linear-gradient(135deg, rgb(147, 197, 253) 0%, rgb(165, 243, 252) 50%, rgb(191, 219, 254) 100%)',
        }}
      />
      <Navigation />

      <main className="flex items-center justify-center min-h-[calc(100vh-5rem)] pt-8 sm:pt-16 md:pt-24 pb-8 sm:pb-16">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 w-full">
          <div className="mb-6 md:mb-8 text-center">
            <h1 className="text-3xl sm:text-4xl md:text-5xl font-bold mb-2 text-slate-800 dark:text-slate-900">Project Summary</h1>
            <p className="text-slate-700 dark:text-slate-800 text-sm md:text-base">Review your generated project</p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 md:gap-8 mb-8 md:mb-12 lg:items-stretch">
            {/* Left: Project Info Card */}
            <div className="lg:col-span-2 flex">
              <div className="rounded-xl bg-white/80 backdrop-blur-md border border-slate-200/50 shadow-lg p-6 md:p-8 w-full flex flex-col">
                <h2 className="text-2xl font-semibold mb-6 text-slate-800 dark:text-slate-900">Generated Project</h2>

                <div className="space-y-6 flex-grow">
                  <div>
                    <label className="text-sm font-medium text-slate-600 dark:text-slate-700 block mb-2">Project Description</label>
                    <p className="text-slate-800 dark:text-slate-900 text-base leading-relaxed">{projectInfo.description}</p>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="text-sm font-medium text-slate-600 dark:text-slate-700 block mb-2">Language</label>
                      <p className="text-slate-800 dark:text-slate-900 font-medium">{projectInfo.language}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-slate-600 dark:text-slate-700 block mb-2">Project Type</label>
                      <p className="text-slate-800 dark:text-slate-900 font-medium">{projectInfo.appType}</p>
                    </div>
                  </div>

                  {projectInfo.additionalInstructions && (
                    <div>
                      <label className="text-sm font-medium text-slate-600 dark:text-slate-700 block mb-2">Additional Instructions</label>
                      <p className="text-slate-800 dark:text-slate-900 text-sm">{projectInfo.additionalInstructions}</p>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Right: Action Buttons */}
            <div className="flex">
              <div className="rounded-xl bg-white/80 backdrop-blur-md border border-slate-200/50 shadow-lg p-6 md:p-8 w-full flex flex-col">
                <h3 className="text-2xl font-semibold text-slate-800 dark:text-slate-900 mb-6">Actions</h3>
                <div className="space-y-3 flex-grow flex flex-col justify-start">
                  <Button
                    onClick={() => router.push('/ide')}
                    className="w-full bg-gradient-to-r from-blue-500 via-blue-400 to-cyan-500 hover:from-blue-600 hover:via-blue-500 hover:to-cyan-600 text-white font-semibold shadow-lg hover:shadow-xl transition-all duration-300 h-12 group"
                    size="lg"
                  >
                    <Code2 className="mr-2 h-5 w-5 group-hover:rotate-12 transition-transform" />
                    View Code (Advanced)
                  </Button>

                  <Button
                    onClick={() => setShowRequestChanges(!showRequestChanges)}
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

          {/* Request Changes Section */}
          {showRequestChanges && (
            <div className="rounded-xl bg-white/80 backdrop-blur-md border border-slate-200/50 shadow-lg p-6 md:p-8 mb-8">
              <h3 className="text-xl font-semibold mb-4 text-slate-800 dark:text-slate-900">Request Changes</h3>
              <p className="text-slate-700 dark:text-slate-800 text-sm mb-4">
                Describe what you'd like to change about the generated project
              </p>

              <div className="space-y-4">
                <Textarea
                  value={changes}
                  onChange={(e) => setChanges(e.target.value)}
                  placeholder="E.g., Add authentication, change the color scheme, add more features..."
                  className="min-h-32 !bg-background backdrop-blur-md border-b border-border text-foreground placeholder:text-muted-foreground"
                />

                <div className="flex gap-3">
                  <Button
                    onClick={handleRequestChanges}
                    disabled={!changes.trim()}
                    className="bg-gradient-to-r from-blue-500 via-blue-400 to-cyan-500 hover:from-blue-600 hover:via-blue-500 hover:to-cyan-600 text-white font-semibold shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 px-6 group"
                  >
                    <Sparkles className="mr-2 h-4 w-4 group-hover:rotate-180 transition-transform duration-500" />
                    Apply Changes
                  </Button>
                  <Button
                    onClick={() => {
                      setShowRequestChanges(false)
                      setChanges('')
                    }}
                    variant="outline"
                    className="border-b border-border !bg-background backdrop-blur-md text-foreground hover:!bg-background/90 transition-all duration-300 px-6 font-medium shadow-sm hover:shadow-md"
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
