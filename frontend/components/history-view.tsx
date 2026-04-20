'use client'

import { useEffect, useState } from 'react'
import { History, Lock, Clock, CornerDownRight } from 'lucide-react'
import { api } from '@/lib/api'
import { Button } from '@/components/ui/button'

interface Project {
  id: number
  name: string
  created_at?: string
}

interface HistoryViewProps {
  onSelectProject?: (projectId: number) => void
}

export function HistoryView({ onSelectProject }: HistoryViewProps) {
  const [user, setUser] = useState<{ name: string } | null>(null)
  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(false)
  const [selectedId, setSelectedId] = useState<number | null>(null)

  useEffect(() => {
    const storedUser = localStorage.getItem('user')
    if (storedUser) {
      const parsedUser = JSON.parse(storedUser)
      setUser(parsedUser)
      fetchHistory()
    }
  }, [])

  const fetchHistory = async () => {
    setLoading(true)
    try {
      const data = await api.projects.list()
      setProjects(data || [])
    } catch (error) {
      console.error('Failed to fetch history:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleOpenAuth = () => {
    window.dispatchEvent(new CustomEvent('open-auth-modal', { 
      detail: { mode: 'login' } 
    }))
  }

  const handleSelect = (project: Project) => {
    setSelectedId(project.id)
    if (onSelectProject) {
      onSelectProject(project.id)
    } else {
      window.location.href = `/preview?projectId=${project.id}`
    }
  }

  if (!user) {
    return (
      <div className="flex flex-col items-center justify-center h-full px-6 py-12 text-center animate-in fade-in zoom-in duration-500">
        <div className="h-16 w-16 rounded-3xl bg-primary/10 flex items-center justify-center mb-6 border border-primary/20 shadow-xl shadow-primary/5">
          <Lock className="h-6 w-6 text-primary" />
        </div>
        <h3 className="text-sm font-bold text-foreground mb-2 uppercase tracking-widest">Access Restricted</h3>
        <p className="text-xs text-muted-foreground font-light leading-relaxed mb-8 max-w-[200px]">
          Sign in to unlock your persistent project vault and track your architectural evolution.
        </p>
        <Button 
          onClick={handleOpenAuth}
          className="w-full bg-primary/10 hover:bg-primary/20 border border-primary/30 text-primary text-[10px] font-black uppercase tracking-widest"
        >
          Sign In to Access
        </Button>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-full animate-pulse">
        <Clock className="h-8 w-8 text-muted-foreground/30 mb-4" />
        <p className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground/50">Retrieving Vault...</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-4 py-2 animate-in fade-in slide-in-from-right-4 duration-500">
      {projects.length === 0 ? (
        <div className="px-6 py-12 text-center">
          <History className="h-8 w-8 text-muted-foreground/20 mx-auto mb-4" />
          <p className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">No projects yet</p>
        </div>
      ) : (
        <div className="space-y-4 px-2">
          {projects.map((project) => (
            <div key={project.id} className="group relative">
               <div className="flex items-center gap-2 mb-1 px-4">
                  <div className="h-5 w-5 rounded-lg bg-secondary/50 flex items-center justify-center border border-white/5">
                    <span className="text-[10px] font-bold text-muted-foreground">{project.name.charAt(0)}</span>
                  </div>
                  <span className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground/70 group-hover:text-primary transition-colors cursor-default">
                    {project.name}
                  </span>
               </div>
               <div className="flex gap-3 px-4">
                  <CornerDownRight className="h-4 w-4 mt-1 text-muted-foreground/40 shrink-0" />
                  <button 
                    onClick={() => handleSelect(project)}
                    className={`flex-1 text-left rounded-xl glass-panel p-3 border transition-all duration-300 group/item ${
                      selectedId === project.id
                        ? 'bg-primary/15 border-primary/40 shadow-lg shadow-primary/10'
                        : 'bg-white/5 border-transparent hover:bg-primary/10 hover:border-primary/20'
                    }`}
                  >
                    <div className="flex justify-between items-center">
                      <span className="text-xs font-light text-foreground/80 group-hover/item:text-foreground">Project #{project.id}</span>
                      {selectedId === project.id && (
                        <span className="text-[9px] font-black text-primary uppercase tracking-widest">Active</span>
                      )}
                    </div>
                    {project.created_at && (
                      <p className="text-[9px] text-muted-foreground/50 mt-1">{new Date(project.created_at).toLocaleDateString()}</p>
                    )}
                  </button>
               </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
