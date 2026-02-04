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
    if (projectInfo?.projectId && projectInfo?.runId) {
      window.location.href = `http://127.0.0.1:8000/projects/${projectInfo.projectId}/runs/${projectInfo.runId}/download`
    }
  }

  const handlePreview = () => {
    if (projectInfo?.runId) {
      const port = 8000 + projectInfo.runId
      window.open(`http://127.0.0.1:${port}`, '_blank')
    }
  }

  if (!projectInfo) {
    return (
      <div className="min-h-screen bg-background text-foreground">
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
    <div className="min-h-screen bg-background text-foreground">
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

            {/* Right: Action Buttons */}
            <div className="space-y-4">
              <Button
                onClick={() => router.push('/ide')}
                className="btn-glow w-full bg-primary hover:bg-primary/85 text-primary-foreground font-semibold shadow-lg hover:shadow-xl"
                size="lg"
              >
                View Code (Advanced)
              </Button>

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
