import { Suspense } from 'react'
import { notFound } from 'next/navigation'
import Link from 'next/link'
import Image from 'next/image'
import { ArrowLeft, RefreshCw, ExternalLink, BarChart3, Clock, Zap } from 'lucide-react'
import Navbar from '@/components/Navbar'
import PredictionBadge from '@/components/PredictionBadge'
import PriceChart from '@/components/PriceChart'
import SeasonalChart from '@/components/SeasonalChart'
import StoreDeals from '@/components/StoreDeals'
import PriceAlertBanner from '@/components/PriceAlertBanner'
import { getGameStats, getPriceHistory, getPrediction } from '@/lib/api'
import { formatDate, formatPrice, steamImageUrl } from '@/lib/utils'

interface Props { params: { id: string } }

function StatCard({ label, value, highlight }: { label: string; value: string; highlight?: boolean }) {
  return (
    <div className={`glass rounded-xl p-4 text-center ${highlight ? 'border-steam-green/30 glow-green' : ''}`}>
      <div className={`font-mono font-bold text-base ${highlight ? 'text-steam-green' : 'text-steam-text'}`}>{value}</div>
      <div className="text-steam-subtle text-xs mt-0.5">{label}</div>
    </div>
  )
}

export default async function GamePage({ params }: Props) {
  const { id } = params

  const [statsResult, historyResult, predictionResult] = await Promise.allSettled([
    getGameStats(id),
    getPriceHistory(id),
    getPrediction(id),
  ])

  if (statsResult.status === 'rejected') {
    const msg = (statsResult.reason as Error)?.message || ''
    if (msg.includes('404') || msg.toLowerCase().includes('not found')) {
      return (
        <div className="min-h-screen bg-steam-bg flex items-center justify-center px-6">
          <div className="text-center space-y-6 max-w-md">
            <div className="w-20 h-20 mx-auto rounded-2xl bg-steam-card border border-steam-border flex items-center justify-center">
              <Clock size={36} className="text-steam-cyan animate-pulse" />
            </div>
            <div>
              <h1 className="font-display font-bold text-2xl text-steam-text">Loading price data...</h1>
              <p className="text-steam-subtle mt-2 text-sm">This game is being synced. Refresh in a moment.</p>
            </div>
            <div className="flex gap-3 justify-center">
              <Link href="/" className="inline-flex items-center gap-2 px-5 py-2.5 glass rounded-xl text-steam-subtle text-sm font-mono hover:text-steam-text transition-colors">
                <ArrowLeft size={14} /> Back
              </Link>
            </div>
          </div>
        </div>
      )
    }
    notFound()
  }

  const stats      = statsResult.value
  const history    = historyResult.status === 'fulfilled' ? historyResult.value : null
  const prediction = predictionResult.status === 'fulfilled' ? predictionResult.value : null
  const steamUrl   = stats.appid ? `https://store.steampowered.com/app/${stats.appid}` : null
  const headerImg  = steamImageUrl(stats.appid)

  const currentPrice  = prediction?.price_context.current_price ?? 0
  const minPrice      = stats.stats?.min_price ?? 0
  const avgPrice      = stats.stats?.avg_price ?? 0
  const discountPct   = prediction?.price_context.current_discount_pct ?? 0

  return (
    <div className="min-h-screen bg-steam-bg">
      <Navbar />

      {/* Hero banner */}
      <div className="relative h-56 overflow-hidden">
        {headerImg ? (
          <Image src={headerImg} alt={stats.title} fill className="object-cover" unoptimized priority />
        ) : (
          <div className="absolute inset-0 bg-gradient-to-br from-steam-muted to-steam-card" />
        )}
        <div className="absolute inset-0 bg-gradient-to-t from-steam-bg via-steam-bg/60 to-steam-bg/10" />
      </div>

      <div className="max-w-6xl mx-auto px-6 -mt-16 pb-20">

        {/* Back + title */}
        <Link href="/" className="inline-flex items-center gap-2 text-steam-subtle text-sm hover:text-steam-text transition-colors mb-5 font-mono">
          <ArrowLeft size={14} /> Back to search
        </Link>

        <div className="flex items-start justify-between gap-4 mb-6">
          <div className="animate-slide-up">
            <h1 className="font-display font-bold text-3xl sm:text-4xl text-steam-text leading-tight">
              {stats.title}
            </h1>
            {stats.appid && (
              <p className="text-steam-subtle text-sm font-mono mt-1">Steam App #{stats.appid}</p>
            )}
          </div>
          <div className="flex items-center gap-2 flex-shrink-0 animate-slide-up-delay-1">
            {steamUrl && (
              <a href={steamUrl} target="_blank" rel="noopener noreferrer"
                className="flex items-center gap-1.5 px-3 py-2 glass rounded-lg text-steam-subtle hover:text-steam-cyan text-xs font-mono transition-colors">
                <ExternalLink size={12} /> View on Steam
              </a>
            )}
          </div>
        </div>

        {/* Price alert banner */}
        {currentPrice > 0 && minPrice > 0 && (
          <div className="mb-6 animate-slide-up-delay-1">
            <PriceAlertBanner
              currentPrice={currentPrice} minPrice={minPrice}
              discountPct={discountPct} avgPrice={avgPrice}
            />
          </div>
        )}

        {/* Main grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

          {/* Left: prediction + stats */}
          <div className="lg:col-span-1 space-y-5">

            {/* Prediction */}
            <div className="animate-slide-up-delay-1">
              {prediction
                ? <PredictionBadge data={prediction} />
                : (
                  <div className="glass rounded-2xl p-6 text-center space-y-3">
                    <BarChart3 size={28} className="text-steam-subtle mx-auto" />
                    <p className="text-steam-subtle text-sm">
                      {predictionResult.status === 'rejected'
                        ? 'Need more price history for a prediction.'
                        : 'Generating prediction...'}
                    </p>
                  </div>
                )
              }
            </div>

            {/* Stat cards */}
            {stats.stats && (
              <div className="space-y-3 animate-slide-up-delay-2">
                <p className="text-steam-subtle text-xs font-mono uppercase tracking-widest">Price Stats</p>
                <div className="grid grid-cols-2 gap-2">
                  <StatCard label="All-time low"  value={formatPrice(stats.stats.min_price)}
                    highlight={discountPct > 0 && currentPrice <= minPrice * 1.05} />
                  <StatCard label="All-time high" value={formatPrice(stats.stats.max_price)} />
                  <StatCard label="Avg price"     value={formatPrice(stats.stats.avg_price)} />
                  <StatCard label="Best discount" value={`${stats.stats.max_discount ?? 0}%`} />
                  <StatCard label="Sale avg"      value={`${stats.stats.avg_discount_when_on_sale?.toFixed(1) ?? '—'}%`} />
                  <StatCard label="Records"       value={stats.stats.total_records?.toLocaleString() ?? '—'} />
                </div>
                {stats.stats.first_seen && (
                  <div className="glass rounded-xl px-4 py-3 text-xs text-steam-subtle font-mono">
                    Tracked since <span className="text-steam-text">{formatDate(stats.stats.first_seen)}</span>
                  </div>
                )}
              </div>
            )}

            {/* Store deals */}
            <div className="animate-slide-up-delay-3">
              <p className="text-steam-subtle text-xs font-mono uppercase tracking-widest mb-3">Current Prices</p>
              <StoreDeals gameId={id} />
            </div>
          </div>

          {/* Right: charts */}
          <div className="lg:col-span-2 space-y-5">
            <div className="animate-slide-up-delay-2">
              {history
                ? <PriceChart history={history.history} stats={stats.stats} />
                : (
                  <div className="glass rounded-2xl p-8 text-center">
                    <p className="text-steam-subtle text-sm">No price history available yet.</p>
                  </div>
                )
              }
            </div>

            {stats.seasonal_patterns?.length > 0 && (
              <div className="animate-slide-up-delay-3">
                <SeasonalChart patterns={stats.seasonal_patterns} />
              </div>
            )}

            {/* Footer hint */}
            <div className="glass rounded-xl px-5 py-4 flex items-center justify-between animate-slide-up-delay-3">
              <div>
                <p className="text-steam-text text-sm font-semibold">Keep data fresh</p>
                <p className="text-steam-subtle text-xs font-mono mt-0.5">
                  Updated {stats.stats?.last_seen ? formatDate(stats.stats.last_seen) : '—'}
                </p>
              </div>
              {stats.appid && (
                <code className="text-steam-subtle/50 text-xs font-mono">
                  POST /sync/game/{stats.appid}
                </code>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
