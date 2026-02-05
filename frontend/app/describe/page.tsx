'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Navigation } from '@/components/navigation'
import { Button } from '@/components/ui/button'
import { Loader } from 'lucide-react'

const APP_TYPES = [
  'Web App',
  'API Backend',
  'CLI Tool',
  'Data Analysis Script',
  'ML Pipeline',
  'Automation Script',
  'Scraper',
  'Chatbot',
  'Mobile App UI',
  'Desktop App',
]

const detectLanguage = (text: string): string => {
  const lowerText = text.toLowerCase()
  if (lowerText.includes('javascript') || lowerText.includes('react') || lowerText.includes('nextjs') || lowerText.includes('node')) {
    return 'JavaScript'
  }
  if (lowerText.includes('typescript') || lowerText.includes('ts')) {
    return 'TypeScript'
  }
  return 'Python'
}

const detectAppType = (text: string): string => {
  const lowerText = text.toLowerCase()
  if (lowerText.includes('api') || lowerText.includes('backend') || lowerText.includes('server')) {
    return 'API Backend'
  }
  if (lowerText.includes('cli') || lowerText.includes('command line')) {
    return 'CLI Tool'
  }
  if (lowerText.includes('data') || lowerText.includes('analysis')) {
    return 'Data Analysis Script'
  }
  if (lowerText.includes('ml') || lowerText.includes('machine learning') || lowerText.includes('model')) {
    return 'ML Pipeline'
  }
  if (lowerText.includes('automation') || lowerText.includes('task')) {
    return 'Automation Script'
  }
  if (lowerText.includes('scrape') || lowerText.includes('crawler')) {
    return 'Scraper'
  }
  if (lowerText.includes('chat') || lowerText.includes('bot')) {
    return 'Chatbot'
  }
  if (lowerText.includes('web') || lowerText.includes('app') || lowerText.includes('site')) {
    return 'Web App'
  }
  return 'Web App'
}

export default function DescribePage() {
  const router = useRouter()
  const [description, setDescription] = useState('')
  const [language, setLanguage] = useState('Python')
  const [appType, setAppType] = useState('Web App')
  const [additionalInstructions, setAdditionalInstructions] = useState('')
  const [isGenerating, setIsGenerating] = useState(false)

  const handleAutoDetect = () => {
    if (description.trim()) {
      setLanguage(detectLanguage(description))
      setAppType(detectAppType(description))
    }
  }

  const handleGenerateProject = async () => {
    if (description.trim()) {
      setIsGenerating(true)
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        console.log('Starting generation with API URL:', apiUrl);

        // 1. Create Project
        console.log('Creating project...');
        const pRes = await fetch(`${apiUrl}/projects`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name: `Project ${new Date().toISOString()}` })
        })
        if (!pRes.ok) throw new Error(`Failed to create project: ${pRes.statusText}`)
        const project = await pRes.json()
        console.log('Project created:', project);

        // 2. Start Run
        console.log('Starting run...');
        const rRes = await fetch(`${apiUrl}/projects/${project.id}/runs`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            prompt: description + (additionalInstructions ? `\n\n${additionalInstructions}` : ''),
            entrypoint: 'main.py' // Default for now
          })
        })
        if (!rRes.ok) throw new Error(`Failed to start run: ${rRes.statusText}`)
        const run = await rRes.json()
        console.log('Run started:', run);

        // Store project info for the generating page
        const projectInfo = {
          description,
          language,
          appType,
          additionalInstructions,
          projectId: project.id,
          runId: run.run_id
        };
        console.log('Storing project info in sessionStorage:', projectInfo);
        sessionStorage.setItem('projectInfo', JSON.stringify(projectInfo))

        console.log('Redirecting to /generating...');
        router.push('/generating')

      } catch (err) {
        console.error('Generation Error:', err)
        alert(`Failed to start generation: ${err instanceof Error ? err.message : 'Unknown error'}. Ensure backend is running at ${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}`)
      } finally {
        setIsGenerating(false)
      }
    }
  }

  return (
    <div className="min-h-screen bg-background text-foreground">
      <Navigation />

      <main className="pt-24 pb-20">
        <div className="mx-auto max-w-7xl px-6">
          {/* Title */}
          <div className="mb-8 md:mb-12 text-center">
            <h1 className="text-3xl md:text-5xl font-bold text-foreground">Describe Your Project</h1>
          </div>

          {/* Two column layout */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 md:gap-8 mb-8">
            {/* Left column - Textarea */}
            <div className="lg:col-span-2">
              <label className="block text-sm font-medium text-foreground mb-3">
                What do you want to build?
              </label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Describe what you want to build…"
                className="w-full h-80 rounded-xl bg-card border border-border p-4 text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent resize-none"
              />
            </div>

            {/* Right column - Options */}
            <div>
              <div className="rounded-xl bg-card border border-border p-6">
                <div className="flex items-center justify-between mb-6">
                  <h3 className="text-lg font-semibold text-foreground">Project Options</h3>
                  <Button
                    onClick={handleAutoDetect}
                    variant="outline"
                    size="sm"
                    className="border-primary text-primary hover:bg-primary/10 bg-transparent"
                  >
                    Auto Detect
                  </Button>
                </div>

                {/* Language Dropdown */}
                <div className="mb-5">
                  <label className="block text-xs font-medium text-muted-foreground mb-2">Language</label>
                  <select
                    value={language}
                    onChange={(e) => setLanguage(e.target.value)}
                    className="w-full rounded-lg bg-secondary border border-border px-3 py-2 text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                  >
                    <option>Python</option>
                    <option>JavaScript</option>
                    <option>TypeScript</option>
                  </select>
                </div>

                {/* App Type Dropdown */}
                <div className="mb-5">
                  <label className="block text-xs font-medium text-muted-foreground mb-2">App Type</label>
                  <select
                    value={appType}
                    onChange={(e) => setAppType(e.target.value)}
                    className="w-full rounded-lg bg-secondary border border-border px-3 py-2 text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                  >
                    {APP_TYPES.map((type) => (
                      <option key={type}>{type}</option>
                    ))}
                  </select>
                </div>

                {/* Additional Instructions */}
                <div>
                  <label className="block text-xs font-medium text-muted-foreground mb-2">Additional Instructions</label>
                  <input
                    type="text"
                    value={additionalInstructions}
                    onChange={(e) => setAdditionalInstructions(e.target.value)}
                    placeholder="Any specific requirements..."
                    className="w-full rounded-lg bg-secondary border border-border px-3 py-2 text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                  />
                </div>
              </div>
            </div>
          </div>

          <div className="flex justify-end pt-4">
            <Button
              onClick={handleGenerateProject}
              disabled={!description.trim() || isGenerating}
              size="lg"
              className="btn-glow bg-primary hover:bg-primary/85 text-primary-foreground disabled:opacity-50 disabled:cursor-not-allowed font-semibold shadow-lg hover:shadow-xl min-w-[160px]"
            >
              {isGenerating ? (
                <>
                  <Loader className="mr-2 h-4 w-4 animate-spin" />
                  Generating...
                </>
              ) : (
                'Generate Project'
              )}
            </Button>
          </div>
        </div>
      </main>
    </div>
  )
}
