const API_BASE = '/agent-ops/api'

export type User = {
  id: number
  username: string
  email: string | null
  display_name: string
  created_at: string
}

export type SocialAccount = {
  id: number
  platform: string
  handle: string
  display_name: string
  avatar_url: string
  bio: string
  profile_url: string
  tier: 'basic' | 'standard' | 'premium'
  price: number
  followers: number
  status: string
  owner_user_id: number | null
}

export type DashboardStats = {
  total_accounts_owned: number
  available_market: number
  active_schedules: number
  batch_tasks: number
  recent_logs: number
}

export type Schedule = {
  id: number
  account_id: number
  start_time: string
  duration_minutes: number
  enabled: boolean
  created_at: string
}

export type BatchTask = {
  id: number
  name: string
  prompt_text: string
  start_time: string
  duration_minutes: number
  enabled: boolean
  created_at: string
  account_ids: number[]
}

export type ExecutionLog = {
  id: number
  account_id: number
  step: string
  message: string
  screenshot_url: string | null
  status: string
  created_at: string
  account_handle?: string
}

function authHeaders(token: string | null): HeadersInit {
  const headers: HeadersInit = { 'Content-Type': 'application/json' }
  if (token) headers.Authorization = `Bearer ${token}`
  return headers
}

async function request<T>(path: string, token: string | null, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { ...authHeaders(token), ...(init?.headers || {}) },
  })
  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = await res.json()
      detail = body.detail || JSON.stringify(body)
    } catch {
      /* ignore */
    }
    throw new Error(typeof detail === 'string' ? detail : 'Request failed')
  }
  if (res.status === 204) return undefined as T
  return res.json()
}

export const api = {
  register: (body: { username: string; password: string; email?: string; display_name: string }) =>
    request<{ access_token: string; user: User }>('/auth/register', null, {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  login: (body: { username: string; password: string }) =>
    request<{ access_token: string; user: User }>('/auth/login', null, {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  me: (token: string) => request<User>('/auth/me', token),
  dashboard: (token: string) => request<DashboardStats>('/dashboard', token),
  marketAccounts: (token: string, skip = 0, limit = 50) =>
    request<SocialAccount[]>(`/market/accounts?skip=${skip}&limit=${limit}`, token),
  myAccounts: (token: string) => request<SocialAccount[]>('/my/accounts', token),
  purchase: (token: string, accountId: number) =>
    request<SocialAccount>(`/my/accounts/${accountId}/purchase`, token, { method: 'POST' }),
  getPrompt: (token: string, accountId: number) =>
    request<{ persona: string; prompt_text: string } | null>(`/my/accounts/${accountId}/prompt`, token),
  savePrompt: (token: string, accountId: number, body: { persona: string; prompt_text: string }) =>
    request(`/my/accounts/${accountId}/prompt`, token, { method: 'PUT', body: JSON.stringify(body) }),
  listSchedules: (token: string, accountId: number) =>
    request<Schedule[]>(`/my/accounts/${accountId}/schedules`, token),
  createSchedule: (
    token: string,
    accountId: number,
    body: { start_time: string; duration_minutes: number; enabled: boolean },
  ) =>
    request<Schedule>(`/my/accounts/${accountId}/schedules`, token, {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  deleteSchedule: (token: string, accountId: number, scheduleId: number) =>
    request(`/my/accounts/${accountId}/schedules/${scheduleId}`, token, { method: 'DELETE' }),
  batchTasks: (token: string) => request<BatchTask[]>('/batch-tasks', token),
  createBatchTask: (
    token: string,
    body: {
      name: string
      prompt_text: string
      start_time: string
      duration_minutes: number
      account_ids: number[]
      enabled: boolean
    },
  ) =>
    request<BatchTask>('/batch-tasks', token, { method: 'POST', body: JSON.stringify(body) }),
  executionLogs: (token: string) => request<ExecutionLog[]>('/execution-logs', token),
}
