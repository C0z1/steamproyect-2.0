'use client'

import { useEffect, useState, useCallback } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import Image from 'next/image'
import Link from 'next/link'
import {
  Library, Heart, Sparkles, RefreshCw, Clock, TrendingDown,
  Zap, ChevronRight, Star, Database, AlertTriangle
} from 'lucide-react'
import Navbar from '@/components/Navbar'
import GameCard from '@/components/GameCard'
import { getToken, getUserFromStorage, type SteamUser } from '@/lib/auth'
import { getLibrary, getWishlist, getRecommendations, syncLibrary } from '@/lib/api'
import { formatPrice, formatDate, timeAgo, steamImageUrl } from '@/lib/utils'

// ── Tab types ─────────────────────────────────────────────────────────────────

type Tab = 'library' | 'wishlist' | 'recs'

// ── Library tab ───────────────────────────────────────────────────────────────

function LibraryTab({ token }: { token: string }) {
  const [data, setData]       = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [syncing, setSyncing] = useState(false)

  const load = useCallback(async () => {
    try {
      const d = await getLibrary(token)
      setData(d)
    } catch { } finally { setLoading(false) }
  }, [token])

  useEffect(() => { load() }, [load])

  const handleSync = async () => {
    setSyncing(true)
    try {
      await syncLibrary(token)
      await new Promise(r => setTimeout(r, 1500))
      const d = await getLibrary(token, true)
      setData(d)
    } catch { } finally { setSyncing(false) }
  }

  if (loading) return <LoadingSkeleton />

  const stats  = data?.stats  || {}
  const games  = data?.games  || []
  const tracked = games.filter((g: any) => g.game_id)

  return (
    <div className="space-y-6">
      {/* Library stats */}
      <div className="grid grid-cols-3 gap-4">
        {[
          { label: 'Total Games',   value: stats.total_games   || 0, icon: Library  },
          { label: 'Hours Played',  value: `${stats.total_hours || 0}h`, icon: Clock },
          { label: 'Tracked in DB', value: stats.tracked_games || 0, icon: Database  },
        ].map(({ label, value, icon: Icon }) => (
          <div key={label} className="glass rounded-xl p-4 text-center">
            <Icon size={18} className="text-steam-cyan mx-auto mb-2" />
            <p className="font-display font-bold text-xl text-steam-text">{value}</p>
            <p className="text-steam-subtle text-xs mt-0.5">{label}</p>
          </div>
        ))}
      </div>

      {/* Actions */}
      <div className="flex gap-3">
        <button onClick={handleSync} disabled={syncing}
          className="flex items-center gap-2 px-4 py-2 glass rounded-xl text-sm font-mono text-steam-subtle hover:text-steam-text transition-all disabled:opacity-50">
          <RefreshCw size={14} className={syncing ? 'animate-spin text-steam-cyan' : ''} />
          {syncing ? 'Syncing...' : 'Sync with Steam'}
        </button>
      </div>

      {/* Games grid */}
      {games.length === 0 ? (
        <EmptyState msg="No library data yet. Click Sync with Steam to import your games." icon={Library} />
      ) : (
        <div className="space-y-2">
          {games.map((g: any, i: number) => (
            <div key={g.appid}
              className="glass glass-hover rounded-xl flex items-center gap-4 px-4 py-3 group">
              {/* Image */}
              <div className="w-16 h-9 rounded-lg overflow-hidden bg-steam-muted flex-shrink-0">
                {steamImageUrl(g.appid) ? (
                  <img src={steamImageUrl(g.appid)!} alt={g.game_title}
                    className="w-full h-full object-cover" />
                ) : (
                  <div className="w-full h-full bg-steam-muted" />
                )}
              </div>

              {/* Title + playtime */}
              <div className="flex-1 min-w-0">
                <p className="text-steam-text text-sm font-semibold truncate">{g.game_title}</p>
                <p className="text-steam-subtle text-xs font-mono">
                  {g.playtime_mins > 0
                    ? `${Math.round(g.playtime_mins / 60)}h played`
                    : 'Never played'}
                  {g.last_played && ` · last ${timeAgo(g.last_played)}`}
                </p>
              </div>

              {/* Price info */}
              {g.game_id && (
                <div className="text-right flex-shrink-0">
                  <p className="text-steam-subtle text-xs font-mono">avg price</p>
                  <p className="text-steam-text text-sm font-mono font-semibold">
                    {formatPrice(g.avg_price)}
                  </p>
                </div>
              )}

              {/* Link */}
              {g.game_id && (
                <Link href={`/game/${g.game_id}`}
                  className="flex-shrink-0 text-steam-subtle hover:text-steam-cyan transition-colors opacity-0 group-hover:opacity-100">
                  <ChevronRight size={16} />
                </Link>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// ── Wishlist tab ──────────────────────────────────────────────────────────────

function WishlistTab({ token }: { token: string }) {
  const [data, setData]       = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [syncing, setSyncing] = useState(false)

  const load = useCallback(async () => {
    try {
      const d = await getWishlist(token)
      setData(d.wishlist || [])
    } catch { } finally { setLoading(false) }
  }, [token])

  useEffect(() => { load() }, [load])

  const handleSync = async () => {
    setSyncing(true)
    try {
      const d = await getWishlist(token, true)
      setData(d.wishlist || [])
    } catch { } finally { setSyncing(false) }
  }

  if (loading) return <LoadingSkeleton />

  const alerts = data.filter(g => g.discount_pct > 0 || g.signal === 'BUY')

  return (
    <div className="space-y-6">
      {alerts.length > 0 && (
        <div className="glass rounded-xl px-5 py-4 border border-steam-amber/20 bg-steam-amber/5">
          <div className="flex items-center gap-2 mb-3">
            <AlertTriangle size={14} className="text-steam-amber" />
            <p className="text-steam-amber text-sm font-semibold">{alerts.length} wishlist item{alerts.length > 1 ? 's' : ''} worth checking</p>
          </div>
          <div className="flex flex-wrap gap-2">
            {alerts.map(g => (
              <Link key={g.appid} href={g.game_id ? `/game/${g.game_id}` : '#'}
                className="text-xs font-mono bg-steam-muted px-3 py-1.5 rounded-lg text-steam-text hover:text-steam-cyan transition-colors">
                {g.game_title} {g.discount_pct > 0 && `−${g.discount_pct}%`}
              </Link>
            ))}
          </div>
        </div>
      )}

      <div className="flex gap-3">
        <button onClick={handleSync} disabled={syncing}
          className="flex items-center gap-2 px-4 py-2 glass rounded-xl text-sm font-mono text-steam-subtle hover:text-steam-text disabled:opacity-50 transition-all">
          <RefreshCw size={14} className={syncing ? 'animate-spin text-steam-cyan' : ''} />
          {syncing ? 'Syncing...' : 'Sync wishlist'}
        </button>
      </div>

      {data.length === 0 ? (
        <EmptyState msg="No wishlist data. Click Sync wishlist to import from Steam." icon={Heart} />
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {data.map((g: any) => {
            const isOnSale  = g.discount_pct > 0
            const isBuy     = g.signal === 'BUY'
            const isAtLow   = g.current_price > 0 && g.all_time_low > 0
                              && g.current_price <= g.all_time_low * 1.05
            return (
              <div key={g.appid} className={`glass glass-hover rounded-xl overflow-hidden group ${
                isBuy ? 'border-steam-green/20' : isOnSale ? 'border-steam-amber/20' : ''
              }`}>
                <div className="flex gap-3 p-4">
                  <div className="w-20 h-11 rounded-lg overflow-hidden bg-steam-muted flex-shrink-0">
                    {steamImageUrl(g.appid) && (
                      <img src={steamImageUrl(g.appid)!} alt={g.game_title} className="w-full h-full object-cover" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-steam-text text-sm font-semibold truncate">{g.game_title}</p>
                    <div className="flex items-center gap-2 mt-1 flex-wrap">
                      {g.current_price > 0 && (
                        <span className={`font-mono text-sm font-bold ${isOnSale ? 'text-steam-green' : 'text-steam-text'}`}>
                          {formatPrice(g.current_price)}
                        </span>
                      )}
                      {isOnSale && (
                        <span className="text-xs font-mono bg-steam-green/15 text-steam-green px-1.5 py-0.5 rounded">
                          −{g.discount_pct}%
                        </span>
                      )}
                      {isAtLow && (
                        <span className="text-xs font-mono bg-steam-cyan/10 text-steam-cyan px-1.5 py-0.5 rounded">
                          ATL
                        </span>
                      )}
                      {isBuy && (
                        <span className="text-xs font-mono bg-steam-green/10 text-steam-green px-1.5 py-0.5 rounded flex items-center gap-1">
                          <Zap size={9} /> BUY
                        </span>
                      )}
                    </div>
                    {g.all_time_low > 0 && (
                      <p className="text-steam-subtle text-xs font-mono mt-1">
                        ATL {formatPrice(g.all_time_low)}
                      </p>
                    )}
                  </div>
                  {g.game_id && (
                    <Link href={`/game/${g.game_id}`}
                      className="flex-shrink-0 text-steam-subtle hover:text-steam-cyan opacity-0 group-hover:opacity-100 transition-all self-center">
                      <ChevronRight size={16} />
                    </Link>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

// ── Recommendations tab ───────────────────────────────────────────────────────

function RecsTab({ token }: { token: string }) {
  const [recs, setRecs]       = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getRecommendations(token, 24)
      .then(d => setRecs(d.recommendations || []))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [token])

  if (loading) return <LoadingSkeleton />

  if (!recs.length) return (
    <EmptyState
      msg="No recommendations yet. Sync your library and browse some games so the model can generate BUY signals."
      icon={Sparkles}
    />
  )

  return (
    <div className="space-y-4">
      <p className="text-steam-subtle text-sm">
        Games you <span className="text-steam-text">don't own</span> that our ML model says are worth buying right now.
      </p>
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
        {recs.map((r: any, i: number) => (
          <GameCard key={r.id} id={r.id} title={r.title} appid={r.appid}
            currentPrice={r.current_price} discountPct={r.discount_pct}
            score={r.score} signal={r.signal} minPrice={r.min_price} index={i} />
        ))}
      </div>
    </div>
  )
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function LoadingSkeleton() {
  return (
    <div className="space-y-3">
      {[1,2,3,4].map(i => (
        <div key={i} className="glass rounded-xl h-16 animate-pulse shimmer" />
      ))}
    </div>
  )
}

function EmptyState({ msg, icon: Icon }: { msg: string; icon: any }) {
  return (
    <div className="text-center py-16 space-y-3">
      <Icon size={32} className="text-steam-subtle/40 mx-auto" />
      <p className="text-steam-subtle text-sm max-w-sm mx-auto">{msg}</p>
    </div>
  )
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function DashboardPage() {
  const searchParams = useSearchParams()
  const router       = useRouter()
  const [user, setUser]   = useState<SteamUser | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [tab, setTab]     = useState<Tab>('library')

  // Handle token from URL after Steam OAuth callback
  useEffect(() => {
    const urlToken = searchParams.get('token')
    if (urlToken) {
      localStorage.setItem('steamsense_token', urlToken)
      router.replace('/dashboard')
      return
    }
    const t = getToken()
    setToken(t)
    setUser(getUserFromStorage())
    const tabParam = searchParams.get('tab') as Tab
    if (tabParam) setTab(tabParam)
  }, [searchParams, router])

  if (!user || !token) {
    return (
      <div className="min-h-screen bg-steam-bg">
        <Navbar />
        <div className="flex items-center justify-center min-h-screen px-6">
          <div className="text-center space-y-6 max-w-sm">
            <div className="w-20 h-20 mx-auto rounded-2xl bg-steam-card border border-steam-border flex items-center justify-center">
              <Gamepad2 size={36} className="text-steam-cyan" />
            </div>
            <div>
              <h1 className="font-display font-bold text-2xl text-steam-text">Sign in to access your dashboard</h1>
              <p className="text-steam-subtle mt-2 text-sm">Connect your Steam account to see your library, wishlist, and personalized recommendations.</p>
            </div>
            <a href={`http://localhost:8000/auth/steam`}
              className="inline-flex items-center gap-3 px-6 py-3 bg-[#1b2838] border border-[#2a475e] rounded-xl text-white font-semibold hover:bg-[#2a475e] transition-colors">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                <path d="M11.979 0C5.678 0 .511 4.86.022 11.037l6.432 2.658c.545-.371 1.203-.59 1.912-.59.063 0 .125.004.188.006l2.861-4.142V8.91c0-2.495 2.028-4.524 4.524-4.524 2.494 0 4.524 2.031 4.524 4.527s-2.03 4.525-4.524 4.525h-.105l-4.076 2.911c0 .052.004.105.004.159 0 1.875-1.515 3.396-3.39 3.396-1.635 0-3.016-1.173-3.331-2.727L.436 15.27C1.862 20.307 6.486 24 11.979 24c6.627 0 11.999-5.373 11.999-12S18.605 0 11.979 0z"/>
              </svg>
              Sign in with Steam
            </a>
          </div>
        </div>
      </div>
    )
  }

  const tabs = [
    { key: 'library',  label: 'Library',         icon: Library  },
    { key: 'wishlist', label: 'Wishlist',         icon: Heart    },
    { key: 'recs',     label: 'Recommendations',  icon: Sparkles },
  ] as const

  return (
    <div className="min-h-screen bg-steam-bg">
      <Navbar />
      <div className="max-w-5xl mx-auto px-6 pt-24 pb-20">

        {/* Header */}
        <div className="flex items-center gap-4 mb-8 animate-slide-up">
          {user.avatar_url && (
            <Image src={user.avatar_url} alt={user.display_name} width={56} height={56}
              className="rounded-xl border-2 border-steam-cyan/20" unoptimized />
          )}
          <div>
            <p className="text-steam-subtle text-xs font-mono mb-1">Dashboard</p>
            <h1 className="font-display font-bold text-2xl text-steam-text">{user.display_name}</h1>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 mb-8">
          {tabs.map(({ key, label, icon: Icon }) => (
            <button key={key} onClick={() => setTab(key as Tab)}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-mono transition-all ${
                tab === key
                  ? 'bg-steam-cyan/10 border border-steam-cyan/30 text-steam-cyan'
                  : 'glass text-steam-subtle hover:text-steam-text'
              }`}>
              <Icon size={14} /> {label}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="animate-fade-in">
          {tab === 'library'  && <LibraryTab  token={token} />}
          {tab === 'wishlist' && <WishlistTab token={token} />}
          {tab === 'recs'     && <RecsTab     token={token} />}
        </div>
      </div>
    </div>
  )
}

function Gamepad2({ size, className }: { size: number; className?: string }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor"
      strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <line x1="6" y1="12" x2="10" y2="12" /><line x1="8" y1="10" x2="8" y2="14" />
      <line x1="15" y1="13" x2="15.01" y2="13" /><line x1="18" y1="11" x2="18.01" y2="11" />
      <rect x="2" y="6" width="20" height="12" rx="2" />
    </svg>
  )
}
