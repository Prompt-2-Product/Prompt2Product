'use client'

import { Navigation } from '@/components/navigation'
import { TeamMemberCard } from '@/components/team-member-card'
import { ArrowRight } from 'lucide-react'
import { Button } from '@/components/ui/button'
import Link from 'next/link'

export default function AboutPage() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <Navigation />

      <main className="pt-24 pb-20">
        <div className="mx-auto max-w-7xl px-6">
          {/* Hero Section */}
          <section className="mb-16 md:mb-20 animate-in fade-in duration-1000">
            <div className="max-w-3xl mb-12">
              <h1 className="text-4xl md:text-6xl font-bold text-foreground mb-6 text-balance">
                About Prompt2Product
              </h1>
              <p className="text-base md:text-lg text-muted-foreground leading-relaxed">
                Prompt2Product is a revolutionary AI-powered platform that transforms natural language descriptions into fully functional, production-ready code. We believe that great ideas shouldn't be limited by technical barriers. Our mission is to democratize software development by making it accessible to everyone, regardless of their coding expertise.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              {[
                {
                  title: 'Our Vision',
                  description: 'To create a world where anyone can build software by simply describing what they want to create.',
                },
                {
                  title: 'Our Mission',
                  description: 'Empower developers and non-developers alike to rapidly prototype and deploy applications using AI.',
                },
                {
                  title: 'Our Values',
                  description: 'Innovation, accessibility, and excellence in everything we build. We prioritize user experience and community.',
                },
              ].map((item, idx) => (
                <div
                  key={idx}
                  className="group bg-card border border-border rounded-xl p-6 hover:border-primary/60 hover:bg-card/80 transition-all duration-300 hover:shadow-lg hover:shadow-primary/10"
                >
                  <h3 className="text-lg font-semibold text-foreground mb-3 group-hover:text-primary transition-colors">{item.title}</h3>
                  <p className="text-muted-foreground text-sm leading-relaxed">{item.description}</p>
                </div>
              ))}
            </div>
          </section>

          {/* Divider */}
          <div className="h-px bg-gradient-to-r from-transparent via-border to-transparent my-20" />

          {/* Team Section */}
          <section className="animate-in fade-in duration-1000 delay-300">
            <div className="text-center mb-12 md:mb-16">
              <h2 className="text-3xl md:text-5xl font-bold text-foreground mb-4">
                Meet Our <span className="text-primary">Core Team</span>
              </h2>
              <p className="text-muted-foreground text-base md:text-lg max-w-2xl mx-auto px-4">
                A passionate group of developers, designers, and innovators working together to revolutionize how software is created.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8 mb-16">
              <TeamMemberCard
                name="Hamza Motiwala"
                role="Lead Developer"
                initials="HM"
                gradientColor="bg-gradient-to-br from-blue-500 to-blue-700"
                github="https://github.com"
                linkedin="https://linkedin.com"
                email="hamza@example.com"
              />
              <TeamMemberCard
                name="Zarish Asim"
                role="Full Stack Engineer"
                initials="ZA"
                gradientColor="bg-gradient-to-br from-purple-500 to-purple-700"
                github="https://github.com"
                linkedin="https://linkedin.com"
                email="zarish@example.com"
              />
              <TeamMemberCard
                name="Noor Fatima"
                role="UI/UX Designer"
                initials="NF"
                gradientColor="bg-gradient-to-br from-pink-500 to-rose-700"
                github="https://github.com"
                linkedin="https://linkedin.com"
                email="noor@example.com"
              />
              <TeamMemberCard
                name="Ayesha Khan"
                role="Product Manager"
                initials="AK"
                gradientColor="bg-gradient-to-br from-indigo-500 to-indigo-700"
                github="https://github.com"
                linkedin="https://linkedin.com"
                email="ayesha@example.com"
              />
            </div>

            {/* CTA */}
            <div className="text-center pt-12 border-t border-border">
              <h3 className="text-2xl font-semibold text-foreground mb-4">Ready to build something amazing?</h3>
              <p className="text-muted-foreground mb-6 max-w-lg mx-auto">
                Start creating production-ready code in seconds with Prompt2Product.
              </p>
              <Link href="/describe">
                <Button size="lg" className="bg-primary hover:bg-primary/90 text-primary-foreground font-semibold gap-2">
                  Start Building
                  <ArrowRight className="w-5 h-5" />
                </Button>
              </Link>
            </div>
          </section>
        </div>
      </main>
    </div>
  )
}
