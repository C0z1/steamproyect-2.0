import type {
  Game, SearchResult, PriceHistoryResponse,
  GameStatsResponse, PredictionResponse, HealthResponse
} from './types'

const BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

async function apiFetch<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    next: { revalidate: 60 },
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }
  return res.json()
}

// ── Health ────────────────────────────────────────────────────────────────────

export const getHealth = () => apiFetch<HealthResponse>('/health')

// ── Games ─────────────────────────────────────────────────────────────────────

export const searchGames = (q: string) =>
  apiFetch<SearchResult[]>(`/games/search?q=${encodeURIComponent(q)}`)

export const listGames = (limit = 50, offset = 0) =>
  apiFetch<Game[]>(`/games?limit=${limit}&offset=${offset}`)

export const getGameStats = (gameId: string) =>
  apiFetch<GameStatsResponse>(`/games/${gameId}`)

// ── Prices ────────────────────────────────────────────────────────────────────

export const getPriceHistory = (gameId: string, since?: string) =>
  apiFetch<PriceHistoryResponse>(
    `/prices/${gameId}/history${since ? `?since=${since}` : ''}`
  )

// ── Prediction ────────────────────────────────────────────────────────────────

export const getPrediction = (gameId: string, forceRefresh = false) =>
  apiFetch<PredictionResponse>(
    `/predict/${gameId}${forceRefresh ? '?force_refresh=true' : ''}`
  )

// ── Sync ──────────────────────────────────────────────────────────────────────

export const syncGame = async (appid: number) => {
  const res = await fetch(`${BASE}/sync/game/${appid}`, { method: 'POST' })
  if (!res.ok) throw new Error(`Sync failed: ${res.statusText}`)
  return res.json()
}
