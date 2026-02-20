// ── ITAD / Game ───────────────────────────────────────────────────────────────

export interface Game {
  id: string
  slug: string
  title: string
  appid?: number
  total_records?: number
  min_price?: number
  max_discount?: number
}

export interface SearchResult {
  id: string
  slug: string
  title: string
  type?: string
}

// ── Price History ──────────────────────────────────────────────────────────────

export interface PricePoint {
  timestamp: string
  price_usd: number
  regular_usd: number
  cut_pct: number
  shop_name: string
}

export interface PriceHistoryResponse {
  game_id: string
  title: string
  appid?: number
  count: number
  history: PricePoint[]
}

// ── Stats ─────────────────────────────────────────────────────────────────────

export interface PriceStats {
  total_records: number
  first_seen: string
  last_seen: string
  min_price: number
  max_price: number
  avg_price: number
  max_discount: number
  avg_discount_when_on_sale: number
  avg_cut_q4: number
  avg_cut_summer: number
  days_since_min_price: number
}

export interface SeasonalPattern {
  month: number
  avg_discount: number
  sample_count: number
}

export interface GameStatsResponse {
  game_id: string
  title: string
  appid?: number
  stats: PriceStats
  seasonal_patterns: SeasonalPattern[]
}

// ── Prediction ────────────────────────────────────────────────────────────────

export interface Prediction {
  score: number         // 0–100
  signal: 'BUY' | 'WAIT'
  reason: string
  confidence: number
}

export interface PriceContext {
  current_price: number
  min_price_ever: number
  avg_price: number
  current_discount_pct: number
}

export interface PredictionResponse {
  game_id: string
  title: string
  appid?: number
  prediction: Prediction
  price_context: PriceContext
  from_cache: boolean
}

// ── Health ────────────────────────────────────────────────────────────────────

export interface HealthResponse {
  status: string
  db: string
  model: string
  env: string
}
