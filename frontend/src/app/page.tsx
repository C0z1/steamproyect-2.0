import { Suspense } from 'react'
import { TrendingUp, Database, Brain, Zap, Clock, ArrowRight } from 'lucide-react'
import Link from 'next/link'
import Navbar from '@/components/Navbar'
import GameSearch from '@/components/GameSearch'
import GameCard from '@/components/GameCard'
import { getTopDeals, getTopBuySignals, getOverviewStats } from '@/lib/api'

// ── Skeleton ──────────────────────────────────────────────────────────────────

function CardSkeleton() {
  return (
    <div className="glass rounded-2xl overflow-hidden animate-pulse">
      <div className="h-32 bg-steam-muted shimmer" />
      <div className="p-4 space-y-2">
        <div className="h-4 bg-steam-muted rounded w-3/4" />
        <div className="h-3 bg-steam-muted rounded w-1/2" />
        <div className="h-2 bg-steam-muted rounded" />
      </div>
    </div>
  )
}

function GridSkeleton() {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
      {Array.from({ length: 8 }).map((_, i) => <CardSkeleton key={i} />)}
    </div>
  )
}

// ── Data sections ─────────────────────────────────────────────────────────────

async function OverviewBar() {
  let stats = { total_games: 0, total_records: 0, buy_signals: 0, wait_signals: 0 }
  try { stats = await getOverviewStats() } catch {}
  return (
    <div className="flex flex-wrap items-center justify-center gap-6 sm:gap-10 py-6">
      {[
        { label: 'Games tracked', value: stats.total_games.toLocaleString(), icon: Database },
        { label: 'Price records', value: stats.total_records.toLocaleString(), icon: TrendingUp },
        { label: 'BUY signals', value: stats.buy_signals.toString(), icon: Zap, green: true },
        { label: 'WAIT signals', value: stats.wait_signals.toString(), icon: Clock },
      ].map(({ label, value, icon: Icon, green }) => (
        <div key={label} className="text-center">
          <div className="flex items-center justify-center gap-1.5 text-steam-subtle text-xs font-mono mb-0.5">
            <Icon size={11} className={green ? 'text-steam-green' : ''} />
            {label}
          </div>
          <div className={`font-display font-bold text-lg ${green ? 'text-steam-green' : 'text-steam-text'}`}>
            {value || '—'}
          </div>
        </div>
      ))}
    </div>
  )
}

async function TopDealsSection() {
  let deals: any[] = []
  try { deals = await getTopDeals(8) } catch {}

  if (!deals.length) return (
    <div className="text-center py-10 text-steam-subtle text-sm">
      No deals data yet — run a sync first.
      <code className="block mt-1 text-xs text-steam-cyan/60">POST /sync/top?top_n=50</code>
    </div>
  )

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
      {deals.map((d, i) => (
        <GameCard
          key={d.id}
          id={d.id} title={d.title} appid={d.appid}
          currentPrice={d.current_price} regularPrice={d.regular_price}
          discountPct={d.discount_pct} minPrice={d.min_price}
          lastSeen={d.last_seen} index={i}
        />
      ))}
    </div>
  )
}

async function BuySignalsSection() {
  let signals: any[] = []
  try { signals = await getTopBuySignals(8) } catch {}

  if (!signals.length) return (
    <div className="text-center py-10 text-steam-subtle text-sm">
      No predictions yet — predictions are generated when you view a game.
    </div>
  )

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
      {signals.map((s, i) => (
        <GameCard
          key={s.id}
          id={s.id} title={s.title} appid={s.appid}
          currentPrice={s.current_price} discountPct={s.discount_pct}
          score={s.score} signal={s.signal} reason={s.reason}
          index={i}
        />
      ))}
    </div>
  )
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function HomePage() {
  return (
    <div className="min-h-screen bg-steam-bg">
      <Navbar />

      {/* Hero */}
      <div className="relative pt-28 pb-12 px-6 overflow-hidden">
        <div className="absolute inset-0 bg-grid-pattern opacity-25 pointer-events-none" />
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[700px] h-[350px] rounded-full bg-steam-cyan/4 blur-[100px] pointer-events-none" />

        <div className="relative max-w-3xl mx-auto text-center space-y-7">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-steam-cyan/10 border border-steam-cyan/20 rounded-full text-steam-cyan text-xs font-mono">
            <Brain size={11} /> ML-powered · updated live
          </div>

          <div className="space-y-3">
            <h1 className="font-display font-bold text-5xl sm:text-6xl leading-none tracking-tight">
              <span className="text-steam-text">Buy or</span>
              <br />
              <span className="text-gradient-cyan">Wait?</span>
            </h1>
            <p className="text-steam-subtle text-lg max-w-lg mx-auto leading-relaxed">
              Machine learning analyzes years of Steam price history to tell you exactly when to buy.
            </p>
          </div>

          <GameSearch />
        </div>
      </div>

      {/* Overview stats bar */}
      <div className="max-w-4xl mx-auto px-6">
        <div className="glass rounded-2xl">
          <Suspense fallback={<div className="h-20 animate-pulse" />}>
            <OverviewBar />
          </Suspense>
        </div>
      </div>

      {/* Main content */}
      <div className="max-w-6xl mx-auto px-6 py-12 space-y-14">

        {/* Hot Deals */}
        <section>
          <div className="flex items-center justify-between mb-5">
            <div>
              <h2 className="font-display font-bold text-xl text-steam-text">🔥 Hot Deals</h2>
              <p className="text-steam-subtle text-sm mt-0.5">Games currently on sale, sorted by biggest discount</p>
            </div>
            <Link href="/explore?tab=deals" className="flex items-center gap-1 text-steam-subtle text-xs font-mono hover:text-steam-cyan transition-colors">
              See all <ArrowRight size={12} />
            </Link>
          </div>
          <Suspense fallback={<GridSkeleton />}>
            <TopDealsSection />
          </Suspense>
        </section>

        {/* ML Buy Signals */}
        <section>
          <div className="flex items-center justify-between mb-5">
            <div>
              <h2 className="font-display font-bold text-xl text-steam-text">
                <span className="text-steam-green">⚡</span> ML Buy Signals
              </h2>
              <p className="text-steam-subtle text-sm mt-0.5">Games our model says are worth buying right now</p>
            </div>
            <Link href="/explore?tab=buy" className="flex items-center gap-1 text-steam-subtle text-xs font-mono hover:text-steam-cyan transition-colors">
              See all <ArrowRight size={12} />
            </Link>
          </div>
          <Suspense fallback={<GridSkeleton />}>
            <BuySignalsSection />
          </Suspense>
        </section>

      </div>
    </div>
  )
}
