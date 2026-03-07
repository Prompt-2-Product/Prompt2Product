const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000'

export async function fetchApi(endpoint: string, options: RequestInit = {}) {
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
    },
    runs: {
        get: (runId: number) => fetchApi(`/runs/${runId}`),
        getLogs: (runId: number) => fetchApi(`/runs/${runId}/logs`),
    }
}
