/**
 * Set NEXT_PUBLIC_FRONTEND_ONLY=true in .env.local to run the UI without the API.
 * Remove it (or set to false) when the backend should be used again.
 */
export const isFrontendOnly =
  process.env.NEXT_PUBLIC_FRONTEND_ONLY === '1' ||
  process.env.NEXT_PUBLIC_FRONTEND_ONLY === 'true'

export const DEMO_PROJECT_INFO = {
  description: 'Demo project (UI preview — backend disconnected)',
  language: 'TypeScript',
  appType: 'Web App',
  additionalInstructions: '',
  projectId: 1,
  runId: 1,
}

export function seedDemoProjectInfoIfNeeded() {
  if (!isFrontendOnly) return
  if (typeof window === 'undefined') return
  if (!sessionStorage.getItem('projectInfo')) {
    sessionStorage.setItem('projectInfo', JSON.stringify(DEMO_PROJECT_INFO))
  }
}
