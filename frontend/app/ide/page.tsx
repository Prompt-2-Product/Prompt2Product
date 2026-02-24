'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Navigation } from '@/components/navigation'
import { Button } from '@/components/ui/button'
import { ResizablePanelGroup, ResizablePanel, ResizableHandle } from '@/components/ui/resizable'
import { ChevronRight, ChevronDown, File, Folder, ArrowLeft, Download, MessageSquare, X, Minimize2, Maximize2 } from 'lucide-react'

const PYTHON_CODE = `def hello_world():
    print("Hello, World!")

def greet(name):
    return f"Hello, {name}!"

class Calculator:
    @staticmethod
    def add(a, b):
        return a + b
    
    @staticmethod
    def multiply(a, b):
        return a * b

if __name__ == "__main__":
    print(greet("Prompt2Product"))
    calc = Calculator()
    print(calc.add(10, 5))
    print(calc.multiply(3, 4))`

export default function IDEPage() {
  const router = useRouter()
  const [expandedFolders, setExpandedFolders] = useState<string[]>(['src', 'config'])
  const [selectedFile, setSelectedFile] = useState<string>('main.py')
  const [chatCollapsed, setChatCollapsed] = useState(false)
  const [explorerCollapsed, setExplorerCollapsed] = useState(false)
  const [consoleCollapsed, setConsoleCollapsed] = useState(false)
  const [projectInfo, setProjectInfo] = useState<{ description: string; language: string; appType: string } | null>(null)
  const [chatMessage, setChatMessage] = useState('')
  const [chatHistory, setChatHistory] = useState<Array<{ role: 'user' | 'system'; content: string }>>([])

  useEffect(() => {
    // Load project info from sessionStorage
    const stored = sessionStorage.getItem('projectInfo')
    if (stored) {
      const parsed = JSON.parse(stored)
      setProjectInfo({ description: parsed.description, language: parsed.language, appType: parsed.appType })
      setChatHistory([
        { role: 'user', content: parsed.description },
        { role: 'system', content: 'Your project is ready! How can I help you modify it?' }
      ])
    }
  }, [])

  const toggleFolder = (folderName: string) => {
    setExpandedFolders((prev) =>
      prev.includes(folderName) ? prev.filter((f) => f !== folderName) : [...prev, folderName],
    )
  }

  const handleChatSubmit = () => {
    if (chatMessage.trim()) {
      setChatHistory(prev => [...prev, { role: 'user', content: chatMessage }])
      setChatMessage('')
      // In production, this would send to backend
      setTimeout(() => {
        setChatHistory(prev => [...prev, { role: 'system', content: 'I understand. Let me help you with that change.' }])
      }, 1000)
    }
  }

  const handleDownload = () => {
    // Mock download - in production, this would call the backend API
    if (projectInfo) {
      alert('Downloading project...\n\nIn production, this would download the generated project as a ZIP file.')
    }
  }

  const fileTree = [
    {
      id: 'src',
      name: 'src',
      type: 'folder' as const,
      children: [
        { id: 'main.py', name: 'main.py', type: 'file' as const },
        { id: 'utils.py', name: 'utils.py', type: 'file' as const },
        { id: 'config.py', name: 'config.py', type: 'file' as const },
      ],
    },
    {
      id: 'config',
      name: 'config',
      type: 'folder' as const,
      children: [
        { id: 'settings.json', name: 'settings.json', type: 'file' as const },
        { id: 'requirements.txt', name: 'requirements.txt', type: 'file' as const },
      ],
    },
    { id: 'README.md', name: 'README.md', type: 'file' as const },
  ]

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
        <span className="text-xs md:text-sm text-foreground font-medium">Prompt2Product - Advanced Mode</span>
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
                      disabled={!chatMessage.trim()}
                      size="sm"
                      className="bg-gradient-to-r from-blue-500 via-blue-400 to-cyan-500 hover:from-blue-600 hover:via-blue-500 hover:to-cyan-600 text-white font-semibold disabled:opacity-50 disabled:cursor-not-allowed px-3"
                    >
                      Send
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
                  {fileTree.map((item) => (
                    <div key={item.id}>
                      {item.type === 'folder' ? (
                        <div>
                          <button
                            onClick={() => toggleFolder(item.id)}
                            className="flex w-full items-center gap-1.5 rounded px-2 py-1.5 text-xs text-foreground hover:bg-secondary transition-colors"
                          >
                            {expandedFolders.includes(item.id) ? (
                              <ChevronDown className="h-3.5 w-3.5" />
                            ) : (
                              <ChevronRight className="h-3.5 w-3.5" />
                            )}
                            <Folder className="h-3.5 w-3.5 text-blue-400" />
                            <span className="text-xs">{item.name}</span>
                          </button>

                          {expandedFolders.includes(item.id) && item.children && (
                            <div className="ml-4">
                              {item.children.map((child) => (
                                <button
                                  key={child.id}
                                  onClick={() => setSelectedFile(child.id)}
                                  className={`flex w-full items-center gap-2 rounded px-2 py-1 text-xs transition-colors ${
                                    selectedFile === child.id
                                      ? 'bg-primary/20 text-primary'
                                      : 'text-muted-foreground hover:bg-secondary'
                                  }`}
                                >
                                  <File className="h-3.5 w-3.5" />
                                  <span className="text-xs">{child.name}</span>
                                </button>
                              ))}
                            </div>
                          )}
                        </div>
                      ) : (
                        <button
                          onClick={() => setSelectedFile(item.id)}
                          className={`flex w-full items-center gap-2 rounded px-2 py-1 text-xs transition-colors ${
                            selectedFile === item.id ? 'bg-primary/20 text-primary' : 'text-muted-foreground hover:bg-secondary'
                          }`}
                        >
                          <File className="h-3.5 w-3.5" />
                          <span className="text-xs">{item.name}</span>
                        </button>
                      )}
                    </div>
                  ))}
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
                  <span className="text-xs font-medium text-foreground">{selectedFile}</span>
                </div>

                {/* Code Content */}
                <div className="flex-1 overflow-auto font-mono text-xs min-h-0">
                  <div className="flex h-full min-h-0">
                    <div className="w-10 bg-secondary/50 text-muted-foreground py-3 px-2 text-right select-none border-r border-border text-[10px] flex-shrink-0">
                      {PYTHON_CODE.split('\n').map((_, i) => (
                        <div key={i} className="leading-5">{i + 1}</div>
                      ))}
                    </div>
                    <div className="flex-1 py-3 px-4 text-foreground bg-background overflow-auto min-w-0">
                      <pre className="whitespace-pre-wrap break-words leading-5">{PYTHON_CODE}</pre>
                    </div>
                  </div>
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
                        <span className="text-[10px] text-green-400 font-medium">Running</span>
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
                    <div className="text-green-400">[INFO] Project loaded successfully</div>
                    <div className="text-green-400">[INFO] Dependencies installed</div>
                    <div className="text-green-400">[INFO] Starting development server on port 3000</div>
                    <div className="text-green-400">[INFO] Hot reload enabled</div>
                    <div className="text-green-400">[INFO] Watching for file changes...</div>
                    <div className="text-green-400 mt-2">&gt; python main.py</div>
                    <div className="text-foreground">Hello, Prompt2Product!</div>
                    <div className="text-foreground">15</div>
                    <div className="text-foreground">12</div>
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
