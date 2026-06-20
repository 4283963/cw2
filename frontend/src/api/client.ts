// 后端 API 客户端：通过 HTTP 与 FastAPI 树状路由联动
import type { SampleData, SimulateRequest, SimulateResult } from '../types'

const BASE = '/api'

async function http<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init)
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(`HTTP ${res.status}: ${text}`)
  }
  return res.json() as Promise<T>
}

export function getSample(): Promise<SampleData> {
  return http<SampleData>(`${BASE}/sample`)
}

export function runSimulate(req: SimulateRequest): Promise<SimulateResult> {
  return http<SimulateResult>(`${BASE}/simulate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
}
