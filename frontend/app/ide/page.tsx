'use client'

import { useState, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { Navigation } from '@/components/navigation'
import { Button } from '@/components/ui/button'
import { ResizablePanelGroup, ResizablePanel, ResizableHandle } from '@/components/ui/resizable'
import { ChevronRight, ChevronDown, File, Folder, ArrowLeft, Download, MessageSquare, Minimize2, Maximize2, Loader2 } from 'lucide-react'

interface FileNode {
  id: string
  name: string
  type: 'file' | 'folder'
  children?: FileNode[]
}

export default function IDEPage() {
  const router = useRouter()
  const [expandedFolders, setExpandedFolders] = useState<string[]>([])
  const [selectedFile, setSelectedFile] = useState<string | null>(null)
  const [fileContent, setFileContent] = useState<string>('')
  const [fileTree, setFileTree] = useState<FileNode[]>([])
  const [isLoadingTree, setIsLoadingTree] = useState(true)
  const [isLoadingContent, setIsLoadingContent] = useState(false)
  
  const [chatCollapsed, setChatCollapsed] = useState(false)
  const [explorerCollapsed, setExplorerCollapsed] = useState(false)
  const [consoleCollapsed, setConsoleCollapsed] = useState(false)
  const [projectInfo, setProjectInfo] = useState<{ projectId: number; runId: number; description: string; language: string; appType: string } | null>(null)
  const [chatMessage, setChatMessage] = useState('')
  const [chatHistory, setChatHistory] = useState<Array<{ role: 'user' | 'system'; content: string }>>([])
  const [isSubmittingChange, setIsSubmittingChange] = useState(false)

  const fetchFileTree = useCallback(async (projectId: number, runId: number) => {
    setIsLoadingTree(true)
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://10.1.129.232:8002';
      const res = await fetch(`${apiUrl}/projects/${projectId}/runs/${runId}/files`)
      if (res.ok) {
        const data = await res.json()
        setFileTree(data)
        // Auto-expand first folder if exists
        if (data.length > 0 && data[0].type === 'folder') {
          setExpandedFolders([data[0].id])
        }
      }
    } catch (err) {
      console.error('Failed to fetch file tree:', err)
    } finally {
      setIsLoadingTree(false)
    }
  }, [])

  const fetchFileContent = async (projectId: number, runId: number, filePath: string) => {
    setIsLoadingContent(true)
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://10.1.129.232:8002';
      const res = await fetch(`${apiUrl}/projects/${projectId}/runs/${runId}/files/${filePath}`)
      if (res.ok) {
        const data = await res.json()
        setFileContent(data.content)
      } else {
        setFileContent('// Error loading file content')
      }
    } catch (err) {
      console.error('Failed to fetch file content:', err)
      setFileContent('// Error connecting to backend')
    } finally {
      setIsLoadingContent(false)
    }
  }

  useEffect(() => {
    const stored = sessionStorage.getItem('projectInfo')
    if (stored) {
      const parsed = JSON.parse(stored)
      const { projectId, runId, description, language, appType } = parsed
      
      if (!projectId || !runId) {
        router.push('/describe')
        return
      }

      setProjectInfo({ projectId, runId, description, language, appType })
      setChatHistory([
        { role: 'user', content: description },
        { role: 'system', content: 'Your project is ready! How can I help you modify it?' }
      ])

      fetchFileTree(projectId, runId)
    } else {
      router.push('/describe')
    }
  }, [router, fetchFileTree])

  useEffect(() => {
    if (selectedFile && projectInfo) {
      fetchFileContent(projectInfo.projectId, projectInfo.runId, selectedFile)
    }
  }, [selectedFile, projectInfo])

  const toggleFolder = (folderId: string) => {
    setExpandedFolders((prev) =>
      prev.includes(folderId) ? prev.filter((f) => f !== folderId) : [...prev, folderId],
    )
  }

  const handleChatSubmit = async () => {
    const message = chatMessage.trim()
    if (!message || !projectInfo || isSubmittingChange) return

    setIsSubmittingChange(true)
    setChatHistory(prev => [...prev, { role: 'user', content: message }])
    setChatMessage('')

    try {
      console.log(`[FRONTEND][IDE] Queued modify request for run ${projectInfo.runId}`)
      sessionStorage.setItem('changeRequest', message)
      sessionStorage.setItem('generationFlow', 'modify')
      setChatHistory(prev => [...prev, { role: 'system', content: 'Queued. Opening generation console...' }])
      router.push('/generating')
    } catch (err) {
      setChatHistory(prev => [...prev, {
        role: 'system',
        content: `Failed to submit modification: ${err instanceof Error ? err.message : 'Unknown error'}`
      }])
    } finally {
      setIsSubmittingChange(false)
    }
  }

  const handleDownload = () => {
    if (projectInfo) {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://10.1.129.232:8002';
      window.open(`${apiUrl}/projects/${projectInfo.projectId}/runs/${projectInfo.runId}/download`, '_blank')
    }
  }

  const renderTree = (nodes: FileNode[]) => {
    return nodes.map((node) => (
      <div key={node.id}>
        {node.type === 'folder' ? (
          <div>
            <button
              onClick={() => toggleFolder(node.id)}
              className="flex w-full items-center gap-1.5 rounded px-2 py-1.5 text-xs text-foreground hover:bg-secondary transition-colors"
            >
              {expandedFolders.includes(node.id) ? (
                <ChevronDown className="h-3.5 w-3.5" />
              ) : (
                <ChevronRight className="h-3.5 w-3.5" />
              )}
              <Folder className="h-3.5 w-3.5 text-blue-400" />
              <span className="text-xs">{node.name}</span>
            </button>

            {expandedFolders.includes(node.id) && node.children && (
              <div className="ml-4 border-l border-border/50 ml-3.5 pl-1">
                {renderTree(node.children)}
              </div>
            )}
          </div>
        ) : (
          <button
            onClick={() => setSelectedFile(node.id)}
            className={`flex w-full items-center gap-2 rounded px-2 py-1 text-xs transition-colors ${
              selectedFile === node.id
                ? 'bg-primary/20 text-primary'
                : 'text-muted-foreground hover:bg-secondary'
            }`}
          >
            <File className="h-3.5 w-3.5" />
            <span className="text-xs">{node.name}</span>
          </button>
        )}
      </div>
    ))
  }

  return (
    <div className="h-screen bg-background text-foreground flex flex-col overflow-hidden">
      <Navigation />

      {/* Top Bar */}
      <div className="border-b border-border px-4 md:px-6 py-3 flex items-center justify-between bg-background flex-shrink-0" style={{ marginTop: '3rem' }}>
        <Button
          onClick={() => router.push('/preview')}
          variant="ghost"
          size="sm"
          className="text-foreground hover:bg-secondary/50 gap-2 font-medium"
        >
          <ArrowLeft className="h-4 w-4" />
          <span className="hidden sm:inline">Back to Project summary</span>
        </Button>
        <span className="text-xs md:text-sm text-foreground font-medium">Prompt2Product - IDE</span>
        <Button
          onClick={handleDownload}
          variant="ghost"
          size="sm"
          className="text-foreground hover:bg-secondary/50 gap-2 font-medium"
        >
          <Download className="h-4 w-4" />
          <span className="hidden sm:inline">Download</span>
        </Button>
      </div>

      {/* Main IDE Layout */}
      <main className="flex-1 overflow-hidden relative min-h-0">
        <ResizablePanelGroup direction="horizontal" className="h-full w-full">
          {/* Left: Chat Panel */}
          {!chatCollapsed && (
            <>
              <ResizablePanel defaultSize={20} minSize={15} maxSize={40} collapsible className="border-r border-border bg-background flex flex-col min-w-0">
                {/* Chat Header */}
                <div className="border-b border-border px-4 py-2.5 flex items-center justify-between bg-background flex-shrink-0">
                  <div className="flex items-center gap-2">
                    <MessageSquare className="h-4 w-4 text-muted-foreground" />
                    <span className="text-xs font-semibold text-foreground uppercase tracking-wider">Chat</span>
                  </div>
                  <button
                    onClick={() => setChatCollapsed(true)}
                    className="p-1 hover:bg-secondary/50 rounded transition-colors"
                    aria-label="Collapse chat"
                  >
                    <Minimize2 className="h-3 w-3 text-muted-foreground" />
                  </button>
                </div>

                {/* Chat Messages */}
                <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4 custom-scrollbar">
                  {chatHistory.map((msg, index) => (
                    <div key={index} className="flex flex-col gap-2">
                      <div className="flex items-center gap-2">
                        {msg.role === 'user' ? (
                          <>
                            <div className="h-5 w-5 rounded-full bg-primary/20 flex items-center justify-center flex-shrink-0">
                              <span className="text-xs font-semibold text-primary">U</span>
                            </div>
                            <span className="text-xs font-medium text-muted-foreground">You</span>
                          </>
                        ) : (
                          <>
                            <div className="h-5 w-5 rounded-full bg-gradient-to-r from-blue-500 to-cyan-500 flex items-center justify-center flex-shrink-0">
                              <span className="text-xs font-semibold text-white">P</span>
                            </div>
                            <span className="text-xs font-medium text-muted-foreground">Prompt2Product</span>
                          </>
                        )}
                      </div>
                      <div className={`ml-7 rounded-lg p-3 text-xs leading-relaxed whitespace-pre-wrap break-words ${
                        msg.role === 'user' 
                          ? 'bg-secondary/60 border border-border/60 text-foreground' 
                          : 'bg-primary/15 border border-primary/30 text-foreground'
                      }`}>
                        {msg.content}
                      </div>
                    </div>
                  ))}
                </div>

                {/* Chat Input */}
                <div className="border-t border-border px-4 py-2.5 bg-background flex-shrink-0">
                  <div className="flex gap-2">
                    <textarea
                      value={chatMessage}
                      onChange={(e) => setChatMessage(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' && !e.shiftKey) {
                          e.preventDefault()
                          handleChatSubmit()
                        }
                      }}
                      placeholder="Ask about your project..."
                      className="flex-1 min-h-[50px] max-h-[80px] rounded-lg bg-secondary/40 border border-border/60 px-3 py-2 text-xs text-foreground placeholder:text-muted-foreground resize-none focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                      rows={2}
                    />
                    <Button
                      onClick={handleChatSubmit}
                      disabled={!chatMessage.trim() || isSubmittingChange}
                      size="sm"
                      className="bg-gradient-to-r from-blue-500 via-blue-400 to-cyan-500 hover:from-blue-600 hover:via-blue-500 hover:to-cyan-600 text-white font-semibold disabled:opacity-50 disabled:cursor-not-allowed px-3"
                    >
                      {isSubmittingChange ? 'Sending...' : 'Send'}
                    </Button>
                  </div>
                </div>
              </ResizablePanel>
              <ResizableHandle withHandle />
            </>
          )}

          {/* Middle: Explorer Panel */}
          {!explorerCollapsed && (
            <>
              <ResizablePanel defaultSize={20} minSize={15} maxSize={35} collapsible className="border-r border-border bg-background flex flex-col min-w-0">
                {/* Explorer Header */}
                <div className="border-b border-border px-4 py-2.5 flex items-center justify-between bg-background flex-shrink-0">
                  <span className="text-xs font-semibold text-foreground uppercase tracking-wider">Explorer</span>
                  <button
                    onClick={() => setExplorerCollapsed(true)}
                    className="p-1 hover:bg-secondary/50 rounded transition-colors"
                    aria-label="Collapse explorer"
                  >
                    <Minimize2 className="h-3 w-3 text-muted-foreground" />
                  </button>
                </div>

                {/* File Tree */}
                <div className="flex-1 overflow-y-auto p-2 custom-scrollbar">
                  {isLoadingTree ? (
                    <div className="flex flex-col items-center justify-center p-4 gap-2 text-muted-foreground">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span className="text-[10px]">Loading files...</span>
                    </div>
                  ) : (
                    renderTree(fileTree)
                  )}
                  {!isLoadingTree && fileTree.length === 0 && (
                    <div className="p-4 text-center text-muted-foreground text-[10px]">
                      No files generated yet.
                    </div>
                  )}
                </div>
              </ResizablePanel>
              <ResizableHandle withHandle />
            </>
          )}

          {/* Right: Code Editor & Console */}
          <ResizablePanel defaultSize={chatCollapsed && explorerCollapsed ? 100 : chatCollapsed || explorerCollapsed ? 80 : 60} minSize={30} className="min-w-0">
            <ResizablePanelGroup direction="vertical" className="h-full w-full">
              {/* Code Editor */}
              <ResizablePanel defaultSize={70} minSize={40} className="flex flex-col bg-background min-h-0">
                {/* Editor Header */}
                <div className="border-b border-border px-4 py-2 flex items-center gap-2 bg-background flex-shrink-0">
                  <File className="h-3.5 w-3.5 text-blue-400" />
                  <span className="text-xs font-medium text-foreground">{selectedFile || 'Select a file'}</span>
                  {isLoadingContent && <Loader2 className="h-3 w-3 animate-spin text-muted-foreground ml-auto" />}
                </div>

                {/* Code Content */}
                <div className="flex-1 overflow-auto font-mono text-xs min-h-0 relative">
                  {!selectedFile ? (
                    <div className="h-full flex items-center justify-center text-muted-foreground/40">
                      <div className="text-center">
                        <Code2 className="h-12 w-12 mx-auto mb-2 opacity-10" />
                        <p className="text-sm">Select a file to view code</p>
                      </div>
                    </div>
                  ) : (
                    <div className="flex h-full min-h-0">
                      <div className="w-10 bg-secondary/50 text-muted-foreground py-3 px-2 text-right select-none border-r border-border text-[10px] flex-shrink-0">
                        {fileContent.split('\n').map((_, i) => (
                          <div key={i} className="leading-5">{i + 1}</div>
                        ))}
                      </div>
                      <div className="flex-1 py-3 px-4 text-foreground bg-background overflow-auto min-w-0">
                        <pre className="whitespace-pre-wrap break-words leading-5">{fileContent || (isLoadingContent ? '' : '// No content')}</pre>
                      </div>
                    </div>
                  )}
                </div>
              </ResizablePanel>

              <ResizableHandle withHandle />

              {/* Console */}
              {!consoleCollapsed && (
                <ResizablePanel defaultSize={30} minSize={15} maxSize={60} collapsible className="flex flex-col bg-background border-t border-border min-h-0">
                  {/* Console Header */}
                  <div className="border-b border-border px-4 py-2 flex items-center justify-between bg-background flex-shrink-0">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-semibold text-foreground uppercase tracking-wider">Console</span>
                      <div className="flex items-center gap-1.5">
                        <div className="h-1.5 w-1.5 rounded-full bg-green-500"></div>
                        <span className="text-[10px] text-green-400 font-medium">System Ready</span>
                      </div>
                    </div>
                    <button
                      onClick={() => setConsoleCollapsed(true)}
                      className="p-1 hover:bg-secondary/50 rounded transition-colors"
                      aria-label="Collapse console"
                    >
                      <Minimize2 className="h-3 w-3 text-muted-foreground" />
                    </button>
                  </div>

                  {/* Console Content */}
                  <div className="flex-1 overflow-y-auto font-mono text-[10px] p-4 space-y-1 custom-scrollbar">
                    <div className="text-blue-400">[SYSTEM] IDE initialized</div>
                    <div className="text-green-400">[INFO] Successfully connected to workspace storage</div>
                    {projectInfo && (
                      <div className="text-muted-foreground">[DEBUG] Loaded Project ID: {projectInfo.projectId}, Run ID: {projectInfo.runId}</div>
                    )}
                    <div className="text-green-400">[SUCCESS] File system synchronization complete</div>
                    <div className="mt-2 text-foreground opacity-50">Watching for changes...</div>
                  </div>
                </ResizablePanel>
              )}
            </ResizablePanelGroup>
          </ResizablePanel>
        </ResizablePanelGroup>
      </main>

      {/* Collapsed Panel Buttons - Left Side */}
      <div className="fixed left-0 z-20 flex flex-col gap-2" style={{ top: 'calc(3rem + 3.5rem + 50%)', transform: 'translateY(-50%)' }}>
        {chatCollapsed && (
          <button
            onClick={() => setChatCollapsed(false)}
            className="bg-background border-r border-t border-b border-border px-2 py-4 rounded-r-lg hover:bg-secondary/50 transition-colors shadow-lg"
            aria-label="Expand chat"
          >
            <MessageSquare className="h-4 w-4 text-muted-foreground" />
          </button>
        )}
        {explorerCollapsed && !chatCollapsed && (
          <button
            onClick={() => setExplorerCollapsed(false)}
            className="bg-background border-r border-t border-b border-border px-2 py-4 rounded-r-lg hover:bg-secondary/50 transition-colors shadow-lg"
            aria-label="Expand explorer"
          >
            <Folder className="h-4 w-4 text-muted-foreground" />
          </button>
        )}
      </div>
      
      {/* Collapsed Panel Button - Bottom Right (Console) */}
      {consoleCollapsed && (
        <button
          onClick={() => setConsoleCollapsed(false)}
          className="fixed bottom-0 right-0 z-20 bg-background border-l border-t border-r border-border px-4 py-2 rounded-t-lg hover:bg-secondary/50 transition-colors shadow-lg"
          aria-label="Expand console"
        >
          <Maximize2 className="h-4 w-4 text-muted-foreground" />
        </button>
      )}
    </div>
  )
}

function Code2(props: any) {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="m18 16 4-4-4-4" />
      <path d="m6 8-4 4 4 4" />
      <path d="m14.5 4-5 16" />
    </svg>
  )
}
