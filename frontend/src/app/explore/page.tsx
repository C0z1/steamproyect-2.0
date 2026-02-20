import { Suspense } from 'react'
import { Compass, Zap, Clock, TrendingDown, Database } from 'lucide-react'
import Navbar from '@/components/Navbar'
import GameCard from '@/components/GameCard'
import { getTopDeals, getTopBuySignals, listGames } from '@/lib/api'

interface Props { searchParams: { tab?: string } }

async function DealsGrid() {
  let deals: any[] = []
  try { deals = await getTopDeals(40) } catch {}
  if (!deals.length) return <Empty msg="No deals found. Sync some games first." />
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
      {deals.map((d, i) => (
        <GameCard key={d.id} id={d.id} title={d.title} appid={d.appid}
          currentPrice={d.current_price} regularPrice={d.regular_price}
          discountPct={d.discount_pct} minPrice={d.min_price}
          lastSeen={d.last_seen} index={i} />
      ))}
    </div>
  )
}

async function BuyGrid() {
  let signals: any[] = []
  try { signals = await getTopBuySignals(40) } catch {}
  if (!signals.length) return <Empty msg="No BUY signals yet. View some game pages to generate predictions." />
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
      {signals.map((s, i) => (
        <GameCard key={s.id} id={s.id} title={s.title} appid={s.appid}
          currentPrice={s.current_price} discountPct={s.discount_pct}
          score={s.score} signal={s.signal} index={i} />
      ))}
    </div>
  )
}

async function AllGamesGrid() {
  let games: any[] = []
  try { games = await listGames(100) } catch {}
  if (!games.length) return <Empty msg="No games synced yet." />
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
      {games.map((g, i) => (
        <GameCard key={g.id} id={g.id} title={g.title} appid={g.appid}
          minPrice={g.min_price} discountPct={g.max_discount} index={i} />
      ))}
    </div>
  )
}

function Empty({ msg }: { msg: string }) {
  return (
    <div className="col-span-full py-20 text-center">
      <Database size={32} className="text-steam-subtle/40 mx-auto mb-3" />
      <p className="text-steam-subtle text-sm">{msg}</p>
    </div>
  )
}

function GridSkeleton() {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
      {Array.from({ length: 15 }).map((_, i) => (
        <div key={i} className="glass rounded-2xl overflow-hidden animate-pulse">
          <div className="h-32 bg-steam-muted" />
          <div className="p-4 space-y-2">
            <div className="h-4 bg-steam-muted rounded w-3/4" />
            <div className="h-3 bg-steam-muted rounded w-1/2" />
          </div>
        </div>
      ))}
    </div>
  )
}

export default function ExplorePage({ searchParams }: Props) {
  const tab = searchParams.tab ?? 'deals'

  const tabs = [
    { key: 'deals', label: 'Hot Deals',    icon: TrendingDown },
    { key: 'buy',   label: 'BUY Signals',  icon: Zap },
    { key: 'all',   label: 'All Games',    icon: Database },
  ]

  return (
    <div className="min-h-screen bg-steam-bg">
      <Navbar />

      <div className="max-w-7xl mx-auto px-6 pt-24 pb-20">

        {/* Header */}
        <div className="mb-8 animate-slide-up">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-8 h-8 rounded-lg bg-steam-cyan/10 border border-steam-cyan/20 flex items-center justify-center">
              <Compass size={16} className="text-steam-cyan" />
            </div>
            <h1 className="font-display font-bold text-2xl text-steam-text">Explore</h1>
          </div>
          <p className="text-steam-subtle text-sm">Browse all tracked games and find the best deals</p>
        </div>

        {/* Tabs */}
        <div className="flex items-center gap-2 mb-8">
          {tabs.map(({ key, label, icon: Icon }) => (
            <a
              key={key}
              href={`/explore?tab=${key}`}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-mono transition-all ${
                tab === key
                  ? 'bg-steam-cyan/10 border border-steam-cyan/30 text-steam-cyan'
                  : 'glass text-steam-subtle hover:text-steam-text'
              }`}
            >
              <Icon size={14} />
              {label}
            </a>
          ))}
        </div>

        {/* Grid */}
        <Suspense fallback={<GridSkeleton />}>
          {tab === 'deals' && <DealsGrid />}
          {tab === 'buy'   && <BuyGrid />}
          {tab === 'all'   && <AllGamesGrid />}
        </Suspense>
      </div>
    </div>
  )
}
