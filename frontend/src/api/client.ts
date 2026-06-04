export const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1'

/** 获取当前用户 ID（从 localStorage，避免 Pinia 未初始化问题） */
function getCurrentUserId(): number | null {
  const stored = localStorage.getItem('active_user_id')
  return stored ? parseInt(stored) : null
}

export async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const userId = getCurrentUserId()

  // 自动附加 user_id 到请求头
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...((options?.headers as Record<string, string>) || {}),
  }
  if (userId !== null) {
    headers['X-User-Id'] = String(userId)
  }

  const resp = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  })
  if (!resp.ok) {
    const text = await resp.text()
    throw new Error(`HTTP ${resp.status}: ${text}`)
  }
  if (resp.status === 204) {
    return undefined as unknown as T
  }
  return resp.json() as Promise<T>
}

const client = {
  get: <T>(path: string) =>
    request<T>(path, { method: 'GET' }).then(data => ({ data })),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'POST', body: body ? JSON.stringify(body) : undefined }).then(data => ({ data })),
  put: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'PUT', body: body ? JSON.stringify(body) : undefined }).then(data => ({ data })),
  delete: <T>(path: string) =>
    request<T>(path, { method: 'DELETE' }).then(data => ({ data })),
}

export default client
