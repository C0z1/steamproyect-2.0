import type {
  Game, SearchResult, PriceHistoryResponse, GameStatsResponse,
  PredictionResponse, CurrentPricesResponse, TopDeal, BuySignal, OverviewStats
} from './types'

const BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

async function apiFetch<T>(path: string, revalidate = 60): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { next: { revalidate } })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }
  return res.json()
}

// Health
export const getHealth = () => apiFetch<{ status: string; db: string; model: string }>('/health')

// Stats
export const getOverviewStats = () => apiFetch<OverviewStats>('/stats/overview', 30)

// Games
export const searchGames = (q: string) =>
  apiFetch<SearchResult[]>(`/games/search?q=${encodeURIComponent(q)}`, 0)

export const listGames = (limit = 50, offset = 0) =>
  apiFetch<Game[]>(`/games?limit=${limit}&offset=${offset}`, 30)

export const getGameStats = (gameId: string) =>
  apiFetch<GameStatsResponse>(`/games/${gameId}`, 60)

export const getTopDeals = (limit = 12) =>
  apiFetch<TopDeal[]>(`/games/top/deals?limit=${limit}`, 30)

export const getTopBuySignals = (limit = 12) =>
  apiFetch<BuySignal[]>(`/games/top/buy?limit=${limit}`, 30)

export const getCurrentPrices = (gameId: string) =>
  apiFetch<CurrentPricesResponse>(`/games/${gameId}/current-prices`, 10)

// Prices
export const getPriceHistory = (gameId: string, since?: string) =>
  apiFetch<PriceHistoryResponse>(`/prices/${gameId}/history${since ? `?since=${since}` : ''}`, 60)

// Predictions
export const getPrediction = (gameId: string, forceRefresh = false) =>
  apiFetch<PredictionResponse>(`/predict/${gameId}${forceRefresh ? '?force_refresh=true' : ''}`, 0)

// Sync
export const syncByGameId = async (gameId: string) => {
  const res = await fetch(`${BASE}/sync/id/${encodeURIComponent(gameId)}`, { method: 'POST' })
  if (!res.ok) throw new Error('Sync failed')
  return res.json()
}

export const syncByAppid = async (appid: number) => {
  const res = await fetch(`${BASE}/sync/game/${appid}`, { method: 'POST' })
  if (!res.ok) throw new Error('Sync failed')
  return res.json()
}
