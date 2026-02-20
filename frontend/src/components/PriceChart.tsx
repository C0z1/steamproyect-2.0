'use client'

import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, ReferenceLine
} from 'recharts'
import type { PricePoint, PriceStats } from '@/lib/types'
import { formatDate, formatPrice } from '@/lib/utils'

interface Props {
  history: PricePoint[]
  stats?: PriceStats
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null
  const d = payload[0].payload as PricePoint
  return (
    <div className="glass rounded-xl px-4 py-3 text-sm space-y-1 min-w-[160px]">
      <p className="text-steam-subtle text-xs font-mono">{formatDate(label)}</p>
      <p className="text-steam-cyan font-mono font-semibold">{formatPrice(d.price_usd)}</p>
      {d.cut_pct > 0 && (
        <p className="text-steam-green text-xs font-mono">−{d.cut_pct}% off</p>
      )}
      <p className="text-steam-subtle text-xs">{d.shop_name}</p>
    </div>
  )
}

export default function PriceChart({ history, stats }: Props) {
  if (!history.length) return (
    <div className="glass rounded-2xl p-8 text-center text-steam-subtle">
      No price history available.
    </div>
  )

  // Sample down if too many points (keep max 200 for performance)
  const data = history.length > 200
    ? history.filter((_, i) => i % Math.ceil(history.length / 200) === 0)
    : history

  const minPrice = stats?.min_price ?? 0
  const maxPrice = stats?.max_price ?? Math.max(...data.map(d => d.price_usd))

  return (
    <div className="glass rounded-2xl p-6 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-steam-subtle text-xs font-mono uppercase tracking-widest mb-1">Price History</p>
          <div className="flex items-center gap-4 text-sm">
            <span className="text-steam-subtle">
              Low <span className="text-steam-green font-mono">{formatPrice(minPrice)}</span>
            </span>
            <span className="text-steam-subtle">
              High <span className="text-steam-text font-mono">{formatPrice(maxPrice)}</span>
            </span>
            <span className="text-steam-subtle">
              {data.length} data points
            </span>
          </div>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={240}>
        <AreaChart data={data} margin={{ top: 5, right: 5, bottom: 5, left: 10 }}>
          <defs>
            <linearGradient id="priceGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%"  stopColor="#00d4ff" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#00d4ff" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#1f2d45" />
          <XAxis
            dataKey="timestamp"
            tickFormatter={v => {
              const d = new Date(v)
              return `${d.toLocaleString('default', { month: 'short' })} '${String(d.getFullYear()).slice(2)}`
            }}
            tick={{ fill: '#5c7a9e', fontSize: 11, fontFamily: 'var(--font-mono)' }}
            tickLine={false}
            axisLine={{ stroke: '#1f2d45' }}
            interval="preserveStartEnd"
          />
          <YAxis
            tickFormatter={v => `$${v}`}
            tick={{ fill: '#5c7a9e', fontSize: 11, fontFamily: 'var(--font-mono)' }}
            tickLine={false}
            axisLine={false}
            width={45}
            domain={['auto', 'auto']}
          />
          <Tooltip content={<CustomTooltip />} />
          {minPrice > 0 && (
            <ReferenceLine
              y={minPrice}
              stroke="#00ff87"
              strokeDasharray="4 4"
              strokeOpacity={0.6}
              label={{ value: 'ATL', position: 'right', fill: '#00ff87', fontSize: 10, fontFamily: 'var(--font-mono)' }}
            />
          )}
          <Area
            type="monotone"
            dataKey="price_usd"
            stroke="#00d4ff"
            strokeWidth={2}
            fill="url(#priceGrad)"
            dot={false}
            activeDot={{ r: 4, fill: '#00d4ff', strokeWidth: 0 }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}
