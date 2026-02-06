'use client'

import { Navigation } from '@/components/navigation'
import { TeamMemberCard } from '@/components/team-member-card'
import { Code2, Zap, CheckCircle, ArrowRight, Target, Users, Sparkles } from 'lucide-react'
import { Button } from '@/components/ui/button'
import Link from 'next/link'

export default function OverviewPage() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <Navigation />

      <main className="pt-24 pb-20">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          {/* Hero Section */}
          <section className="mb-16 md:mb-24 animate-in fade-in duration-1000">
            <div className="max-w-4xl mx-auto mb-12 text-center">
              <h1 className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-bold text-foreground mb-6 text-balance">
                System <span className="bg-gradient-to-r from-blue-300 via-cyan-200 to-blue-200 bg-clip-text text-transparent">Overview</span>
              </h1>
              <p className="text-base sm:text-lg md:text-xl text-muted-foreground leading-relaxed max-w-3xl mx-auto">
                Prompt2Product is an AI-powered platform that transforms natural language descriptions into fully functional, production-ready code. We believe that great ideas shouldn't be limited by technical barriers.
              </p>
            </div>

            {/* Vision, Mission, Values */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 md:gap-8 mb-16">
              {[
                {
                  icon: Target,
                  title: 'Our Vision',
                  description: 'To create a world where anyone can build software by simply describing what they want to create.',
                },
                {
                  icon: Sparkles,
                  title: 'Our Mission',
                  description: 'Empower developers and non-developers alike to rapidly prototype and deploy applications using AI.',
                },
                {
                  icon: Users,
                  title: 'Our Values',
                  description: 'Innovation, accessibility, and excellence in everything we build. We prioritize user experience and community.',
                },
              ].map((item, idx) => (
                <div
                  key={idx}
                  className="group bg-card border border-border rounded-xl p-6 md:p-8 hover:border-primary/60 hover:bg-card/80 transition-all duration-300 hover:shadow-lg hover:shadow-primary/10 animate-in fade-in"
                  style={{ animationDelay: `${idx * 100}ms` }}
                >
                  <div className="w-12 h-12 md:w-14 md:h-14 rounded-lg bg-primary/20 text-primary flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300">
                    <item.icon className="w-6 h-6 md:w-7 md:h-7" />
                  </div>
                  <h3 className="text-lg md:text-xl font-semibold text-foreground mb-3 group-hover:text-primary transition-colors">{item.title}</h3>
                  <p className="text-muted-foreground text-sm md:text-base leading-relaxed">{item.description}</p>
                </div>
              ))}
            </div>
          </section>

          {/* Divider */}
          <div className="h-px bg-gradient-to-r from-transparent via-border to-transparent my-16 md:my-20" />

          {/* System Features */}
          <section className="mb-16 md:mb-24 animate-in fade-in duration-1000 delay-200">
            <div className="text-center mb-12 md:mb-16">
              <h2 className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl font-bold text-foreground mb-4">
                Powerful <span className="text-primary">Features</span>
              </h2>
              <p className="text-muted-foreground text-base md:text-lg max-w-2xl mx-auto">
                Everything you need to transform ideas into production-ready code
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 md:gap-8">
              {[
                {
                  icon: Code2,
                  title: 'AI-Powered Generation',
                  description: 'Advanced AI models analyze your descriptions and generate complete, working codebases with proper structure and best practices.',
                },
                {
                  icon: Zap,
                  title: 'Fast & Efficient',
                  description: 'Get your project generated in minutes, not hours. Our system optimizes the generation process for speed without compromising quality.',
                },
                {
                  icon: CheckCircle,
                  title: 'Production-Ready',
                  description: 'Generated code follows industry standards, includes proper error handling, and is ready for deployment.',
                },
              ].map((item, idx) => (
                <div
                  key={idx}
                  className="group bg-card border border-border rounded-xl p-6 md:p-8 hover:border-primary/60 hover:bg-card/80 transition-all duration-300 hover:shadow-lg hover:shadow-primary/10"
                >
                  <div className="w-12 h-12 md:w-14 md:h-14 rounded-lg bg-primary/20 text-primary flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300">
                    <item.icon className="w-6 h-6 md:w-7 md:h-7" />
                  </div>
                  <h3 className="text-lg md:text-xl font-semibold text-foreground mb-3 group-hover:text-primary transition-colors">{item.title}</h3>
                  <p className="text-muted-foreground text-sm md:text-base leading-relaxed">{item.description}</p>
                </div>
              ))}
            </div>
          </section>

          {/* How It Works */}
          <section className="mb-16 md:mb-24 animate-in fade-in duration-1000 delay-300">
            <div className="text-center mb-12 md:mb-16">
              <h2 className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl font-bold text-foreground mb-4">
                How It <span className="text-primary">Works</span>
              </h2>
              <p className="text-muted-foreground text-base md:text-lg max-w-2xl mx-auto">
                Simple steps to transform your ideas into running code
              </p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 md:gap-8">
              {[
                {
                  step: '01',
                  title: 'Describe Your Idea',
                  description: 'Simply write what you want to build in plain English. No technical jargon needed.',
                },
                {
                  step: '02',
                  title: 'AI Generates Code',
                  description: 'Our system analyzes your requirements and generates a complete, structured codebase.',
                },
                {
                  step: '03',
                  title: 'Review & Deploy',
                  description: 'Preview your generated project, make refinements if needed, and deploy to production.',
                },
              ].map((item, idx) => (
                <div
                  key={item.step}
                  className="bg-card border border-border rounded-xl p-6 md:p-8 text-center hover:border-primary/60 hover:bg-card/80 transition-all duration-300 hover:shadow-lg hover:shadow-primary/10"
                >
                  <div className="w-14 h-14 md:w-16 md:h-16 rounded-full bg-primary/20 text-primary flex items-center justify-center mx-auto mb-4 font-semibold text-lg md:text-xl group-hover:scale-110 transition-transform duration-300">
                    {item.step}
                  </div>
                  <h3 className="text-lg md:text-xl font-semibold text-foreground mb-3">{item.title}</h3>
                  <p className="text-muted-foreground text-sm md:text-base leading-relaxed">{item.description}</p>
                </div>
              ))}
            </div>
          </section>

          {/* Divider */}
          <div className="h-px bg-gradient-to-r from-transparent via-border to-transparent my-16 md:my-20" />

          {/* Team Section */}
          <section className="mb-16 md:mb-24 animate-in fade-in duration-1000 delay-400">
            <div className="text-center mb-12 md:mb-16">
              <h2 className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl font-bold text-foreground mb-4">
                Meet Our <span className="text-primary">Core Team</span>
              </h2>
              <p className="text-muted-foreground text-base md:text-lg max-w-2xl mx-auto px-4">
                A passionate group of developers, designers, and innovators working together to revolutionize how software is created.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 md:gap-8 mb-16">
              <TeamMemberCard
                name="Hamza Motiwala"
                role="Lead Developer"
                initials="HM"
                gradientColor="bg-gradient-to-br from-blue-500 to-blue-700"
                github="https://github.com/moti987"
                linkedin=""
                email="hamza@example.com"
              />
              <TeamMemberCard
                name="Zarish Asim"
                role="Full Stack Engineer"
                initials="ZA"
                gradientColor="bg-gradient-to-br from-purple-500 to-purple-700"
                github="https://github.com/Zarish166"
                linkedin="https://www.linkedin.com/in/zarish-asim-23a391339/"
                email="zarish@example.com"
              />
              <TeamMemberCard
                name="Noor Fatima"
                role="UI/UX Designer"
                initials="NF"
                gradientColor="bg-gradient-to-br from-pink-500 to-rose-700"
                github="https://github.com/SNoorFatima"
                linkedin="https://www.linkedin.com/in/syeda-noorfatima/"
                email="noor@example.com"
              />
              <TeamMemberCard
                name="Ayesha Khan"
                role="Product Manager"
                initials="AK"
                gradientColor="bg-gradient-to-br from-indigo-500 to-indigo-700"
                github="https://github.com/xKhani"
                linkedin="https://www.linkedin.com/in/ayesha-khani/"
                email="ayesha@example.com"
              />
            </div>
          </section>

          {/* CTA Section */}
          <div className="text-center pt-12 border-t border-border animate-in fade-in duration-1000 delay-500">
            <h3 className="text-2xl sm:text-3xl md:text-4xl font-semibold text-foreground mb-4">Ready to build something amazing?</h3>
            <p className="text-muted-foreground mb-8 text-base md:text-lg max-w-lg mx-auto">
              Start creating production-ready code with Prompt2Product.
            </p>
            <Link href="/describe">
              <Button 
                size="lg" 
                className="btn-glow bg-primary hover:bg-primary/85 text-primary-foreground font-semibold gap-2 shadow-lg hover:shadow-xl text-base md:text-lg px-8 py-6"
              >
                Start Building
                <ArrowRight className="w-5 h-5" />
              </Button>
            </Link>
          </div>
        </div>
      </main>
    </div>
  )
}
