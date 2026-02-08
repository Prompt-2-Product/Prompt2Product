'use client'

import { useState, useEffect } from 'react'
import { Loader, X } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface ProjectChatProps {
  isOpen: boolean
  onClose: () => void
  projectInfo: {
    description: string
    language: string
    appType: string
  } | null
  initialMessage?: string
  onSubmit?: (message: string) => void
  isGenerating?: boolean
}

export function ProjectChat({ isOpen, onClose, projectInfo, initialMessage, onSubmit, isGenerating = false }: ProjectChatProps) {
  const [message, setMessage] = useState(initialMessage || '')
  const [chatHistory, setChatHistory] = useState<Array<{ role: 'user' | 'system'; content: string }>>([])

  useEffect(() => {
    if (isOpen && projectInfo) {
      // Initialize chat with project description
      setChatHistory([
        { role: 'user', content: projectInfo.description },
        { role: 'system', content: 'How would you like to modify this project?' }
      ])
      setMessage(initialMessage || '')
    }
  }, [isOpen, projectInfo, initialMessage])

  const handleSubmit = () => {
    if (message.trim() && onSubmit) {
      setChatHistory(prev => [
        ...prev,
        { role: 'user', content: message }
      ])
      onSubmit(message)
      setMessage('')
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm animate-in fade-in duration-300">
      <div className="w-full h-full lg:w-[90vw] lg:h-[90vh] lg:max-w-6xl lg:max-h-[800px] bg-background border border-border/50 rounded-lg lg:rounded-xl shadow-2xl flex flex-col overflow-hidden animate-in zoom-in-95 duration-300">
        {/* Chat Header */}
        <div className="px-5 py-4 border-b border-border/50 flex-shrink-0 bg-background flex items-center justify-between">
          <div className="flex-1">
            <h2 className="text-base font-semibold text-foreground mb-1">Request Changes</h2>
            {projectInfo && (
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-xs px-2 py-0.5 rounded-md bg-primary/10 text-primary border border-primary/20">
                  {projectInfo.language}
                </span>
                <span className="text-xs px-2 py-0.5 rounded-md bg-secondary/50 text-foreground border border-border/50">
                  {projectInfo.appType}
                </span>
              </div>
            )}
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-secondary/50 rounded-lg transition-colors"
            aria-label="Close chat"
          >
            <X className="h-5 w-5 text-foreground" />
          </button>
        </div>

        {/* Chat Messages Area */}
        <div className="flex-1 overflow-y-auto px-5 py-4 space-y-5 custom-scrollbar min-h-0">
          {chatHistory.map((msg, index) => (
            <div key={index} className="flex flex-col gap-2.5">
              <div className="flex items-center gap-2">
                {msg.role === 'user' ? (
                  <>
                    <div className="h-6 w-6 rounded-full bg-primary/20 flex items-center justify-center">
                      <span className="text-xs font-semibold text-primary">U</span>
                    </div>
                    <span className="text-xs font-medium text-muted-foreground">You</span>
                  </>
                ) : (
                  <>
                    <div className="h-6 w-6 rounded-full bg-gradient-to-r from-blue-500 to-cyan-500 flex items-center justify-center">
                      <span className="text-xs font-semibold text-white">P</span>
                    </div>
                    <span className="text-xs font-medium text-muted-foreground">Prompt2Product</span>
                  </>
                )}
              </div>
              <div className={`ml-8 rounded-xl p-4 text-sm leading-relaxed whitespace-pre-wrap break-words shadow-sm ${
                msg.role === 'user' 
                  ? 'bg-secondary/60 border border-border/60 text-foreground' 
                  : 'bg-primary/15 border border-primary/30 text-foreground'
              }`}>
                {msg.content}
              </div>
            </div>
          ))}
          {isGenerating && (
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
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault()
                  handleSubmit()
                }
              }}
              placeholder="Describe the changes you want..."
              disabled={isGenerating}
              className="flex-1 min-h-[90px] rounded-xl bg-secondary/40 border border-border/60 px-4 py-3 text-sm text-foreground placeholder:text-muted-foreground resize-none focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent disabled:cursor-not-allowed disabled:opacity-70"
              rows={3}
            />
            <div className="flex flex-col gap-2">
              <Button
                onClick={handleSubmit}
                disabled={!message.trim() || isGenerating}
                className="bg-gradient-to-r from-blue-500 via-blue-400 to-cyan-500 hover:from-blue-600 hover:via-blue-500 hover:to-cyan-600 text-white font-semibold shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 px-6 h-full"
              >
                {isGenerating ? (
                  <Loader className="h-4 w-4 animate-spin" />
                ) : (
                  'Send'
                )}
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

