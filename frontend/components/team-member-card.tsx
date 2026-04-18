'use client'

import { Github, Linkedin, Mail } from 'lucide-react'

interface TeamMemberProps {
  name: string
  role?: string
  initials: string
  gradientColor: string
  github?: string
  linkedin?: string
  email?: string
}

export function TeamMemberCard({
  name,
  role,
  initials,
  gradientColor,
  github,
  linkedin,
  email,
}: TeamMemberProps) {
  return (
    <div className="group relative team-card-glow rounded-2xl">
      <div className="relative rounded-2xl bg-card border border-border p-6 group-hover:border-primary/60 group-hover:bg-card/80 transition-all duration-300 flex flex-col items-center text-center">
        {/* Avatar */}
        <div
          className={`w-20 h-20 rounded-full flex items-center justify-center text-2xl font-bold text-white mb-4 ${gradientColor} shadow-lg`}
        >
          {initials}
        </div>

        {/* Name */}
        <h3 className="text-lg font-semibold text-foreground">{name}</h3>

        {/* Role */}
        {role && <p className="text-sm text-muted-foreground mt-1">{role}</p>}

        {/* Social Links */}
        <div className="flex items-center justify-center gap-3 mt-4 pt-4 border-t border-border/50 w-full">
          {linkedin && (
            <a
              href={linkedin}
              target="_blank"
              rel="noopener noreferrer"
              className="p-2 hover:bg-secondary rounded-lg transition-colors text-muted-foreground hover:text-primary"
              title="LinkedIn"
            >
              <Linkedin className="w-4 h-4" />
            </a>
          )}
          {github && (
            <a
              href={github}
              target="_blank"
              rel="noopener noreferrer"
              className="p-2 hover:bg-secondary rounded-lg transition-colors text-muted-foreground hover:text-primary"
              title="GitHub"
            >
              <Github className="w-4 h-4" />
            </a>
          )}
          {email && (
            <a
              href={`mailto:${email}`}
              className="p-2 hover:bg-secondary rounded-lg transition-colors text-muted-foreground hover:text-primary"
              title="Email"
            >
              <Mail className="w-4 h-4" />
            </a>
          )}
        </div>
      </div>
    </div>
  )
}
