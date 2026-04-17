'use client'

import { Navigation } from '@/components/navigation'
import { Button } from '@/components/ui/button'
import { useRouter } from 'next/navigation'

export default function LandingPage() {
  const router = useRouter()

  const handleStartBuilding = () => {
    router.push('/describe')
  }

  const steps = [
    {
      step: '01',
      title: 'Describe your project',
      description: 'Write your idea in plain language — no boilerplate or tech stack details needed.',
    },
    {
      step: '02',
      title: 'Choose Preference',
      description: 'Pick Python, JavaScript, or TypeScript and select the kind of application you want to build.',
    },
    {
      step: '03',
      title: 'Let it generate',
      description: 'Prompt2Product turns your description into a complete, production-ready codebase.',
    },
    {
      step: '04',
      title: 'Preview & test',
      description: 'Inspect the generated project, run it locally, and explore the structure.',
    },
    {
      step: '05',
      title: 'Download or refine',
      description: 'Download the code, or request changes and iterate until it matches your vision.',
    },
  ]

  return (
    <div className="min-h-screen bg-background text-foreground relative overflow-hidden page-transition">
      {/* Cinematic Background Layer */}
      <div className="mesh-gradient" />
      <div className="technical-grid" />

      <Navigation />

      <main className="pt-16">
        <section className="min-h-[calc(100vh-4rem)] flex flex-col justify-center gap-6 sm:gap-8 md:gap-10 lg:gap-12 px-6 sm:px-10 lg:px-16 xl:px-24">
          {/* Row 1 - Hero copy + CTA */}
          <div className="space-y-4 sm:space-y-6 md:space-y-8 animate-in fade-in duration-1000 text-center relative z-20">
            <div>
              <h1 className="text-2xl sm:text-3xl md:text-4xl lg:text-5xl xl:text-6xl font-black leading-tight text-foreground dark:text-white mb-3 sm:mb-4 text-balance tracking-tighter">
                Natural Language to{' '}
                <span className="hero-text-accent">
                  Executable Code
                </span>
              </h1>
              <p className="text-base sm:text-lg md:text-xl lg:text-2xl text-muted-foreground max-w-xl sm:max-w-2xl lg:max-w-3xl mx-auto font-light">
                Where Ideas Become Running Code
              </p>
            </div>

            <div className="flex justify-center gap-4 pt-2 flex-wrap">
              <Button
                size="lg"
                className="btn-glow bg-primary hover:bg-primary/85 text-primary-foreground font-semibold shadow-lg hover:shadow-xl text-sm sm:text-base"
                onClick={handleStartBuilding}
              >
                Start Building
              </Button>
            </div>
          </div>

          {/* Row 2 - Horizontal 5-step flow */}
          <div className="animate-in fade-in duration-1000 delay-150 text-center relative z-20">
            <h2 className="text-sm sm:text-base md:text-lg lg:text-xl font-black text-foreground dark:text-white mb-3 sm:mb-4 md:mb-5 tracking-tight uppercase">
              Your project in <span className="text-primary italic">5 easy steps</span>
            </h2>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
              {steps.map((item) => (
                <div
                  key={item.step}
                  className="rounded-2xl glass-panel px-4 py-4 sm:px-5 sm:py-6 flex flex-col gap-2 text-center items-center group hover:scale-[1.02] transition-all duration-300"
                >
                  <div className="flex h-8 w-8 sm:h-9 sm:w-9 items-center justify-center rounded-full bg-primary/20 text-xs sm:text-sm font-semibold text-primary mb-1">
                    {item.step}
                  </div>
                  <p className="text-sm sm:text-base font-medium text-foreground">
                    {item.title}
                  </p>
                  <p className="text-xs sm:text-sm text-muted-foreground leading-snug">
                    {item.description}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </section>
      </main>
    </div>
  )
}
