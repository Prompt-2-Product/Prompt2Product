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
        modify: (projectId: number, runId: number, prompt: string) =>
            fetchApi(`/projects/${projectId}/runs/${runId}/modify`, {
                method: 'POST',
                body: JSON.stringify({ prompt }),
            }),
    },
    runs: {
        get: (runId: number) => fetchApi(`/runs/${runId}`),
        getLogs: (runId: number) => fetchApi(`/runs/${runId}/logs`),
    },
    generateProject: async (info: any, onLog: (log: string) => void) => {
        return pollLogs(info.runId, onLog);
    },
    submitChangeRequest: async (prompt: string, onLog: (log: string) => void) => {
        const projectInfoString = sessionStorage.getItem('projectInfo');
        if (!projectInfoString) throw new Error("No existing project found to modify.");
        const info = JSON.parse(projectInfoString);
        
        // Trigger modification on current project/run
        await api.projects.modify(info.projectId, info.runId, prompt);
        return pollLogs(info.runId, onLog);
    }
}

async function pollLogs(runId: number, onLog: (log: string) => void) {
    let seenCount = 0;
    let finished = false;

    while (!finished) {
        try {
            const [run, logs] = await Promise.all([
                api.runs.get(runId),
                api.runs.getLogs(runId)
            ]);

            // New logs available?
            if (Array.isArray(logs) && logs.length > seenCount) {
                logs.slice(seenCount).forEach((l: any) => {
                    const message = typeof l === 'string' ? l : (l.message || JSON.stringify(l));
                    onLog(message);
                });
                seenCount = logs.length;
            }

            // Check terminal states
            const s = run.status?.toLowerCase();
            if (s === 'completed' || s === 'success' || s === 'failed') {
                finished = true;
                if (s === 'failed') throw new Error("Generation process failed on backend.");
            }
        } catch (err) {
            console.error("[API] Polling error:", err);
            // Non-terminal errors are ignored to keep polling alive
        }

        if (!finished) {
            await new Promise(r => setTimeout(r, 2000));
        }
    }
}
