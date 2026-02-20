import { Suspense } from 'react'
import { notFound } from 'next/navigation'
import Link from 'next/link'
import Image from 'next/image'
import { ArrowLeft, ExternalLink, BarChart3, Clock } from 'lucide-react'
import Navbar from '@/components/Navbar'
import PredictionBadge from '@/components/PredictionBadge'
import PriceChart from '@/components/PriceChart'
import PriceHistoryTable from '@/components/PriceHistoryTable'
import SeasonalChart from '@/components/SeasonalChart'
import StoreDeals from '@/components/StoreDeals'
import PriceAlertBanner from '@/components/PriceAlertBanner'
import NextSalePredictor from '@/components/NextSalePredictor'
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
            <Link href="/" className="inline-flex items-center gap-2 px-5 py-2.5 glass rounded-xl text-steam-subtle text-sm font-mono hover:text-steam-text transition-colors">
              <ArrowLeft size={14} /> Back
            </Link>
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

  const currentPrice = prediction?.price_context.current_price ?? 0
  const minPrice     = stats.stats?.min_price ?? 0
  const avgPrice     = stats.stats?.avg_price ?? 0
  const discountPct  = prediction?.price_context.current_discount_pct ?? 0

  return (
    <div className="min-h-screen bg-steam-bg">
      <Navbar />

      {/* Hero */}
      <div className="relative h-64 overflow-hidden">
        {headerImg ? (
          <Image src={headerImg} alt={stats.title} fill className="object-cover scale-105" unoptimized priority />
        ) : (
          <div className="absolute inset-0 bg-gradient-to-br from-steam-muted to-steam-card" />
        )}
        <div className="absolute inset-0 bg-gradient-to-t from-steam-bg via-steam-bg/50 to-transparent" />
      </div>

      <div className="max-w-6xl mx-auto px-6 -mt-20 pb-24">
        <Link href="/" className="inline-flex items-center gap-2 text-steam-subtle text-sm hover:text-steam-text transition-colors mb-5 font-mono">
          <ArrowLeft size={14} /> Back
        </Link>

        {/* Title bar */}
        <div className="flex items-start justify-between gap-4 mb-5">
          <div className="animate-slide-up">
            <h1 className="font-display font-bold text-3xl sm:text-4xl text-steam-text leading-tight">
              {stats.title}
            </h1>
            {stats.appid && (
              <p className="text-steam-subtle text-sm font-mono mt-1">App #{stats.appid}</p>
            )}
          </div>
          <div className="flex items-center gap-2 flex-shrink-0 mt-1">
            {steamUrl && (
              <a href={steamUrl} target="_blank" rel="noopener noreferrer"
                className="flex items-center gap-1.5 px-3 py-2 glass rounded-lg text-steam-subtle hover:text-steam-cyan text-xs font-mono transition-colors">
                <ExternalLink size={12} /> Steam
              </a>
            )}
          </div>
        </div>

        {/* Alert banner */}
        {currentPrice > 0 && minPrice > 0 && (
          <div className="mb-6 animate-slide-up-delay-1">
            <PriceAlertBanner currentPrice={currentPrice} minPrice={minPrice}
              discountPct={discountPct} avgPrice={avgPrice} />
          </div>
        )}

        {/* 3-col layout */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

          {/* Left column */}
          <div className="space-y-5">
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

            {/* Stats grid */}
            {stats.stats && (
              <div className="space-y-3 animate-slide-up-delay-2">
                <p className="text-steam-subtle text-xs font-mono uppercase tracking-widest">Price Stats</p>
                <div className="grid grid-cols-2 gap-2">
                  <StatCard label="All-time low"  value={formatPrice(stats.stats.min_price)}
                    highlight={discountPct > 0 && currentPrice <= minPrice * 1.05} />
                  <StatCard label="All-time high" value={formatPrice(stats.stats.max_price)} />
                  <StatCard label="Avg price"     value={formatPrice(stats.stats.avg_price)} />
                  <StatCard label="Best discount" value={`${stats.stats.max_discount ?? 0}%`} />
                  <StatCard label="Sale avg"      value={`${(stats.stats.avg_discount_when_on_sale ?? 0).toFixed(1)}%`} />
                  <StatCard label="Records"       value={(stats.stats.total_records ?? 0).toLocaleString()} />
                </div>
                {stats.stats.first_seen && (
                  <p className="text-steam-subtle/60 text-xs font-mono px-1">
                    Tracking since {formatDate(stats.stats.first_seen)}
                  </p>
                )}
              </div>
            )}

            {/* Sale predictor */}
            {history && stats.seasonal_patterns && (
              <div className="animate-slide-up-delay-3">
                <NextSalePredictor
                  history={history.history}
                  seasonal={stats.seasonal_patterns}
                />
              </div>
            )}

            {/* Store deals */}
            <div className="animate-slide-up-delay-3">
              <p className="text-steam-subtle text-xs font-mono uppercase tracking-widest mb-3">Current Prices</p>
              <StoreDeals gameId={id} />
            </div>
          </div>

          {/* Right column (2/3) */}
          <div className="lg:col-span-2 space-y-5">

            {/* Price chart with range selector */}
            <div className="animate-slide-up-delay-2">
              {history?.history?.length
                ? <PriceChart history={history.history} stats={stats.stats} />
                : (
                  <div className="glass rounded-2xl p-8 text-center">
                    <p className="text-steam-subtle text-sm">No price history yet.</p>
                  </div>
                )
              }
            </div>

            {/* Seasonal chart */}
            {stats.seasonal_patterns?.length > 0 && (
              <div className="animate-slide-up-delay-3">
                <SeasonalChart patterns={stats.seasonal_patterns} />
              </div>
            )}

            {/* Price history table */}
            {history?.history?.length > 0 && (
              <div className="animate-slide-up-delay-3">
                <p className="text-steam-subtle text-xs font-mono uppercase tracking-widest mb-3">Full Price History</p>
                <PriceHistoryTable history={history.history} />
              </div>
            )}

          </div>
        </div>
      </div>
    </div>
  )
}
