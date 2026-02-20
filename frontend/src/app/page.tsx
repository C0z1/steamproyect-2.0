import { Suspense } from 'react'
import { TrendingUp, Database, Brain, ChevronRight } from 'lucide-react'
import Link from 'next/link'
import Navbar from '@/components/Navbar'
import GameSearch from '@/components/GameSearch'
import { listGames } from '@/lib/api'
import { formatPrice } from '@/lib/utils'
import type { Game } from '@/lib/types'

async function RecentGames() {
  let games: Game[] = []
  try {
    games = await listGames(12)
  } catch {
    return (
      <div className="text-center py-12">
        <p className="text-steam-subtle text-sm font-mono">
          Backend not connected — start the FastAPI server and sync some games.
        </p>
        <code className="mt-3 block text-steam-cyan/70 text-xs">
          uvicorn main:app --reload --port 8000
        </code>
      </div>
    )
  }

  if (!games.length) return (
    <div className="text-center py-12">
      <p className="text-steam-subtle text-sm">No games synced yet.</p>
      <p className="text-steam-subtle/60 text-xs mt-1 font-mono">
        POST /sync/top?top_n=50
      </p>
    </div>
  )

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
      {games.map((game, i) => (
        <Link
          key={game.id}
          href={`/game/${game.id}`}
          className="glass rounded-xl p-4 hover:border-steam-cyan/30 hover:bg-steam-muted/50 transition-all group animate-slide-up"
          style={{ animationDelay: `${i * 40}ms`, animationFillMode: 'both' }}
        >
          <div className="flex items-start justify-between gap-2">
            <div className="flex-1 min-w-0">
              <h3 className="text-steam-text text-sm font-semibold truncate group-hover:text-steam-cyan transition-colors">
                {game.title}
              </h3>
              <div className="flex items-center gap-2 mt-1.5">
                {game.min_price !== undefined && (
                  <span className="text-steam-green text-xs font-mono">
                    Low {formatPrice(game.min_price)}
                  </span>
                )}
                {game.max_discount !== undefined && game.max_discount > 0 && (
                  <span className="text-steam-subtle text-xs font-mono">
                    · up to −{game.max_discount}%
                  </span>
                )}
              </div>
            </div>
            <ChevronRight size={14} className="text-steam-subtle group-hover:text-steam-cyan transition-colors flex-shrink-0 mt-0.5" />
          </div>
          {game.total_records !== undefined && (
            <div className="mt-2 pt-2 border-t border-steam-border/50">
              <span className="text-steam-subtle/60 text-xs font-mono">
                {game.total_records.toLocaleString()} price records
              </span>
            </div>
          )}
        </Link>
      ))}
    </div>
  )
}

export default function HomePage() {
  return (
    <div className="min-h-screen bg-steam-bg">
      <Navbar />

      {/* Hero */}
      <div className="relative pt-32 pb-16 px-6 overflow-hidden">
        {/* Background grid */}
        <div className="absolute inset-0 bg-grid-pattern opacity-30 pointer-events-none" />

        {/* Glow orb */}
        <div className="absolute top-20 left-1/2 -translate-x-1/2 w-[600px] h-[300px] rounded-full bg-steam-cyan/5 blur-[80px] pointer-events-none" />

        <div className="relative max-w-3xl mx-auto text-center space-y-8">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-steam-cyan/10 border border-steam-cyan/20 rounded-full text-steam-cyan text-xs font-mono">
            <Brain size={12} />
            ML-powered price intelligence
          </div>

          {/* Heading */}
          <div className="space-y-3">
            <h1 className="font-display font-bold text-5xl sm:text-6xl leading-none tracking-tight">
              <span className="text-steam-text">Buy or</span>
              <br />
              <span className="text-gradient-cyan">Wait?</span>
            </h1>
            <p className="text-steam-subtle text-lg max-w-lg mx-auto leading-relaxed">
              Machine learning predicts the optimal moment to buy any Steam game. Never pay full price again.
            </p>
          </div>

          {/* Search */}
          <div className="pt-2">
            <GameSearch />
          </div>

          {/* Stats row */}
          <div className="flex items-center justify-center gap-8 pt-4">
            {[
              { icon: Database, label: 'Price records', value: 'Live DB' },
              { icon: TrendingUp, label: 'Accuracy', value: '~82%' },
              { icon: Brain, label: 'Model', value: 'GBM' },
            ].map(({ icon: Icon, label, value }) => (
              <div key={label} className="text-center">
                <div className="flex items-center justify-center gap-1.5 text-steam-subtle text-xs font-mono mb-0.5">
                  <Icon size={11} />
                  {label}
                </div>
                <div className="text-steam-text text-sm font-display font-semibold">{value}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recent games */}
      <div className="max-w-6xl mx-auto px-6 pb-20">
        <div className="flex items-center justify-between mb-6">
          <h2 className="font-display font-semibold text-steam-text text-lg">
            Synced Games
          </h2>
          <span className="text-steam-subtle text-xs font-mono">click to analyze →</span>
        </div>

        <Suspense fallback={
          <div className="grid grid-cols-3 gap-3">
            {Array.from({length:6}).map((_,i) => (
              <div key={i} className="glass rounded-xl p-4 h-20 animate-pulse" />
            ))}
          </div>
        }>
          <RecentGames />
        </Suspense>
      </div>
    </div>
  )
}
