import { isFrontendOnly } from './frontend-only'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000'

function mockFetchApi(endpoint: string, options: RequestInit = {}) {
    const method = (options.method || 'GET').toUpperCase()

    if (endpoint === '/projects' && method === 'POST') {
        const body = options.body ? JSON.parse(String(options.body)) as { name?: string } : {}
        return Promise.resolve({ id: 1, name: body.name || 'Project' })
    }

    if (/^\/projects\/\d+\/runs$/.test(endpoint) && method === 'POST') {
        return Promise.resolve({ run_id: 1, status: 'queued', attempts: 0 })
    }

    if (/^\/projects\/\d+\/runs\/\d+\/modify$/.test(endpoint) && method === 'POST') {
        return Promise.resolve({ status: 'accepted' })
    }

    if (/^\/runs\/\d+$/.test(endpoint) && method === 'GET') {
        return Promise.resolve({
            id: 1,
            project_id: 1,
            status: 'success',
            entrypoint: 'app.main:app',
            attempts: 0,
        })
    }

    if (/^\/runs\/\d+\/logs$/.test(endpoint) && method === 'GET') {
        return Promise.resolve([])
    }

    return Promise.reject(new Error(`Frontend-only mode: no mock for ${method} ${endpoint}`))
}

export async function fetchApi(endpoint: string, options: RequestInit = {}) {
    if (isFrontendOnly) {
        return mockFetchApi(endpoint, options)
    }

    const url = `${API_BASE_URL}${endpoint}`
    const response = await fetch(url, {
        ...options,
        headers: {
            'Content-Type': 'application/json',
            ...options.headers,
        },
    })

    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
        throw new Error(error.detail || `API error: ${response.status}`)
    }

    return response.json()
}

export const api = {
    projects: {
        create: (name: string) => fetchApi('/projects', {
            method: 'POST',
            body: JSON.stringify({ name }),
        }),
        list: () => fetchApi('/projects'),
        startRun: (projectId: number, prompt: string, entrypoint: string = 'app.main:app') =>
            fetchApi(`/projects/${projectId}/runs`, {
                method: 'POST',
                body: JSON.stringify({ prompt, entrypoint }),
            }),
        downloadUrl: (projectId: number, runId: number) =>
            `${API_BASE_URL}/projects/${projectId}/runs/${runId}/download`,
        modify: (projectId: number, runId: number, prompt: string) =>
            fetchApi(`/projects/${projectId}/runs/${runId}/modify`, {
                method: 'POST',
                body: JSON.stringify({ prompt }),
            }),
    },
    runs: {
        get: (runId: number) => fetchApi(`/runs/${runId}`),
        getLogs: (runId: number) => fetchApi(`/runs/${runId}/logs`),
    }
}
