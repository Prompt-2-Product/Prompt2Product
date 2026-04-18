const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://10.1.129.232:8002'

export async function fetchApi(endpoint: string, options: RequestInit = {}) {
    const url = `${API_BASE_URL}${endpoint}`
    const controller = new AbortController()
    const id = setTimeout(() => controller.abort(), 10000) // 10s timeout

    try {
        const response = await fetch(url, {
            ...options,
            signal: controller.signal,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
            },
        })
        clearTimeout(id)

        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
            throw new Error(error.detail || `API error: ${response.status}`)
        }

        return response.json()
    } catch (err) {
        clearTimeout(id)
        throw err
    }
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
        modify: (projectId: number, run_id: number, prompt: string) =>
            fetchApi(`/projects/${projectId}/runs/${run_id}/modify`, {
                method: 'POST',
                body: JSON.stringify({ prompt }),
            }),
        listFiles: (projectId: number, runId: number) =>
            fetchApi(`/projects/${projectId}/runs/${runId}/files`),
        getFileContent: (projectId: number, runId: number, filePath: string) =>
            fetchApi(`/projects/${projectId}/runs/${runId}/files/${filePath}`),
    },
    runs: {
        get: (runId: number) => fetchApi(`/runs/${runId}`),
        getLogs: (runId: number) => fetchApi(`/runs/${runId}/logs`),
    }
}
